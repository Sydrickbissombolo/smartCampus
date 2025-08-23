from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from backend.database import init_db, get_db
from backend.auth import login_required, role_required
from backend.models import create_ticket, get_tickets, get_ticket_counts_by_week, create_user, get_users, send_ticket_confirmation, get_ticket_by_id
from backend.emailer import send_email
import os
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "frontend/static/attachments"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "docx"}

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.getenv("SECRET_KEY", "devkey")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

init_db()

# ---- Routes ----
@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
@login_required
@role_required("technician")
def add_comment(ticket_id):
    comment = request.form["comment"]
    conn = get_db()
    conn.execute("INSERT INTO comments (ticket_id, technician, comment) VALUES (?, ?, ?)",
                 (ticket_id, session["user"]["username"], comment))
    conn.commit()
    ticket = get_ticket_by_id(ticket_id)
    send_email(
        to=ticket["email"],
        subject="New Comment on Your Ticket",
        body=f"Dear {ticket['username']},\n\nA new comment has been added to your ticket '{ticket['title']}'. Please log in to view the details.\n\nThank you!"
    )
    conn.close()
    flash("Comment added and student notified.", "success")
    return redirect(url_for("technician_dashboard"))

@app.route("/ticket/<int:ticket_id>/status", methods=["POST"])
@login_required
@role_required("technician")
def change_status(ticket_id):
    status = request.form["status"]
    conn = get_db()
    conn.execute("UPDATE tickets SET status=? WHERE id=?", (status, ticket_id))
    conn.commit()
    ticket = get_ticket_by_id(ticket_id)
    send_email(
        to=ticket["email"],
        subject="Ticket Status Updated",
        body=f"Dear {ticket['username']},\n\nThe status of your ticket '{ticket['title']}' has been updated to '{status}'. Please log in to view the details.\n\nThank you!"
    )
    conn.close()
    flash("Status updated.", "success")
    return redirect(url_for("technician_dashboard"))

@app.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("technician")
def edit_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if request.method == "POST":
        new_role = request.form["role"]
        conn.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
        conn.commit()
        conn.close()
        flash("User updated successfully.", "success")
        return redirect(url_for("users"))
    conn.close()
    return render_template("edit_user.html", user=user)

@app.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
@role_required("technician")
def delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully.", "success")
    return redirect(url_for("users"))

@app.route("/users/reset_password/<int:user_id>", methods=["POST"])
@login_required
@role_required("technician")
def reset_user_password(user_id):
    new_pw = request.form["new_password"]
    hashed_pw = generate_password_hash(new_pw)
    conn = get_db()
    conn.execute("UPDATE users SET password=? WHERE id=?", (hashed_pw, user_id))
    conn.commit()
    conn.close()
    flash("Password reset successfully.", "success")
    return redirect(url_for("users"))

@app.route("/login", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user"] = {"username": user["username"], "role": user["role"]}
            if user["role"] == "student":
                return redirect(url_for("student_dashboard"))
            return redirect(url_for("technician_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("index.html")

@app.route("/student")
@login_required
@role_required("student")
def student_dashboard():
    tickets = get_tickets(session["user"]["username"])
    return render_template("student.html", tickets=tickets, user=session["user"])

# @app.route("/api/tickets", methods=["GET"])
# def api_get_tickets():
#     tickets = get_tickets()
#     return jsonify(tickets)


@app.route("/users")
@login_required
@role_required("technician")
def users():
    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page
    conn = get_db()
    users = conn.execute("SELECT id, username, role FROM users ORDER BY id LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    user_list = [dict(u) for u in users]
    return render_template("users.html", users=user_list, user=session["user"], page=page, total=total, per_page=per_page)

@app.route("/users/search")
@login_required
@role_required("technician")
def search_users():
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page
    conn = get_db()
    users = conn.execute(
        "SELECT id, username, role FROM users WHERE username LIKE ? ORDER BY id LIMIT ? OFFSET ?",
        (f"%{query}%", per_page, offset)
    ).fetchall()
    total = conn.execute(
        "SELECT COUNT(*) FROM users WHERE username LIKE ?",
        (f"%{query}%",)
    ).fetchone()[0]
    conn.close()
    user_list = [dict(u) for u in users]
    return render_template(
        "users.html",
        users=user_list,
        user=session["user"],
        query=query,
        page=page,
        total=total,
        per_page=per_page
    )

@app.route("/technician")
@login_required
@role_required("technician")
def technician_dashboard():
    tickets = get_tickets()
    return render_template("technician.html", tickets=tickets, user=session["user"])

@app.route("/ticket/new", methods=["POST"])
@login_required
@role_required("student")
def new_ticket():
    title = request.form["title"]
    category = request.form["category"]
    description = request.form["description"]
    email = request.form["email"]
    phone = request.form["phone"]
    attachment = request.files.get("attachment")
    if attachment and allowed_file(attachment.filename):
        filename = secure_filename(attachment.filename)
        attachment.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    create_ticket(session["user"]["username"], title, category, description, email, phone, filename if attachment else None)
    send_ticket_confirmation(email, title)
    flash("Ticket created successfully!", "success")
    return redirect(url_for("student_dashboard"))

@app.route("/reporting")
@login_required
@role_required("technician")
def reporting():
    data = get_ticket_counts_by_week()
    return render_template("reporting.html", data=data)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = "student"
        try:
            create_user(username, password, role)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash("Registration failed: " + str(e), "danger")
    return render_template("register.html")

@app.route("/register_technician", methods=["GET", "POST"])
def register_technician():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = "technician"
        try:
            create_user(username, password, role)
            flash("Technician registered! Please log in.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash("Registration failed: " + str(e), "danger")
    return render_template("register.html")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_pw = request.form["old_password"]
        new_pw = request.form["new_password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (session["user"]["username"],)).fetchone()
        if user and check_password_hash(user["password"], old_pw):
            hashed_pw = generate_password_hash(new_pw)
            conn.execute("UPDATE users SET password=? WHERE username=?", (hashed_pw, user["username"]))
            conn.commit()
            flash("Password changed!", "success")
        else:
            flash("Old password incorrect.", "danger")
        conn.close()
    return render_template("change_password.html", user=session["user"])

@app.route("/ticket/<int:ticket_id>/close", methods=["POST"])
@login_required
@role_required("technician")
def close_ticket(ticket_id):
    conn = get_db()
    conn.execute("UPDATE tickets SET status='closed' WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()
    flash("Ticket closed.", "success")
    return redirect(url_for("technician_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("welcome"))

if __name__ == "__main__":
    app.run(debug=True)
