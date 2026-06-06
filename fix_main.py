import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. init_db
init_db_patch = """
        try:
            cursor.execute("ALTER TABLE summaries ADD COLUMN created_at TEXT;")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE summaries ADD COLUMN provider TEXT;")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE summaries ADD COLUMN type TEXT;")
        except:
            pass
"""
if 'ALTER TABLE summaries ADD COLUMN created_at' not in content:
    content = content.replace('conn.commit()\n        try:\n            cursor.execute("ALTER TABLE users', 'conn.commit()\n' + init_db_patch + '\n        try:\n            cursor.execute("ALTER TABLE users')

# 2. upload_audio
upload_target = """cursor.execute(
            "INSERT INTO summaries (username, filename, transcript, summary) VALUES (?, ?, ?, ?)",
            (username, file.filename, transcript, final_summary)
        )"""

upload_patch = """import datetime
        now = datetime.datetime.now().strftime("%b %d, %Y")
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in ['.mp3', '.wav', '.m4a', '.flac']:
            file_type = "Audio"
        elif ext in ['.mp4', '.avi', '.mov']:
            file_type = "Video"
        else:
            file_type = "Document"
            
        cursor.execute(
            "INSERT INTO summaries (username, filename, transcript, summary, created_at, provider, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, file.filename, transcript, final_summary, now, provider, file_type)
        )"""
content = content.replace(upload_target, upload_patch)

# 3. get_summaries
get_summaries_target = """cursor.execute(
            "SELECT id, filename FROM summaries WHERE username = ? ORDER BY id DESC",
            (username,),
        )
        rows = cursor.fetchall()
        return [{"id": row["id"], "filename": row["filename"]} for row in rows]"""

get_summaries_patch = """cursor.execute(
            "SELECT id, filename, created_at, provider, type FROM summaries WHERE username = ? ORDER BY id DESC",
            (username,),
        )
        rows = cursor.fetchall()
        return [{
            "id": row["id"], 
            "filename": row["filename"],
            "date": row["created_at"] or "Recent",
            "provider": row["provider"] or "Unknown",
            "type": row["type"] or "Audio"
        } for row in rows]"""
content = content.replace(get_summaries_target, get_summaries_patch)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("main.py updated")
