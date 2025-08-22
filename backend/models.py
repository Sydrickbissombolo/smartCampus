from backend.database import get_db
from werkzeug.security import generate_password_hash
import smtplib
from email.mime.text import MIMEText

def create_user(username, password, role):
    conn = get_db()
    hashed_pw = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, hashed_pw, role)
    )
    conn.commit()
    conn.close()
    
def create_ticket(username, title, category, description, email, phone, attachment=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO tickets (username, title, category, description, email, phone, attachment) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, title, category, description, email, phone, attachment)
    )
    conn.commit()
    conn.close()

def get_ticket_by_id(ticket_id):
    conn = get_db()
    ticket = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return dict(ticket) if ticket else None

def send_ticket_confirmation(to_email, ticket_title):
    from_email = "smartnoreplycampus@gmail.com"
    subject = "Smart Campus Services Support"
    body = f"Dear Student,\n\nThis is confirm that your case '{ticket_title}' has been received. Our technician will contact you soon.\n\nIf you have any other questions, please go ahead to our portal and create a new ticket.\n\nBest regards,\n\nSmart Campus Services Team"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    # Update with your SMTP server details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "smartnoreplycampus@gmail.com"
    smtp_password = "xqkn uizr hnfu leec"

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
    except Exception as e:
        print("Email sending failed:", e)

def send_email(to, subject, body):
    from_email = "smartnoreplycampus@gmail.com"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "smartnoreplycampus@gmail.com"
    smtp_password = "xqkn uizr hnfu leec"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to], msg.as_string())
        server.quit()
    except Exception as e:
        print("Email sending failed:", e)

def get_tickets(username=None):
    conn = get_db()
    if username:
        tickets = conn.execute("SELECT * FROM tickets WHERE username = ?", (username,)).fetchall()
    else:
        tickets = conn.execute("SELECT * FROM tickets").fetchall()
    # Attach comments to each ticket
    ticket_list = []
    for ticket in tickets:
        comments = conn.execute("SELECT * FROM comments WHERE ticket_id = ? ORDER BY created_at ASC", (ticket["id"],)).fetchall()
        ticket_dict = dict(ticket)
        ticket_dict["comments"] = [dict(c) for c in comments]
        ticket_list.append(ticket_dict)
    conn.close()
    return ticket_list


def get_users():
    conn = get_db()
    users = conn.execute("SELECT id, username, role FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(u) for u in users]

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
