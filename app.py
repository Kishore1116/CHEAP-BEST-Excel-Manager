from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = "kishore55"  # Change this to a strong secret key

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin77"  # Change this to your desired password

# Decorator to protect admin pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password", "error")
    return render_template("login.html")

# Logout route
@app.route("/logout")
@login_required
def logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# Admin dashboard route
@app.route("/admin")
@login_required
def admin_dashboard():
    # Your current admin logic
    return render_template("admin.html", submissions=submissions)

# Example home route
@app.route("/")
def index():
    return "Home page"
