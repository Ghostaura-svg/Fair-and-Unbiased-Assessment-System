from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    return render_template("home.html")


def process_login(role, dashboard_route, login_template):
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT user_id, first_name, last_name, email, role, account_status
                FROM users
                WHERE email = %s
                  AND password_hash = %s
                  AND role = %s
                  AND account_status = 'Active'
            """

            cursor.execute(query, (email, password, role))
            user = cursor.fetchone()

            if user:
                session["user_id"] = user["user_id"]
                session["first_name"] = user["first_name"]
                session["last_name"] = user["last_name"]
                session["email"] = user["email"]
                session["role"] = user["role"]

                return redirect(url_for(dashboard_route))

            flash("Invalid email or password for this login type.", "danger")

        except Exception as error:
            flash(f"Database error: {error}", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template(login_template)


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    return process_login("Admin", "admin.admin_dashboard", "admin_login.html")


@auth_bp.route("/faculty/login", methods=["GET", "POST"])
def faculty_login():
    return process_login("Faculty", "faculty.faculty_dashboard", "faculty_login.html")


@auth_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    return process_login("Student", "student.student_dashboard", "student_login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.home"))