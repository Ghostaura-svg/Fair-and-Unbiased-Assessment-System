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
        return message.split(":")[-1].strip()

    if "1451" in message:
        return "This record is linked with other data and cannot be deleted."

    if "1062" in message:
        return "Duplicate record found."

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
# ADMIN STUDENTS
# ============================================================

@admin_bp.route("/admin/students")
def students():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        search_value = f"%{search}%"

        cursor.execute("""
            SELECT
                s.student_id,
                s.registration_no,
                s.student_status,
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.account_status,
                d.department_name,
                p.program_name,
                b.batch_name
            FROM student s
            JOIN users u ON s.user_id = u.user_id
            JOIN batch_program bp ON s.batch_program_id = bp.batch_program_id
            JOIN batch b ON bp.batch_id = b.batch_id
            JOIN program p ON bp.program_id = p.program_id
            JOIN department d ON p.department_id = d.department_id
            WHERE
                s.registration_no LIKE %s
                OR u.first_name LIKE %s
                OR u.last_name LIKE %s
                OR CONCAT(u.first_name, ' ', u.last_name) LIKE %s
                OR d.department_name LIKE %s
                OR p.program_name LIKE %s
                OR b.batch_name LIKE %s
            ORDER BY s.student_id ASC
        """, (
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ))

        students = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin_students.html",
        students=students,
        search=search
    )


@admin_bp.route("/admin/students/add", methods=["GET", "POST"])
def add_student():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
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
            student_status = request.form.get("student_status", "Enrolled").strip()

            try:
                cursor.callproc("sp_add_student", (
                    first_name,
                    last_name,
                    email,
                    password_hash,
                    gender,
                    account_status,
                    phone_no,
                    batch_program_id,
                    registration_no,
                    student_status
                ))

                connection.commit()
                flash("Student added successfully.", "success")
                return redirect(url_for("admin.students"))

            except Exception as error:
                connection.rollback()
                flash(f"Error adding student: {clean_db_error(error)}", "danger")
                return redirect(url_for("admin.add_student"))

    finally:
        cursor.close()
        connection.close()

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

    try:
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
            student_status = request.form.get("student_status", "Enrolled").strip()

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
                    batch_program_id,
                    registration_no,
                    student_status
                ))

                connection.commit()
                flash("Student updated successfully.", "success")
                return redirect(url_for("admin.student_detail", student_id=student_id))

            except Exception as error:
                connection.rollback()
                flash(f"Error updating student: {clean_db_error(error)}", "danger")
                return redirect(url_for("admin.student_detail", student_id=student_id))

        cursor.execute("""
            SELECT
                s.student_id,
                s.registration_no,
                s.student_status,
                s.batch_program_id,
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.password_hash,
                u.gender,
                u.account_status,
                u.created_at,
                d.department_name,
                p.program_name,
                p.program_code,
                b.batch_name,
                bp.expected_graduation
            FROM student s
            JOIN users u ON s.user_id = u.user_id
            JOIN batch_program bp ON s.batch_program_id = bp.batch_program_id
            JOIN batch b ON bp.batch_id = b.batch_id
            JOIN program p ON bp.program_id = p.program_id
            JOIN department d ON p.department_id = d.department_id
            WHERE s.student_id = %s
        """, (student_id,))
        student = cursor.fetchone()

        if not student:
            flash("Student not found.", "danger")
            return redirect(url_for("admin.students"))

        cursor.execute("""
            SELECT phone_no
            FROM user_phone
            WHERE user_id = %s
            LIMIT 1
        """, (student["user_id"],))
        phone = cursor.fetchone()

        student["phone_no"] = phone["phone_no"] if phone else ""

    finally:
        cursor.close()
        connection.close()

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

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.students"))




# ============================================================
# ADMIN FACULTY
# ============================================================

@admin_bp.route("/admin/faculty")
def faculty():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        search_value = f"%{search}%"

        cursor.execute("""
            SELECT
                f.teacher_id,
                f.designation,
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.gender,
                u.account_status,
                d.department_name
            FROM faculty f
            JOIN users u ON f.user_id = u.user_id
            JOIN department d ON f.department_id = d.department_id
            WHERE
                u.first_name LIKE %s
                OR u.last_name LIKE %s
                OR CONCAT(u.first_name, ' ', u.last_name) LIKE %s
                OR u.email LIKE %s
                OR d.department_name LIKE %s
                OR f.designation LIKE %s
            ORDER BY f.teacher_id ASC
        """, (
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ))

        faculty_members = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

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

    try:
        cursor.execute("""
            SELECT
                department_id,
                department_name,
                department_code
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
                    department_id,
                    designation
                ))

                connection.commit()
                flash("Faculty member added successfully.", "success")
                return redirect(url_for("admin.faculty"))

            except Exception as error:
                connection.rollback()
                flash(f"Error adding faculty member: {clean_db_error(error)}", "danger")
                return redirect(url_for("admin.add_faculty"))

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin_faculty_add.html",
        departments=departments
    )


@admin_bp.route("/admin/faculty/<int:teacher_id>", methods=["GET", "POST"])
def faculty_detail(teacher_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                department_id,
                department_name,
                department_code
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
                cursor.callproc("sp_update_faculty", (
                    teacher_id,
                    first_name,
                    last_name,
                    email,
                    password_hash,
                    gender,
                    account_status,
                    phone_no,
                    department_id,
                    designation
                ))

                connection.commit()
                flash("Faculty member updated successfully.", "success")
                return redirect(url_for("admin.faculty_detail", teacher_id=teacher_id))

            except Exception as error:
                connection.rollback()
                flash(f"Error updating faculty member: {clean_db_error(error)}", "danger")
                return redirect(url_for("admin.faculty_detail", teacher_id=teacher_id))

        cursor.execute("""
            SELECT
                f.teacher_id,
                f.department_id,
                f.designation,
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.password_hash,
                u.gender,
                u.account_status,
                u.created_at,
                d.department_name
            FROM faculty f
            JOIN users u ON f.user_id = u.user_id
            JOIN department d ON f.department_id = d.department_id
            WHERE f.teacher_id = %s
        """, (teacher_id,))
        faculty_member = cursor.fetchone()

        if not faculty_member:
            flash("Faculty member not found.", "danger")
            return redirect(url_for("admin.faculty"))

        cursor.execute("""
            SELECT phone_no
            FROM user_phone
            WHERE user_id = %s
            LIMIT 1
        """, (faculty_member["user_id"],))
        phone = cursor.fetchone()

        faculty_member["phone_no"] = phone["phone_no"] if phone else ""

    finally:
        cursor.close()
        connection.close()

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

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.faculty"))



# ============================================================
# ADMIN COURSES
# ============================================================

@admin_bp.route("/admin/courses")
def courses():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        search_value = f"%{search}%"

        cursor.execute("""
            SELECT
                c.course_id,
                c.department_id,
                c.course_code,
                c.course_title,
                c.course_title AS course_name,
                c.credit_hours,
                d.department_name,
                d.department_code,

                NULL AS semester_id,
                NULL AS semester_name

            FROM course c
            JOIN department d ON c.department_id = d.department_id

            WHERE
                c.course_code LIKE %s
                OR c.course_title LIKE %s
                OR d.department_name LIKE %s
                OR d.department_code LIKE %s

            ORDER BY c.course_id ASC
        """, (
            search_value,
            search_value,
            search_value,
            search_value
        ))

        courses = cursor.fetchall()

    except Exception as error:
        flash(f"Error loading courses: {clean_db_error(error)}", "danger")
        courses = []

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin_courses.html",
        courses=courses,
        search=search
    )


@admin_bp.route("/admin/courses/add", methods=["GET", "POST"])
def add_course():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                department_id,
                department_name,
                department_code
            FROM department
            ORDER BY department_name
        """)
        departments = cursor.fetchall()

        # I am also sending semesters only to avoid template error
        # if your old course form still contains semester dropdown.
        cursor.execute("""
            SELECT
                semester_id,
                semester_no,
                CONCAT('Semester ', semester_no) AS semester_name
            FROM semester
            ORDER BY semester_no
        """)
        semesters = cursor.fetchall()

        if request.method == "POST":
            course_code = request.form.get("course_code", "").strip().upper()

            # This handles both possible template field names:
            # course_title or course_name
            course_title = request.form.get("course_title", "").strip()
            if not course_title:
                course_title = request.form.get("course_name", "").strip()

            department_id = request.form.get("department_id", "").strip()
            credit_hours = request.form.get("credit_hours", "").strip()

            try:
                if not department_id or not course_code or not course_title or not credit_hours:
                    flash("Department, course code, course title, and credit hours are required.", "warning")
                    return redirect(url_for("admin.add_course"))

                credit_hours = int(credit_hours)

                if credit_hours <= 0:
                    flash("Credit hours must be greater than zero.", "warning")
                    return redirect(url_for("admin.add_course"))

                # sp_add_course expects exactly 4 arguments:
                # department_id, course_code, course_title, credit_hours
                cursor.callproc("sp_add_course", (
                    department_id,
                    course_code,
                    course_title,
                    credit_hours
                ))

                connection.commit()
                flash("Course added successfully.", "success")
                return redirect(url_for("admin.courses"))

            except ValueError:
                flash("Credit hours must be a valid number.", "danger")
                return redirect(url_for("admin.add_course"))

            except Exception as error:
                connection.rollback()
                flash(f"Error adding course: {clean_db_error(error)}", "danger")
                return redirect(url_for("admin.add_course"))

    except Exception as error:
        flash(f"Error opening course form: {clean_db_error(error)}", "danger")
        departments = []
        semesters = []

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin_course_add.html",
        departments=departments,
        semesters=semesters
    )


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

    finally:
        cursor.close()
        connection.close()

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

    try:
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

        cursor.execute("""
            SELECT semester_id, semester_no
            FROM semester
            ORDER BY semester_no
        """)
        semesters = cursor.fetchall()

        if request.method == "POST":
            teacher_id = request.form.get("teacher_id", "").strip()
            course_id = request.form.get("course_id", "").strip()
            semester_id = request.form.get("semester_id", "").strip()
            section_id = request.form.get("section_id", "").strip()
            assigned_date = request.form.get("assigned_date", "").strip()

            try:
                if not teacher_id or not course_id or not semester_id or not section_id or not assigned_date:
                    flash("All teacher assignment fields are required.", "warning")
                    return redirect(url_for("admin.add_teacher_assignment"))

                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM teacher_assignment
                    WHERE course_id = %s
                      AND semester_id = %s
                      AND section_id = %s
                """, (course_id, semester_id, section_id))
                duplicate_course = cursor.fetchone()["total"]

                if duplicate_course > 0:
                    flash("This course is already assigned for the selected section and semester.", "warning")
                    return redirect(url_for("admin.add_teacher_assignment"))

                cursor.execute("""
                    INSERT INTO teacher_assignment
                    (teacher_id, course_id, semester_id, section_id, assigned_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, (teacher_id, course_id, semester_id, section_id, assigned_date))

                connection.commit()
                flash("Teacher assignment added successfully.", "success")
                return redirect(url_for("admin.teacher_assignments"))

            except Exception as error:
                connection.rollback()
                flash(f"Error adding teacher assignment: {clean_db_error(error)}", "danger")
                return redirect(url_for("admin.add_teacher_assignment"))

    finally:
        cursor.close()
        connection.close()

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

    try:
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
                if not student_id or not section_id or not session_id or not semester_id or not enrollment_start_date:
                    flash("Student, section, session, semester, and start date are required.", "warning")
                    return redirect(url_for("admin.add_enrollment"))

                if not selected_assignments:
                    flash("Please select at least one course for this enrollment.", "warning")
                    return redirect(url_for("admin.add_enrollment"))

                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM enrollment
                    WHERE student_id = %s
                      AND section_id = %s
                      AND session_id = %s
                      AND semester_id = %s
                      AND enrollment_end_date IS NULL
                """, (student_id, section_id, session_id, semester_id))
                duplicate_enrollment = cursor.fetchone()["total"]

                if duplicate_enrollment > 0:
                    flash("This student is already actively enrolled in the selected section, session, and semester.", "warning")
                    return redirect(url_for("admin.add_enrollment"))

                cursor.execute("""
                    INSERT INTO enrollment
                    (student_id, section_id, session_id, semester_id, is_repeat,
                     enrollment_status, enrollment_start_date, enrollment_end_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    student_id,
                    section_id,
                    session_id,
                    semester_id,
                    is_repeat,
                    enrollment_status,
                    enrollment_start_date,
                    enrollment_end_date
                ))

                enrollment_id = cursor.lastrowid

                for assignment_id in selected_assignments:
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM registered_course
                        WHERE enrollment_id = %s
                          AND teacher_assignment_id = %s
                    """, (enrollment_id, assignment_id))
                    duplicate_course = cursor.fetchone()["total"]

                    if duplicate_course == 0:
                        cursor.execute("""
                            INSERT INTO registered_course
                            (enrollment_id, teacher_assignment_id, registration_status)
                            VALUES (%s, %s, 'Registered')
                        """, (enrollment_id, assignment_id))

                connection.commit()
                flash("Enrollment added successfully.", "success")
                return redirect(url_for("admin.enrollment_detail", enrollment_id=enrollment_id))

            except Exception as error:
                connection.rollback()
                flash(f"Error adding enrollment: {clean_db_error(error)}", "danger")
                return redirect(url_for("admin.add_enrollment"))

    finally:
        cursor.close()
        connection.close()

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















# ============================================================
# ACADEMIC SETUP: DEPARTMENT, PROGRAM, SECTION
# ============================================================

@admin_bp.route("/admin/academic-setup")
def academic_setup():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                department_id,
                department_name,
                department_code
            FROM department
            ORDER BY department_name
        """)
        departments = cursor.fetchall()

        cursor.execute("""
            SELECT
                p.program_id,
                p.department_id,
                p.program_name,
                p.program_code,
                p.degree_level,
                p.total_semester,
                d.department_name,
                d.department_code
            FROM program p
            JOIN department d ON p.department_id = d.department_id
            ORDER BY d.department_name, p.program_name
        """)
        programs = cursor.fetchall()

        cursor.execute("""
            SELECT
                sec.section_id,
                sec.batch_program_id,
                sec.section_name,
                sec.capacity,
                b.batch_name,
                p.program_name,
                p.program_code,
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

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin_academic_setup.html",
        departments=departments,
        programs=programs,
        sections=sections,
        batch_programs=batch_programs
    )


# ============================================================
# ACADEMIC SETUP EDIT PAGES
# ============================================================

@admin_bp.route("/admin/academic-setup/departments/<int:department_id>/edit")
def edit_department(department_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                department_id,
                department_name,
                department_code
            FROM department
            WHERE department_id = %s
        """, (department_id,))
        department = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not department:
        flash("Department not found.", "danger")
        return redirect(url_for("admin.academic_setup"))

    return render_template(
        "admin_academic_edit.html",
        edit_type="department",
        record=department
    )


@admin_bp.route("/admin/academic-setup/programs/<int:program_id>/edit")
def edit_program(program_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                program_id,
                department_id,
                program_name,
                program_code,
                degree_level,
                total_semester
            FROM program
            WHERE program_id = %s
        """, (program_id,))
        program = cursor.fetchone()

        cursor.execute("""
            SELECT
                department_id,
                department_name,
                department_code
            FROM department
            ORDER BY department_name
        """)
        departments = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    if not program:
        flash("Program not found.", "danger")
        return redirect(url_for("admin.academic_setup"))

    return render_template(
        "admin_academic_edit.html",
        edit_type="program",
        record=program,
        departments=departments
    )


@admin_bp.route("/admin/academic-setup/sections/<int:section_id>/edit")
def edit_section(section_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                section_id,
                batch_program_id,
                section_name,
                capacity
            FROM section
            WHERE section_id = %s
        """, (section_id,))
        section = cursor.fetchone()

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

    finally:
        cursor.close()
        connection.close()

    if not section:
        flash("Section not found.", "danger")
        return redirect(url_for("admin.academic_setup"))

    return render_template(
        "admin_academic_edit.html",
        edit_type="section",
        record=section,
        batch_programs=batch_programs
    )


# ============================================================
# DEPARTMENT ADD / UPDATE / DELETE
# ============================================================

