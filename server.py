from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from functools import wraps
import os, json, io, zipfile
from datetime import datetime

app = Flask(__name__)
app.secret_key = "kishore55@"  # Change this to a strong secret key

# --- Admin Credentials ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "kishore55"  # Change this to your desired password

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- Config ---
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DATA_FILE = os.path.join(UPLOAD_FOLDER, "submissions.json")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# --- Helpers to Load/Save Data ---
def load_submissions():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_submissions(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

submissions = load_submissions()

# --- Login ---
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

# --- Logout ---
@app.route("/logout")
@login_required
def logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# --- Index ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Admin Dashboard ---
@app.route("/admin")
@login_required
def admin_dashboard():
    current = load_submissions()
    return render_template("admin.html", submissions=current)

# --- File Upload ---
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    filename = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(file.filename)
    dest = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(dest)

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month": "",
        "year": "",
        "file": filename,
        "pasted_data": ""
    }
    submissions.append(record)
    save_submissions(submissions)

    return jsonify({"success": True, "filename": filename})

# --- Submit Data ---
@app.route("/submit", methods=["POST"])
@app.route("/send-data", methods=["POST"])
def submit():
    month = request.form.get("month", "") or ""
    year = request.form.get("year", "") or ""
    pasted = request.form.get("pasted_data")
    if pasted is None:
        pasted = request.form.get("pastedData", "") or ""

    file = request.files.get("file")
    filename = None
    if file and file.filename != "":
        filename = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month": month,
        "year": year,
        "file": filename,
        "pasted_data": pasted
    }
    submissions.append(record)
    save_submissions(submissions)

    return jsonify({"success": True, "message": "Saved"})

# --- Serve Uploaded Files ---
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

# --- Delete Submission ---
@app.route("/delete", methods=["POST"])
@login_required
def delete_submission():
    data = request.get_json()
    ts = data.get("timestamp")
    global submissions

    # Find and remove the matching record
    for s in submissions[:]:
        if s["timestamp"] == ts:
            if s.get("file"):
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], s["file"])
                if os.path.exists(filepath):
                    os.remove(filepath)
            submissions.remove(s)

    save_submissions(submissions)
    return jsonify({"success": True})

# --- Download All Submissions for a Month ---
@app.route("/download_month/<month>")
@login_required
def download_month(month):
    month_submissions = []
    for s in submissions:
        submission_month = s['month'] if s['month'] else datetime.strptime(
            s['timestamp'], "%Y-%m-%d %H:%M:%S"
        ).strftime("%B")
        if submission_month == month:
            month_submissions.append(s)

    if not month_submissions:
        return "No submissions in this month", 404

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for s in month_submissions:
            if s.get("file"):
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], s["file"])
                if os.path.exists(filepath):
                    zf.write(filepath, arcname=s["file"])
    memory_file.seek(0)
    return send_file(memory_file, download_name=f"{month}_submissions.zip", as_attachment=True)

# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
