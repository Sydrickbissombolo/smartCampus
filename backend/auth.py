from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("You must log in first.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                flash("You must log in first.", "danger")
                return redirect(url_for("index"))
            # Only allowing access if the user's role matches
            if session["user"].get("role") != role:
                flash("Unauthorized access.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator