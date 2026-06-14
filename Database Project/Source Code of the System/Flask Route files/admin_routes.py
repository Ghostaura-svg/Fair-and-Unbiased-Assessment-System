from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from db import get_db_connection

admin_bp = Blueprint("admin", __name__)


def admin_required():
    return "user_id" in session and session.get("role") == "Admin"


def close_connection(cursor, connection):
    cursor.close()
    connection.close()


def clean_db_error(error):
    message = str(error)

    if "1644" in message:
        parts = message.split(":")
        return parts[-1].strip()

    return message


def get_first_phone(cursor, user_id):
    cursor.execute("""
        SELECT phone_no
        FROM user_phone
        WHERE user_id = %s
        LIMIT 1
    """, (user_id,))
    phone = cursor.fetchone()
    return phone["phone_no"] if phone else ""


@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM v_admin_dashboard_counts")
    counts = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM v_recent_enrollments
        ORDER BY enrollment_id DESC
        LIMIT 5
    """)
    recent_enrollments = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM v_recent_teacher_assignments
        ORDER BY teacher_assignment_id DESC
        LIMIT 5
    """)
    recent_assignments = cursor.fetchall()

    close_connection(cursor, connection)

    return render_template(
        "admindashboard.html",
        total_students=counts["total_students"],
        total_faculty=counts["total_faculty"],
        total_courses=counts["total_courses"],
        total_enrollments=counts["total_enrollments"],
        total_teacher_assignments=counts["total_teacher_assignments"],
        active_users=counts["active_users"],
        inactive_users=counts["inactive_users"],
        total_departments=counts["total_departments"],
        recent_enrollments=recent_enrollments,
        recent_assignments=recent_assignments
    )


# ============================================================
# STUDENTS
# ============================================================

@admin_bp.route("/admin/students")
def students():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    search = request.args.get("search", "").strip()
    search_value = f"%{search}%"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            student_id,
            registration_no,
            student_status,
            user_id,
            first_name,
            last_name,
            email,
            account_status,
            department_name,
            program_name,
            batch_name
        FROM v_admin_students
        WHERE
            registration_no LIKE %s
            OR first_name LIKE %s
            OR last_name LIKE %s
            OR CONCAT(first_name, ' ', last_name) LIKE %s
            OR department_name LIKE %s
            OR program_name LIKE %s
        ORDER BY student_id ASC
    """, (
        search_value,
        search_value,
        search_value,
        search_value,
        search_value,
        search_value
    ))

    students_data = cursor.fetchall()

    close_connection(cursor, connection)

    return render_template(
        "admin_students.html",
        students=students_data,
        search=search
    )


@admin_bp.route("/admin/students/add", methods=["GET", "POST"])
def add_student():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            bp.batch_program_id,
            b.batch_name,
            p.program_name,
            p.program_code,
            d.department_name
        FROM batch_program bp
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        JOIN department d ON p.department_id = d.department_id
        ORDER BY b.batch_name, p.program_name
    """)
    batch_programs = cursor.fetchall()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        gender = request.form.get("gender", "").strip()
        account_status = request.form.get("account_status", "Active").strip()
        phone_no = request.form.get("phone_no", "").strip()
        batch_program_id = request.form.get("batch_program_id", "").strip()
        registration_no = request.form.get("registration_no", "").strip()
        student_status = request.form.get("student_status", "Active").strip()

        try:
            result_args = cursor.callproc("sp_add_student", (
                first_name,
                last_name,
                email,
                password_hash,
                gender,
                account_status,
                phone_no,
                int(batch_program_id) if batch_program_id else 0,
                registration_no,
                student_status,
                0
            ))

            connection.commit()
            flash("Student added successfully.", "success")
            return redirect(url_for("admin.students"))

        except Exception as error:
            connection.rollback()
            flash(f"Error adding student: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return render_template(
        "admin_student_add.html",
        batch_programs=batch_programs
    )


@admin_bp.route("/admin/students/<int:student_id>", methods=["GET", "POST"])
def student_detail(student_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            bp.batch_program_id,
            b.batch_name,
            p.program_name,
            p.program_code,
            d.department_name
        FROM batch_program bp
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        JOIN department d ON p.department_id = d.department_id
        ORDER BY b.batch_name, p.program_name
    """)
    batch_programs = cursor.fetchall()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        gender = request.form.get("gender", "").strip()
        account_status = request.form.get("account_status", "").strip()
        phone_no = request.form.get("phone_no", "").strip()
        batch_program_id = request.form.get("batch_program_id", "").strip()
        registration_no = request.form.get("registration_no", "").strip()
        student_status = request.form.get("student_status", "").strip()

        try:
            cursor.callproc("sp_update_student", (
                student_id,
                first_name,
                last_name,
                email,
                password_hash,
                gender,
                account_status,
                phone_no,
                int(batch_program_id) if batch_program_id else 0,
                registration_no,
                student_status
            ))

            connection.commit()
            flash("Student updated successfully.", "success")
            return redirect(url_for("admin.student_detail", student_id=student_id))

        except Exception as error:
            connection.rollback()
            flash(f"Error updating student: {clean_db_error(error)}", "danger")

    cursor.execute("""
        SELECT *
        FROM v_admin_students
        WHERE student_id = %s
    """, (student_id,))
    student = cursor.fetchone()

    if not student:
        close_connection(cursor, connection)
        flash("Student not found.", "danger")
        return redirect(url_for("admin.students"))

    student["phone_no"] = get_first_phone(cursor, student["user_id"])

    close_connection(cursor, connection)

    return render_template(
        "admin_student_detail.html",
        student=student,
        batch_programs=batch_programs
    )


@admin_bp.route("/admin/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.callproc("sp_delete_student_safe", (student_id,))
        connection.commit()
        flash("Student deleted successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting student: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return redirect(url_for("admin.students"))


# ============================================================
# FACULTY
# ============================================================

@admin_bp.route("/admin/faculty")
def faculty():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    search = request.args.get("search", "").strip()
    search_value = f"%{search}%"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            teacher_id,
            designation,
            user_id,
            first_name,
            last_name,
            email,
            gender,
            account_status,
            department_name
        FROM v_admin_faculty
        WHERE
            first_name LIKE %s
            OR last_name LIKE %s
            OR CONCAT(first_name, ' ', last_name) LIKE %s
            OR email LIKE %s
            OR department_name LIKE %s
            OR designation LIKE %s
        ORDER BY teacher_id ASC
    """, (
        search_value,
        search_value,
        search_value,
        search_value,
        search_value,
        search_value
    ))

    faculty_members = cursor.fetchall()

    close_connection(cursor, connection)

    return render_template(
        "admin_faculty.html",
        faculty_members=faculty_members,
        search=search
    )


@admin_bp.route("/admin/faculty/add", methods=["GET", "POST"])
def add_faculty():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT department_id, department_name
        FROM department
        ORDER BY department_name
    """)
    departments = cursor.fetchall()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        gender = request.form.get("gender", "").strip()
        account_status = request.form.get("account_status", "Active").strip()
        phone_no = request.form.get("phone_no", "").strip()
        department_id = request.form.get("department_id", "").strip()
        designation = request.form.get("designation", "").strip()

        try:
            cursor.callproc("sp_add_faculty", (
                first_name,
                last_name,
                email,
                password_hash,
                gender,
                account_status,
                phone_no,
                int(department_id) if department_id else 0,
                designation,
                0
            ))

            connection.commit()
            flash("Faculty member added successfully.", "success")
            return redirect(url_for("admin.faculty"))

        except Exception as error:
            connection.rollback()
            flash(f"Error adding faculty member: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return render_template("admin_faculty_add.html", departments=departments)


@admin_bp.route("/admin/faculty/<int:teacher_id>", methods=["GET", "POST"])
def faculty_detail(teacher_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT department_id, department_name
        FROM department
        ORDER BY department_name
    """)
    departments = cursor.fetchall()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        password_hash = request.form.get("password_hash", "").strip()
        gender = request.form.get("gender", "").strip()
        account_status = request.form.get("account_status", "").strip()
        phone_no = request.form.get("phone_no", "").strip()
        department_id = request.form.get("department_id", "").strip()
        designation = request.form.get("designation", "").strip()

        try:
            cursor.callproc("sp_update_faculty", (
                teacher_id,
                first_name,
                last_name,
                email,
                password_hash,
                gender,
                account_status,
                phone_no,
                int(department_id) if department_id else 0,
                designation
            ))

            connection.commit()
            flash("Faculty member updated successfully.", "success")
            return redirect(url_for("admin.faculty_detail", teacher_id=teacher_id))

        except Exception as error:
            connection.rollback()
            flash(f"Error updating faculty member: {clean_db_error(error)}", "danger")

    cursor.execute("""
        SELECT *
        FROM v_admin_faculty
        WHERE teacher_id = %s
    """, (teacher_id,))
    faculty_member = cursor.fetchone()

    if not faculty_member:
        close_connection(cursor, connection)
        flash("Faculty member not found.", "danger")
        return redirect(url_for("admin.faculty"))

    faculty_member["phone_no"] = get_first_phone(cursor, faculty_member["user_id"])

    close_connection(cursor, connection)

    return render_template(
        "admin_faculty_detail.html",
        faculty_member=faculty_member,
        departments=departments
    )


@admin_bp.route("/admin/faculty/<int:teacher_id>/delete", methods=["POST"])
def delete_faculty(teacher_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.callproc("sp_delete_faculty_safe", (teacher_id,))
        connection.commit()
        flash("Faculty member deleted successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting faculty member: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return redirect(url_for("admin.faculty"))


# ============================================================
# COURSES
# ============================================================

@admin_bp.route("/admin/courses")
def courses():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    search = request.args.get("search", "").strip()
    search_value = f"%{search}%"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            course_id,
            course_code,
            course_title,
            credit_hours,
            department_name,
            department_code
        FROM v_admin_courses
        WHERE
            course_code LIKE %s
            OR course_title LIKE %s
            OR department_name LIKE %s
            OR department_code LIKE %s
        ORDER BY course_code ASC
    """, (search_value, search_value, search_value, search_value))

    courses_data = cursor.fetchall()

    close_connection(cursor, connection)

    return render_template("admin_courses.html", courses=courses_data, search=search)


@admin_bp.route("/admin/courses/add", methods=["GET", "POST"])
def add_course():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT department_id, department_name, department_code
        FROM department
        ORDER BY department_name
    """)
    departments = cursor.fetchall()

    if request.method == "POST":
        department_id = request.form.get("department_id", "").strip()
        course_code = request.form.get("course_code", "").strip().upper()
        course_title = request.form.get("course_title", "").strip()
        credit_hours = request.form.get("credit_hours", "").strip()

        try:
            cursor.callproc("sp_add_course", (
                int(department_id) if department_id else 0,
                course_code,
                course_title,
                int(credit_hours) if credit_hours else 0,
                0
            ))

            connection.commit()
            flash("Course added successfully.", "success")
            return redirect(url_for("admin.courses"))

        except Exception as error:
            connection.rollback()
            flash(f"Error adding course: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return render_template("admin_course_add.html", departments=departments)


@admin_bp.route("/admin/courses/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.callproc("sp_delete_course_safe", (course_id,))
        connection.commit()
        flash("Course deleted successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting course: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return redirect(url_for("admin.courses"))


# ============================================================
# TEACHER ASSIGNMENTS
# ============================================================

@admin_bp.route("/admin/teacher-assignments")
def teacher_assignments():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    department_id = request.args.get("department_id", "").strip()
    program_id = request.args.get("program_id", "").strip()
    batch_id = request.args.get("batch_id", "").strip()
    section_id = request.args.get("section_id", "").strip()
    semester_id = request.args.get("semester_id", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT department_id, department_name FROM department ORDER BY department_name")
    departments = cursor.fetchall()

    cursor.execute("SELECT program_id, program_name FROM program ORDER BY program_name")
    programs = cursor.fetchall()

    cursor.execute("SELECT batch_id, batch_name FROM batch ORDER BY batch_name")
    batches = cursor.fetchall()

    cursor.execute("SELECT section_id, section_name FROM section ORDER BY section_name")
    sections = cursor.fetchall()

    cursor.execute("SELECT semester_id, semester_no FROM semester ORDER BY semester_no")
    semesters = cursor.fetchall()

    query = """
        SELECT *
        FROM v_admin_teacher_assignments
        WHERE 1 = 1
    """

    params = []

    if department_id:
        query += " AND department_id = %s"
        params.append(department_id)

    if program_id:
        query += " AND program_id = %s"
        params.append(program_id)

    if batch_id:
        query += " AND batch_id = %s"
        params.append(batch_id)

    if section_id:
        query += " AND section_id = %s"
        params.append(section_id)

    if semester_id:
        query += " AND semester_id = %s"
        params.append(semester_id)

    query += """
        ORDER BY
            batch_name,
            program_name,
            section_name,
            semester_no,
            course_code
    """

    cursor.execute(query, params)
    assignments = cursor.fetchall()

    close_connection(cursor, connection)

    return render_template(
        "admin_teacher_assignments.html",
        assignments=assignments,
        departments=departments,
        programs=programs,
        batches=batches,
        sections=sections,
        semesters=semesters,
        selected_department=department_id,
        selected_program=program_id,
        selected_batch=batch_id,
        selected_section=section_id,
        selected_semester=semester_id
    )


@admin_bp.route("/admin/teacher-assignments/add", methods=["GET", "POST"])
def add_teacher_assignment():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            f.teacher_id,
            u.first_name,
            u.last_name,
            f.designation,
            d.department_name
        FROM faculty f
        JOIN users u ON f.user_id = u.user_id
        JOIN department d ON f.department_id = d.department_id
        WHERE u.account_status = 'Active'
        ORDER BY u.first_name, u.last_name
    """)
    faculty_members = cursor.fetchall()

    cursor.execute("""
        SELECT
            c.course_id,
            c.course_code,
            c.course_title,
            d.department_name
        FROM course c
        JOIN department d ON c.department_id = d.department_id
        ORDER BY c.course_code
    """)
    courses_data = cursor.fetchall()

    cursor.execute("""
        SELECT
            sec.section_id,
            sec.section_name,
            b.batch_name,
            p.program_name,
            d.department_name
        FROM section sec
        JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        JOIN department d ON p.department_id = d.department_id
        ORDER BY b.batch_name, p.program_name, sec.section_name
    """)
    sections = cursor.fetchall()

    cursor.execute("SELECT semester_id, semester_no FROM semester ORDER BY semester_no")
    semesters = cursor.fetchall()

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id", "").strip()
        course_id = request.form.get("course_id", "").strip()
        semester_id = request.form.get("semester_id", "").strip()
        section_id = request.form.get("section_id", "").strip()
        assigned_date = request.form.get("assigned_date", "").strip()

        try:
            cursor.callproc("sp_add_teacher_assignment", (
                int(teacher_id) if teacher_id else 0,
                int(course_id) if course_id else 0,
                int(semester_id) if semester_id else 0,
                int(section_id) if section_id else 0,
                assigned_date,
                0
            ))

            connection.commit()
            flash("Teacher assignment added successfully.", "success")
            return redirect(url_for("admin.teacher_assignments"))

        except Exception as error:
            connection.rollback()
            flash(f"Error adding teacher assignment: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return render_template(
        "admin_teacher_assignment_add.html",
        faculty_members=faculty_members,
        courses=courses_data,
        sections=sections,
        semesters=semesters
    )


@admin_bp.route("/admin/teacher-assignments/<int:assignment_id>/delete", methods=["POST"])
def delete_teacher_assignment(assignment_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.callproc("sp_delete_teacher_assignment_safe", (assignment_id,))
        connection.commit()
        flash("Teacher assignment deleted successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting teacher assignment: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return redirect(url_for("admin.teacher_assignments"))


# ============================================================
# ENROLLMENTS
# ============================================================

@admin_bp.route("/admin/enrollments")
def enrollments():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    department_id = request.args.get("department_id", "").strip()
    program_id = request.args.get("program_id", "").strip()
    batch_id = request.args.get("batch_id", "").strip()
    section_id = request.args.get("section_id", "").strip()
    session_id = request.args.get("session_id", "").strip()
    semester_id = request.args.get("semester_id", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT department_id, department_name FROM department ORDER BY department_name")
    departments = cursor.fetchall()

    cursor.execute("SELECT program_id, program_name FROM program ORDER BY program_name")
    programs = cursor.fetchall()

    cursor.execute("SELECT batch_id, batch_name FROM batch ORDER BY batch_name")
    batches = cursor.fetchall()

    cursor.execute("""
        SELECT
            sec.section_id,
            sec.section_name,
            b.batch_name,
            p.program_name,
            d.department_name
        FROM section sec
        JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        JOIN department d ON p.department_id = d.department_id
        ORDER BY b.batch_name, p.program_name, sec.section_name
    """)
    sections = cursor.fetchall()

    cursor.execute("""
        SELECT session_id, session_name, academic_year
        FROM academic_session
        ORDER BY start_date DESC
    """)
    sessions = cursor.fetchall()

    cursor.execute("SELECT semester_id, semester_no FROM semester ORDER BY semester_no")
    semesters = cursor.fetchall()

    query = """
        SELECT *
        FROM v_admin_enrollments
        WHERE 1 = 1
    """

    params = []

    if department_id:
        query += " AND department_id = %s"
        params.append(department_id)

    if program_id:
        query += " AND program_id = %s"
        params.append(program_id)

    if batch_id:
        query += " AND batch_id = %s"
        params.append(batch_id)

    if section_id:
        query += " AND section_id = %s"
        params.append(section_id)

    if session_id:
        query += " AND session_id = %s"
        params.append(session_id)

    if semester_id:
        query += " AND semester_id = %s"
        params.append(semester_id)

    query += """
        ORDER BY
            session_start_date DESC,
            batch_name,
            program_name,
            section_name,
            semester_no,
            registration_no
    """

    cursor.execute(query, params)
    enrollments_data = cursor.fetchall()

    close_connection(cursor, connection)

    return render_template(
        "admin_enrollments.html",
        enrollments=enrollments_data,
        departments=departments,
        programs=programs,
        batches=batches,
        sections=sections,
        sessions=sessions,
        semesters=semesters,
        selected_department=department_id,
        selected_program=program_id,
        selected_batch=batch_id,
        selected_section=section_id,
        selected_session=session_id,
        selected_semester=semester_id
    )


@admin_bp.route("/admin/enrollments/add", methods=["GET", "POST"])
def add_enrollment():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT session_id, session_name, academic_year
        FROM academic_session
        ORDER BY start_date DESC
    """)
    sessions = cursor.fetchall()

    cursor.execute("""
        SELECT semester_id, semester_no
        FROM semester
        ORDER BY semester_no
    """)
    semesters = cursor.fetchall()

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        section_id = request.form.get("section_id", "").strip()
        session_id = request.form.get("session_id", "").strip()
        semester_id = request.form.get("semester_id", "").strip()
        is_repeat = request.form.get("is_repeat", "No").strip()
        enrollment_status = request.form.get("enrollment_status", "Currently enrolled").strip()
        enrollment_start_date = request.form.get("enrollment_start_date", "").strip()
        enrollment_end_date = request.form.get("enrollment_end_date") or None
        selected_assignments = request.form.getlist("teacher_assignment_ids")

        try:
            if not selected_assignments:
                flash("Please select at least one course for this enrollment.", "warning")
                close_connection(cursor, connection)
                return redirect(url_for("admin.add_enrollment"))

            result_args = cursor.callproc("sp_add_enrollment", (
                int(student_id) if student_id else 0,
                int(section_id) if section_id else 0,
                int(session_id) if session_id else 0,
                int(semester_id) if semester_id else 0,
                is_repeat,
                enrollment_status,
                enrollment_start_date,
                enrollment_end_date,
                0
            ))

            enrollment_id = result_args[-1]

            for assignment_id in selected_assignments:
                cursor.callproc("sp_add_registered_course", (
                    int(enrollment_id),
                    int(assignment_id)
                ))

            connection.commit()
            flash("Enrollment added successfully.", "success")
            return redirect(url_for("admin.enrollment_detail", enrollment_id=enrollment_id))

        except Exception as error:
            connection.rollback()
            flash(f"Error adding enrollment: {clean_db_error(error)}", "danger")

    close_connection(cursor, connection)

    return render_template(
        "admin_enrollment_add.html",
        sessions=sessions,
        semesters=semesters
    )


@admin_bp.route("/admin/enrollments/<int:enrollment_id>")
def enrollment_detail(enrollment_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM v_admin_enrollments
        WHERE enrollment_id = %s
    """, (enrollment_id,))
    enrollment = cursor.fetchone()

    if not enrollment:
        close_connection(cursor, connection)
        flash("Enrollment not found.", "danger")
        return redirect(url_for("admin.enrollments"))

    enrollment["phone_no"] = get_first_phone(cursor, enrollment["user_id"])

    cursor.execute("""
        SELECT *
        FROM v_admin_enrollment_registered_courses
        WHERE enrollment_id = %s
        ORDER BY course_code
    """, (enrollment_id,))
    registered_courses = cursor.fetchall()

    close_connection(cursor, connection)

    return render_template(
        "admin_enrollment_detail.html",
        enrollment=enrollment,
        registered_courses=registered_courses
    )


# ============================================================
# API ROUTES
# ============================================================

@admin_bp.route("/admin/api/student-by-registration")
def student_by_registration():
    if not admin_required():
        return {"success": False, "message": "Unauthorized"}

    registration_no = request.args.get("registration_no", "").strip()

    if not registration_no:
        return {"success": False, "message": "Please enter registration number."}

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            student_id,
            registration_no,
            student_status,
            batch_program_id,
            first_name,
            last_name,
            email,
            account_status,
            department_id,
            department_name,
            program_id,
            program_name,
            batch_id,
            batch_name
        FROM v_admin_students
        WHERE registration_no = %s
    """, (registration_no,))
    student = cursor.fetchone()

    if not student:
        close_connection(cursor, connection)
        return {"success": False, "message": "Student not found."}

    if student["account_status"] != "Active":
        close_connection(cursor, connection)
        return {"success": False, "message": "Student account is not active."}

    cursor.execute("""
        SELECT
            sec.section_id,
            sec.section_name,
            b.batch_name,
            p.program_name,
            d.department_name
        FROM section sec
        JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        JOIN department d ON p.department_id = d.department_id
        WHERE p.program_id = %s
        ORDER BY b.batch_name, sec.section_name
    """, (student["program_id"],))

    sections = cursor.fetchall()

    close_connection(cursor, connection)

    return {
        "success": True,
        "student": student,
        "sections": sections
    }


@admin_bp.route("/admin/api/enrollment-courses")
def enrollment_courses():
    if not admin_required():
        return {"success": False, "message": "Unauthorized"}

    student_id = request.args.get("student_id", "").strip()
    section_id = request.args.get("section_id", "").strip()
    semester_id = request.args.get("semester_id", "").strip()

    if not student_id or not section_id or not semester_id:
        return {"success": False, "message": "Student, section, and semester are required."}

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            batch_program_id,
            program_id
        FROM v_admin_students
        WHERE student_id = %s
    """, (student_id,))
    student_data = cursor.fetchone()

    cursor.execute("""
        SELECT
            bp.program_id AS section_program_id
        FROM section sec
        JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
        WHERE sec.section_id = %s
    """, (section_id,))
    section_data = cursor.fetchone()

    if not student_data or not section_data:
        close_connection(cursor, connection)
        return {"success": False, "message": "Invalid student or section."}

    if student_data["program_id"] != section_data["section_program_id"]:
        close_connection(cursor, connection)
        return {
            "success": False,
            "message": "Selected section does not belong to this student's program."
        }

    cursor.execute("""
        SELECT
            ta.teacher_assignment_id,
            c.course_code,
            c.course_title,
            c.credit_hours,
            u.first_name AS teacher_first_name,
            u.last_name AS teacher_last_name
        FROM teacher_assignment ta
        JOIN course c ON ta.course_id = c.course_id
        JOIN faculty f ON ta.teacher_id = f.teacher_id
        JOIN users u ON f.user_id = u.user_id
        WHERE ta.section_id = %s
          AND ta.semester_id = %s
          AND u.account_status = 'Active'
        ORDER BY c.course_code
    """, (section_id, semester_id))

    courses = cursor.fetchall()

    close_connection(cursor, connection)

    if not courses:
        return {
            "success": False,
            "message": "No assigned courses found for this section and semester."
        }

    return {
        "success": True,
        "courses": courses
    }