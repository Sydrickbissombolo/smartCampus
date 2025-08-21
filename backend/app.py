from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from backend.database import init_db, get_db
from backend.auth import login_required, role_required
from backend.models import create_ticket, get_tickets, get_ticket_counts_by_week, create_user
import os
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = os.getenv("SECRET_KEY", "devkey")

init_db()

# ---- Routes ----
@app.route("/", methods=["GET", "POST"])
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
    create_ticket(session["user"]["username"], title, category, description)
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
        role = request.form["role"]
        try:
            create_user(username, password, role)
            flash("Registration successful! Please log in.", "success")
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
    return render_template("change_password.html")

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
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
