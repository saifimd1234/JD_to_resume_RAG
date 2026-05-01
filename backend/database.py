import sqlite3
import os
import bcrypt
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from backend.config import ADMIN_EMAIL

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "database.db"

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            last_job_role TEXT,
            resumes_generated INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Check if last_job_role exists (migration for existing DBs)
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'last_job_role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_job_role TEXT")
            
        # Migration for profile columns
        profile_cols = {
            'full_name': 'TEXT',
            'phone': 'TEXT',
            'location': 'TEXT',
            'linkedin': 'TEXT',
            'github': 'TEXT'
        }
        for col, col_type in profile_cols.items():
            if col not in columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            
        # Create knowledge base entries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kb_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            github_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Create generated resumes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_role TEXT NOT NULL,
            job_description TEXT NOT NULL,
            resume_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Create password resets table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Auto-upgrade the configured admin email
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (ADMIN_EMAIL,))
        
        # Create user documents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Create user cloud links table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cloud_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            folder_link TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        conn.commit()

# Ensure DB is initialized when module loads
init_db()


# ─── Auth Functions ─────────────────────────────────────────────────────────

def create_user(email: str, password: str, role: str = "user"):
    """Create a new user. Returns True if successful, False if email exists."""
    if email == ADMIN_EMAIL:
        role = "admin"
        
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", 
                           (email, password_hash, role))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(email: str, password: str):
    """Authenticate a user. Returns a dict with user info or None."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, role, resumes_generated, last_job_role, full_name, phone, location, linkedin, github FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "resumes_generated": user["resumes_generated"],
                "last_job_role": user["last_job_role"],
                "full_name": user["full_name"],
                "phone": user["phone"],
                "location": user["location"],
                "linkedin": user["linkedin"],
                "github": user["github"]
            }
        return None

def check_resume_limit(user_id: int):
    """Check if the user has reached their limit. Admins are unlimited. Users get 1 free."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT resumes_generated, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return False, "User not found."
            
        if user["role"] == "admin":
            return True, ""
            
        if user["resumes_generated"] >= 1: # Limit to 1 for free users
            return False, "You've reached your free limit. Upgrade for more."
            
        return True, ""

def increment_resume_count(user_id: int):
    """Increment the resumes_generated counter for a user."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET resumes_generated = resumes_generated + 1 WHERE id = ?", (user_id,))
        conn.commit()

def update_user_profile(user_id: int, profile_data: dict):
    """Update user profile details."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, phone = ?, location = ?, linkedin = ?, github = ?
            WHERE id = ?
        """, (
            profile_data.get("full_name"),
            profile_data.get("phone"),
            profile_data.get("location"),
            profile_data.get("linkedin"),
            profile_data.get("github"),
            user_id
        ))
        conn.commit()


# ─── Resume Tracking Functions ─────────────────────────────────────────────

def save_generated_resume(user_id: int, job_role: str, jd_text: str, resume_content: str):
    """Save a generated resume to the database and update user's last job role."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Save resume
        cursor.execute("""
            INSERT INTO generated_resumes (user_id, job_role, job_description, resume_content)
            VALUES (?, ?, ?, ?)
        """, (user_id, job_role, jd_text, resume_content))
        
        # Update user's last job role
        cursor.execute("UPDATE users SET last_job_role = ? WHERE id = ?", (job_role, user_id))
        conn.commit()

def get_user_resumes(user_id: int):
    """Retrieve all generated resumes for a specific user."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, job_role, job_description, resume_content, created_at 
            FROM generated_resumes 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

# ─── Password Reset Functions ───────────────────────────────────────────────

def create_reset_token(email: str):
    """Create a password reset token for an email."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            return None
            
        user_id = user[0]
        token = str(uuid.uuid4())
        # Token expires in 1 hour
        expires_at = datetime.now() + timedelta(hours=1)
        
        cursor.execute("INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)", 
                       (user_id, token, expires_at.isoformat()))
        conn.commit()
        return token

def verify_reset_token(token: str):
    """Verify a reset token and return user_id if valid."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, expires_at FROM password_resets WHERE token = ?", (token,))
        result = cursor.fetchone()
        
        if not result:
            return None
            
        user_id, expires_at_str = result
        expires_at = datetime.fromisoformat(expires_at_str)
        
        if datetime.now() > expires_at:
            return None
            
        return user_id

def reset_password(user_id: int, new_password: str):
    """Reset the user's password and clear their tokens."""
    password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        cursor.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
        conn.commit()
        return True

# ─── Admin Dashboard Functions ───────────────────────────────────────────────

def get_total_users():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

def get_total_resumes_generated():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(resumes_generated) FROM users")
        result = cursor.fetchone()[0]
        return result if result else 0

