from backend.database import get_db
from werkzeug.security import generate_password_hash

def create_user(username, password, role):
    conn = get_db()
    hashed_pw = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, hashed_pw, role)
    )
    conn.commit()
    conn.close()
    
def create_ticket(username, title, category, description):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tickets (username, title, category, description) VALUES (?, ?, ?, ?)",
        (username, title, category, description),
    )
    conn.commit()
    conn.close()

def get_tickets(username=None):
    conn = get_db()
    cur = conn.cursor()
    if username:
        cur.execute("SELECT * FROM tickets WHERE username=? ORDER BY created_at DESC", (username,))
    else:
        cur.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_ticket_counts_by_week():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT strftime('%W', created_at) as week, COUNT(*) as count
    FROM tickets
    GROUP BY week
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"week": row["week"], "count": row["count"]} for row in rows]