@admin_bp.route("/admin/academic-setup/departments/add", methods=["POST"])
def add_department():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    department_name = request.form.get("department_name", "").strip()
    department_code = request.form.get("department_code", "").strip().upper()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not department_name or not department_code:
            flash("Department name and department code are required.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM department
            WHERE LOWER(department_name) = LOWER(%s)
               OR LOWER(department_code) = LOWER(%s)
        """, (department_name, department_code))
        duplicate = cursor.fetchone()["total"]

        if duplicate > 0:
            flash("Department name or department code already exists.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            INSERT INTO department
            (department_name, department_code)
            VALUES (%s, %s)
        """, (department_name, department_code))

        connection.commit()
        flash("Department added successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error adding department: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


@admin_bp.route("/admin/academic-setup/departments/<int:department_id>/update", methods=["POST"])
def update_department(department_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    department_name = request.form.get("department_name", "").strip()
    department_code = request.form.get("department_code", "").strip().upper()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not department_name or not department_code:
            flash("Department name and department code are required.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM department
            WHERE (LOWER(department_name) = LOWER(%s)
                   OR LOWER(department_code) = LOWER(%s))
              AND department_id <> %s
        """, (department_name, department_code, department_id))
        duplicate = cursor.fetchone()["total"]

        if duplicate > 0:
            flash("Another department already has this name or code.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            UPDATE department
            SET department_name = %s,
                department_code = %s
            WHERE department_id = %s
        """, (department_name, department_code, department_id))

        connection.commit()
        flash("Department updated successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error updating department: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


@admin_bp.route("/admin/academic-setup/departments/<int:department_id>/delete", methods=["POST"])
def delete_department(department_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM program
            WHERE department_id = %s
        """, (department_id,))
        program_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM course
            WHERE department_id = %s
        """, (department_id,))
        course_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM faculty
            WHERE department_id = %s
        """, (department_id,))
        faculty_count = cursor.fetchone()["total"]

        if program_count > 0 or course_count > 0 or faculty_count > 0:
            flash("Cannot delete department because it is linked with programs, courses, or faculty members.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            DELETE FROM department
            WHERE department_id = %s
        """, (department_id,))

        connection.commit()
        flash("Department deleted successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting department: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


# ============================================================
# PROGRAM ADD / UPDATE / DELETE
# ============================================================

@admin_bp.route("/admin/academic-setup/programs/add", methods=["POST"])
def add_program():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    department_id = request.form.get("department_id", "").strip()
    program_name = request.form.get("program_name", "").strip()
    program_code = request.form.get("program_code", "").strip().upper()
    degree_level = request.form.get("degree_level", "").strip()
    total_semester = request.form.get("total_semester", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not department_id or not program_name or not program_code or not degree_level or not total_semester:
            flash("All program fields are required.", "warning")
            return redirect(url_for("admin.academic_setup"))

        total_semester = int(total_semester)

        if total_semester <= 0:
            flash("Total semesters must be greater than zero.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM department
            WHERE department_id = %s
        """, (department_id,))
        department_exists = cursor.fetchone()["total"]

        if department_exists == 0:
            flash("Selected department does not exist.", "danger")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM program
            WHERE LOWER(program_code) = LOWER(%s)
               OR (LOWER(program_name) = LOWER(%s) AND department_id = %s)
        """, (program_code, program_name, department_id))
        duplicate = cursor.fetchone()["total"]

        if duplicate > 0:
            flash("Program code already exists or this program already exists in the selected department.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            INSERT INTO program
            (department_id, program_name, program_code, degree_level, total_semester)
            VALUES (%s, %s, %s, %s, %s)
        """, (department_id, program_name, program_code, degree_level, total_semester))

        connection.commit()
        flash("Program added successfully.", "success")

    except ValueError:
        flash("Total semesters must be a valid number.", "danger")

    except Exception as error:
        connection.rollback()
        flash(f"Error adding program: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


@admin_bp.route("/admin/academic-setup/programs/<int:program_id>/update", methods=["POST"])
def update_program(program_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    department_id = request.form.get("department_id", "").strip()
    program_name = request.form.get("program_name", "").strip()
    program_code = request.form.get("program_code", "").strip().upper()
    degree_level = request.form.get("degree_level", "").strip()
    total_semester = request.form.get("total_semester", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not department_id or not program_name or not program_code or not degree_level or not total_semester:
            flash("All program fields are required.", "warning")
            return redirect(url_for("admin.academic_setup"))

        total_semester = int(total_semester)

        if total_semester <= 0:
            flash("Total semesters must be greater than zero.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT department_id
            FROM program
            WHERE program_id = %s
        """, (program_id,))
        existing_program = cursor.fetchone()

        if not existing_program:
            flash("Program not found.", "danger")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM department
            WHERE department_id = %s
        """, (department_id,))
        department_exists = cursor.fetchone()["total"]

        if department_exists == 0:
            flash("Selected department does not exist.", "danger")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM batch_program
            WHERE program_id = %s
        """, (program_id,))
        linked_batch_programs = cursor.fetchone()["total"]

        if linked_batch_programs > 0 and int(department_id) != int(existing_program["department_id"]):
            flash("Cannot change department because this program is already linked with batch-program records.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM program
            WHERE (LOWER(program_code) = LOWER(%s)
                   OR (LOWER(program_name) = LOWER(%s) AND department_id = %s))
              AND program_id <> %s
        """, (program_code, program_name, department_id, program_id))
        duplicate = cursor.fetchone()["total"]

        if duplicate > 0:
            flash("Another program already has this code or name in the selected department.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            UPDATE program
            SET department_id = %s,
                program_name = %s,
                program_code = %s,
                degree_level = %s,
                total_semester = %s
            WHERE program_id = %s
        """, (department_id, program_name, program_code, degree_level, total_semester, program_id))

        connection.commit()
        flash("Program updated successfully.", "success")

    except ValueError:
        flash("Total semesters must be a valid number.", "danger")

    except Exception as error:
        connection.rollback()
        flash(f"Error updating program: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


@admin_bp.route("/admin/academic-setup/programs/<int:program_id>/delete", methods=["POST"])
def delete_program(program_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM batch_program
            WHERE program_id = %s
        """, (program_id,))
        batch_program_count = cursor.fetchone()["total"]

        if batch_program_count > 0:
            flash("Cannot delete program because it is linked with batch-program records.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            DELETE FROM program
            WHERE program_id = %s
        """, (program_id,))

        connection.commit()
        flash("Program deleted successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting program: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


# ============================================================
# SECTION ADD / UPDATE / DELETE
# ============================================================

@admin_bp.route("/admin/academic-setup/sections/add", methods=["POST"])
def add_section():
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    batch_program_id = request.form.get("batch_program_id", "").strip()
    section_name = request.form.get("section_name", "").strip().upper()
    capacity = request.form.get("capacity", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not batch_program_id or not section_name or not capacity:
            flash("All section fields are required.", "warning")
            return redirect(url_for("admin.academic_setup"))

        capacity = int(capacity)

        if capacity <= 0:
            flash("Section capacity must be greater than zero.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM batch_program
            WHERE batch_program_id = %s
        """, (batch_program_id,))
        batch_program_exists = cursor.fetchone()["total"]

        if batch_program_exists == 0:
            flash("Selected batch-program does not exist.", "danger")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM section
            WHERE batch_program_id = %s
              AND LOWER(section_name) = LOWER(%s)
        """, (batch_program_id, section_name))
        duplicate = cursor.fetchone()["total"]

        if duplicate > 0:
            flash("This section already exists for the selected batch-program.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            INSERT INTO section
            (batch_program_id, section_name, capacity)
            VALUES (%s, %s, %s)
        """, (batch_program_id, section_name, capacity))

        connection.commit()
        flash("Section added successfully.", "success")

    except ValueError:
        flash("Capacity must be a valid number.", "danger")

    except Exception as error:
        connection.rollback()
        flash(f"Error adding section: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


@admin_bp.route("/admin/academic-setup/sections/<int:section_id>/update", methods=["POST"])
def update_section(section_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    batch_program_id = request.form.get("batch_program_id", "").strip()
    section_name = request.form.get("section_name", "").strip().upper()
    capacity = request.form.get("capacity", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not batch_program_id or not section_name or not capacity:
            flash("All section fields are required.", "warning")
            return redirect(url_for("admin.academic_setup"))

        capacity = int(capacity)

        if capacity <= 0:
            flash("Section capacity must be greater than zero.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT batch_program_id
            FROM section
            WHERE section_id = %s
        """, (section_id,))
        existing_section = cursor.fetchone()

        if not existing_section:
            flash("Section not found.", "danger")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM batch_program
            WHERE batch_program_id = %s
        """, (batch_program_id,))
        batch_program_exists = cursor.fetchone()["total"]

        if batch_program_exists == 0:
            flash("Selected batch-program does not exist.", "danger")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM enrollment
            WHERE section_id = %s
        """, (section_id,))
        enrollment_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM teacher_assignment
            WHERE section_id = %s
        """, (section_id,))
        assignment_count = cursor.fetchone()["total"]

        if (enrollment_count > 0 or assignment_count > 0) and int(batch_program_id) != int(existing_section["batch_program_id"]):
            flash("Cannot change batch-program because this section is already used in enrollments or teacher assignments.", "warning")
            return redirect(url_for("admin.academic_setup"))

        if capacity < enrollment_count:
            flash("Section capacity cannot be less than existing enrollment records.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM section
            WHERE batch_program_id = %s
              AND LOWER(section_name) = LOWER(%s)
              AND section_id <> %s
        """, (batch_program_id, section_name, section_id))
        duplicate = cursor.fetchone()["total"]

        if duplicate > 0:
            flash("Another section with this name already exists for the selected batch-program.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            UPDATE section
            SET batch_program_id = %s,
                section_name = %s,
                capacity = %s
            WHERE section_id = %s
        """, (batch_program_id, section_name, capacity, section_id))

        connection.commit()
        flash("Section updated successfully.", "success")

    except ValueError:
        flash("Capacity must be a valid number.", "danger")

    except Exception as error:
        connection.rollback()
        flash(f"Error updating section: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))


@admin_bp.route("/admin/academic-setup/sections/<int:section_id>/delete", methods=["POST"])
def delete_section(section_id):
    if not admin_required():
        return redirect(url_for("auth.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM enrollment
            WHERE section_id = %s
        """, (section_id,))
        enrollment_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM teacher_assignment
            WHERE section_id = %s
        """, (section_id,))
        assignment_count = cursor.fetchone()["total"]

        if enrollment_count > 0 or assignment_count > 0:
            flash("Cannot delete section because it is linked with enrollments or teacher assignments.", "warning")
            return redirect(url_for("admin.academic_setup"))

        cursor.execute("""
            DELETE FROM section
            WHERE section_id = %s
        """, (section_id,))

        connection.commit()
        flash("Section deleted successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting section: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.academic_setup"))