def get_all_users():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, role, resumes_generated, created_at FROM users ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

# ─── Knowledge Base Functions ───────────────────────────────────────────────

def add_kb_entry(user_id: int, category: str, title: str, content: str, github_url: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO kb_entries (user_id, category, title, content, github_url, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, category, title, content, github_url, datetime.now()))
        conn.commit()

def get_kb_entries(user_id: int, category: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if category:
            cursor.execute("SELECT * FROM kb_entries WHERE user_id = ? AND category = ? ORDER BY updated_at DESC", (user_id, category))
        else:
            cursor.execute("SELECT * FROM kb_entries WHERE user_id = ? ORDER BY category, updated_at DESC", (user_id,))
            
        return [dict(row) for row in cursor.fetchall()]

def delete_kb_entry(entry_id: int, user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kb_entries WHERE id = ? AND user_id = ?", (entry_id, user_id))
        conn.commit()

def update_kb_entry(entry_id: int, user_id: int, category: str, title: str, content: str, github_url: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE kb_entries 
            SET category = ?, title = ?, content = ?, github_url = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (category, title, content, github_url, datetime.now(), entry_id, user_id))
        conn.commit()

def get_kb_as_markdown(user_id: int):
    """
    Export the user's KB entries into a raw text string for ingestion or review.
    Instead of physical files, we can just feed this directly to the document loader.
    """
    entries = get_kb_entries(user_id)
    doc_text = ""
    for entry in entries:
        doc_text += f"\n\n# {entry['category'].upper()}: {entry['title']}\n"
        if entry['github_url']:
            doc_text += f"**Project Link**: {entry['github_url']}\n"
        doc_text += f"\n{entry['content']}\n"
        doc_text += "-" * 40
        
    return doc_text

def sync_admin_kb_to_disk(user_id: int):
    """Mirror the admin's database KB entries back to the root knowledge_base/ directory."""
    from backend.config import KNOWLEDGE_BASE_DIR
    import re
    
    entries = get_kb_entries(user_id)
    
    # Ensure the directory exists
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
    
    for entry in entries:
        category_dir = KNOWLEDGE_BASE_DIR / entry['category']
        os.makedirs(category_dir, exist_ok=True)
        
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', entry['title'])
        filename = f"{safe_title}.md"
        filepath = category_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {entry['title']}\n\n")
            if entry['github_url']:
                f.write(f"**GitHub:** {entry['github_url']}\n\n")
            f.write(f"{entry['content']}\n")

def sync_disk_to_admin_kb(user_id: int):
    """Load KB entries from the root knowledge_base folder into the database for the admin."""
    from backend.config import KNOWLEDGE_BASE_DIR
    
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        return
        
    # Check if admin already has entries. If so, return to avoid duplicates.
    entries = get_kb_entries(user_id)
    if len(entries) > 0:
        return
        
    for category_dir in os.listdir(KNOWLEDGE_BASE_DIR):
        cat_path = KNOWLEDGE_BASE_DIR / category_dir
        if not os.path.isdir(cat_path):
            continue
            
        for filename in os.listdir(cat_path):
            if not filename.endswith(".md"):
                continue
                
            filepath = cat_path / filename
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Parse title from filename
            title = filename.replace(".md", "").replace("_", " ").title()
            
            # Simple content parsing: strip the # title from the first line if it exists
            lines = content.split('\n')
            if lines and lines[0].startswith('# '):
                # Optionally use this as title
                title = lines[0][2:].strip()
                content = '\n'.join(lines[1:]).strip()
                
            add_kb_entry(user_id, category_dir, title, content)

# ─── User Documents Functions ───────────────────────────────────────────────

def add_user_document(user_id: int, title: str, file_path: str, file_type: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_documents (user_id, title, file_path, file_type) 
            VALUES (?, ?, ?, ?)
        """, (user_id, title, file_path, file_type))
        conn.commit()

def get_user_documents(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_documents WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_user_document(doc_id: int, user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM user_documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
        doc = cursor.fetchone()
        if doc:
            try:
                if os.path.exists(doc['file_path']):
                    os.remove(doc['file_path'])
            except Exception:
                pass
            cursor.execute("DELETE FROM user_documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
            conn.commit()

# ─── Cloud Storage Functions ───────────────────────────────────────────────

def add_cloud_link(user_id: int, name: str, provider: str, folder_link: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_cloud_links (user_id, name, provider, folder_link) 
            VALUES (?, ?, ?, ?)
        """, (user_id, name, provider, folder_link))
        conn.commit()

def get_cloud_links(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_cloud_links WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_cloud_link(link_id: int, user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_cloud_links WHERE id = ? AND user_id = ?", (link_id, user_id))
        conn.commit()



