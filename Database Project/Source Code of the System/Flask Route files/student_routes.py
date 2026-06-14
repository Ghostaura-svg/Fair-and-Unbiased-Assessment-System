from flask import Blueprint, render_template, redirect, url_for, session, request, flash, send_file, abort
from db import get_db_connection
import os

student_bp = Blueprint("student", __name__)

BASE_PROJECT_PATH = r"C:\Users\admin\Desktop\Fair and Un biased System"

DUMMY_SUBMISSION_PATH = os.path.join(BASE_PROJECT_PATH, "dummy_student_submission.pdf")
DUMMY_STUDENT_REPORT_PATH = os.path.join(BASE_PROJECT_PATH, "dummy_student_evaluation_report.pdf")


def student_required():
    return "user_id" in session and session.get("role") == "Student"


def get_current_session(cursor):
    cursor.execute("""
        SELECT
            session_id,
            session_name,
            academic_year,
            start_date,
            end_date
        FROM academic_session
        WHERE CURDATE() BETWEEN start_date AND end_date
        ORDER BY start_date DESC
        LIMIT 1
    """)
    current_session = cursor.fetchone()

    if current_session:
        return current_session

    cursor.execute("""
        SELECT
            session_id,
            session_name,
            academic_year,
            start_date,
            end_date
        FROM academic_session
        WHERE start_date <= CURDATE()
        ORDER BY start_date DESC
        LIMIT 1
    """)
    return cursor.fetchone()


def get_logged_in_student(cursor):
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
            u.gender,
            b.batch_name,
            p.program_name,
            p.program_code,
            d.department_name
        FROM student s
        JOIN users u ON s.user_id = u.user_id
        JOIN batch_program bp ON s.batch_program_id = bp.batch_program_id
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        JOIN department d ON p.department_id = d.department_id
        WHERE s.user_id = %s
    """, (session["user_id"],))

    return cursor.fetchone()


def resolve_pdf_path(path_from_db, fallback_path):
    if path_from_db and os.path.exists(path_from_db):
        return path_from_db

    if path_from_db:
        normalized_path = path_from_db.replace("/", "\\").lstrip("\\")
        possible_path = os.path.join(BASE_PROJECT_PATH, normalized_path)

        if os.path.exists(possible_path):
            return possible_path

    if os.path.exists(fallback_path):
        return fallback_path

    return None


@student_bp.route("/student/dashboard")
def student_dashboard():
    if not student_required():
        return redirect(url_for("auth.student_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    student = get_logged_in_student(cursor)

    if not student:
        cursor.close()
        connection.close()
        flash("Student profile not found.", "danger")
        return redirect(url_for("auth.student_login"))

    current_session = get_current_session(cursor)

    courses = []
    total_courses = 0
    total_open_portals = 0
    total_submissions = 0
    total_evaluated = 0

    if current_session:
        cursor.execute("""
            SELECT
                rc.registered_course_id,
                rc.registration_status,
                e.enrollment_id,
                e.enrollment_status,
                c.course_code,
                c.course_title,
                c.credit_hours,
                sec.section_name,
                sem.semester_no,
                f.teacher_id,
                fu.first_name AS faculty_first_name,
                fu.last_name AS faculty_last_name,
                COUNT(DISTINCT a.assessment_id) AS total_assessments,
                SUM(CASE WHEN a.portal_status = 'Open' THEN 1 ELSE 0 END) AS open_portals
            FROM registered_course rc
            JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
            JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
            JOIN course c ON ta.course_id = c.course_id
            JOIN section sec ON ta.section_id = sec.section_id
            JOIN semester sem ON ta.semester_id = sem.semester_id
            JOIN faculty f ON ta.teacher_id = f.teacher_id
            JOIN users fu ON f.user_id = fu.user_id
            LEFT JOIN assessment a
                   ON a.teacher_assignment_id = ta.teacher_assignment_id
                  AND a.session_id = e.session_id
            WHERE e.student_id = %s
              AND e.session_id = %s
              AND e.enrollment_status = 'Currently enrolled'
            GROUP BY
                rc.registered_course_id,
                rc.registration_status,
                e.enrollment_id,
                e.enrollment_status,
                c.course_code,
                c.course_title,
                c.credit_hours,
                sec.section_name,
                sem.semester_no,
                f.teacher_id,
                fu.first_name,
                fu.last_name
            ORDER BY c.course_code
        """, (student["student_id"], current_session["session_id"]))
        courses = cursor.fetchall()
        total_courses = len(courses)

        cursor.execute("""
            SELECT COUNT(DISTINCT a.assessment_id) AS total_open_portals
            FROM enrollment e
            JOIN registered_course rc ON e.enrollment_id = rc.enrollment_id
            JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
            JOIN assessment a
                 ON a.teacher_assignment_id = ta.teacher_assignment_id
                AND a.session_id = e.session_id
            WHERE e.student_id = %s
              AND e.session_id = %s
              AND e.enrollment_status = 'Currently enrolled'
              AND a.portal_status = 'Open'
        """, (student["student_id"], current_session["session_id"]))
        total_open_portals = cursor.fetchone()["total_open_portals"]

        cursor.execute("""
            SELECT COUNT(DISTINCT sub.submission_id) AS total_submissions
            FROM enrollment e
            JOIN registered_course rc ON e.enrollment_id = rc.enrollment_id
            JOIN submission sub ON rc.registered_course_id = sub.registered_course_id
            JOIN assessment a ON sub.assessment_id = a.assessment_id
            WHERE e.student_id = %s
              AND e.session_id = %s
              AND a.session_id = e.session_id
        """, (student["student_id"], current_session["session_id"]))
        total_submissions = cursor.fetchone()["total_submissions"]

        cursor.execute("""
            SELECT COUNT(DISTINCT ev.evaluation_id) AS total_evaluated
            FROM enrollment e
            JOIN registered_course rc ON e.enrollment_id = rc.enrollment_id
            JOIN submission sub ON rc.registered_course_id = sub.registered_course_id
            JOIN assessment a ON sub.assessment_id = a.assessment_id
            JOIN evaluation ev ON sub.submission_id = ev.submission_id
            WHERE e.student_id = %s
              AND e.session_id = %s
              AND a.session_id = e.session_id
        """, (student["student_id"], current_session["session_id"]))
        total_evaluated = cursor.fetchone()["total_evaluated"]

    cursor.close()
    connection.close()

    return render_template(
        "student_dashboard.html",
        student=student,
        current_session=current_session,
        courses=courses,
        total_courses=total_courses,
        total_open_portals=total_open_portals,
        total_submissions=total_submissions,
        total_evaluated=total_evaluated
    )


@student_bp.route("/student/courses/<int:registered_course_id>")
def student_course_detail(registered_course_id):
    if not student_required():
        return redirect(url_for("auth.student_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    student = get_logged_in_student(cursor)

    if not student:
        cursor.close()
        connection.close()
        flash("Student profile not found.", "danger")
        return redirect(url_for("auth.student_login"))

    current_session = get_current_session(cursor)

    if not current_session:
        cursor.close()
        connection.close()
        flash("No active academic session found.", "warning")
        return redirect(url_for("student.student_dashboard"))

    cursor.execute("""
        SELECT
            rc.registered_course_id,
            rc.registration_status,
            e.enrollment_id,
            e.session_id,
            c.course_code,
            c.course_title,
            c.credit_hours,
            sec.section_name,
            sem.semester_no,
            fu.first_name AS faculty_first_name,
            fu.last_name AS faculty_last_name
        FROM registered_course rc
        JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
        JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
        JOIN course c ON ta.course_id = c.course_id
        JOIN section sec ON ta.section_id = sec.section_id
        JOIN semester sem ON ta.semester_id = sem.semester_id
        JOIN faculty f ON ta.teacher_id = f.teacher_id
        JOIN users fu ON f.user_id = fu.user_id
        WHERE rc.registered_course_id = %s
          AND e.student_id = %s
          AND e.session_id = %s
          AND e.enrollment_status = 'Currently enrolled'
    """, (registered_course_id, student["student_id"], current_session["session_id"]))
    course = cursor.fetchone()

    if not course:
        cursor.close()
        connection.close()
        flash("Course not found in your current session.", "danger")
        return redirect(url_for("student.student_dashboard"))

    cursor.execute("""
        SELECT
            a.assessment_id,
            a.title,
            a.description,
            a.assessment_type,
            a.total_marks,
            a.created_at,
            a.deadline,
            a.portal_status,
            sub.submission_id,
            sub.file_name,
            sub.file_path,
            sub.upload_time,
            sub.submission_status,
            ev.evaluation_id,
            ev.obtained_marks,
            ev.percentage,
            ev.evaluation_status,
            ev.feedback,
            ev.student_report_path,
            ev.student_report_status
        FROM registered_course rc
        JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
        JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
        JOIN assessment a
             ON a.teacher_assignment_id = ta.teacher_assignment_id
            AND a.session_id = e.session_id
        LEFT JOIN submission sub
               ON sub.assessment_id = a.assessment_id
              AND sub.registered_course_id = rc.registered_course_id
        LEFT JOIN evaluation ev ON sub.submission_id = ev.submission_id
        WHERE rc.registered_course_id = %s
          AND e.student_id = %s
          AND e.session_id = %s
        ORDER BY a.created_at DESC
    """, (registered_course_id, student["student_id"], current_session["session_id"]))
    assessments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_course_detail.html",
        student=student,
        current_session=current_session,
        course=course,
        assessments=assessments
    )


@student_bp.route("/student/assessments/<int:assessment_id>/upload", methods=["GET", "POST"])
def upload_submission(assessment_id):
    if not student_required():
        return redirect(url_for("auth.student_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    student = get_logged_in_student(cursor)

    if not student:
        cursor.close()
        connection.close()
        flash("Student profile not found.", "danger")
        return redirect(url_for("auth.student_login"))

    current_session = get_current_session(cursor)

    if not current_session:
        cursor.close()
        connection.close()
        flash("No active academic session found.", "warning")
        return redirect(url_for("student.student_dashboard"))

    cursor.execute("""
        SELECT
            a.assessment_id,
            a.title,
            a.description,
            a.assessment_type,
            a.total_marks,
            a.deadline,
            a.portal_status,
            rc.registered_course_id,
            c.course_code,
            c.course_title
        FROM assessment a
        JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
        JOIN registered_course rc ON rc.teacher_assignment_id = ta.teacher_assignment_id
        JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
        JOIN course c ON ta.course_id = c.course_id
        WHERE a.assessment_id = %s
          AND e.student_id = %s
          AND e.session_id = %s
          AND a.session_id = e.session_id
          AND e.enrollment_status = 'Currently enrolled'
    """, (assessment_id, student["student_id"], current_session["session_id"]))
    assessment = cursor.fetchone()

    if not assessment:
        cursor.close()
        connection.close()
        flash("Assessment not found for your current enrolled courses.", "danger")
        return redirect(url_for("student.student_dashboard"))

    registered_course_id = assessment["registered_course_id"]

    if assessment["portal_status"] != "Open":
        cursor.close()
        connection.close()
        flash("This portal is closed. You cannot upload submission now.", "warning")
        return redirect(url_for("student.student_course_detail", registered_course_id=registered_course_id))

    cursor.execute("""
        SELECT
            submission_id,
            file_name,
            file_path,
            upload_time,
            submission_status
        FROM submission
        WHERE assessment_id = %s
          AND registered_course_id = %s
    """, (assessment_id, registered_course_id))
    existing_submission = cursor.fetchone()

    if request.method == "POST":
        uploaded_file = request.files.get("submission_file")

        if not uploaded_file or uploaded_file.filename.strip() == "":
            flash("Please select a PDF file.", "warning")
            cursor.close()
            connection.close()
            return redirect(url_for("student.upload_submission", assessment_id=assessment_id))

        if not uploaded_file.filename.lower().endswith(".pdf"):
            flash("Only PDF files are allowed.", "danger")
            cursor.close()
            connection.close()
            return redirect(url_for("student.upload_submission", assessment_id=assessment_id))

        try:
            cursor.execute("""
                INSERT INTO submission
                (assessment_id, registered_course_id, file_name, file_path, upload_time, submission_status)
                VALUES (%s, %s, 'dummy_student_submission.pdf', %s, NOW(), 'Submitted')
                ON DUPLICATE KEY UPDATE
                    file_name = 'dummy_student_submission.pdf',
                    file_path = VALUES(file_path),
                    upload_time = NOW(),
                    submission_status = 'Submitted'
            """, (
                assessment_id,
                registered_course_id,
                DUMMY_SUBMISSION_PATH
            ))

            connection.commit()

            if existing_submission:
                flash("Submission updated successfully.", "success")
            else:
                flash("Submission uploaded successfully.", "success")

            cursor.close()
            connection.close()

            return redirect(url_for("student.student_course_detail", registered_course_id=registered_course_id))

        except Exception as error:
            connection.rollback()
            flash(f"Error uploading submission: {error}", "danger")

    cursor.close()
    connection.close()

    return render_template(
        "student_upload_submission.html",
        student=student,
        current_session=current_session,
        assessment=assessment,
        existing_submission=existing_submission
    )


@student_bp.route("/student/files/submission/<int:submission_id>")
def view_my_submission(submission_id):
    if not student_required():
        return redirect(url_for("auth.student_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    student = get_logged_in_student(cursor)

    if not student:
        cursor.close()
        connection.close()
        abort(404)

    cursor.execute("""
        SELECT
            sub.file_path
        FROM submission sub
        JOIN registered_course rc ON sub.registered_course_id = rc.registered_course_id
        JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
        WHERE sub.submission_id = %s
          AND e.student_id = %s
    """, (submission_id, student["student_id"]))
    file_data = cursor.fetchone()

    cursor.close()
    connection.close()

    if not file_data:
        abort(404)

    final_path = resolve_pdf_path(file_data["file_path"], DUMMY_SUBMISSION_PATH)

    if not final_path:
        abort(404)

    return send_file(final_path, as_attachment=False)


@student_bp.route("/student/files/report/<int:evaluation_id>")
def view_my_report(evaluation_id):
    if not student_required():
        return redirect(url_for("auth.student_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    student = get_logged_in_student(cursor)

    if not student:
        cursor.close()
        connection.close()
        abort(404)

    cursor.execute("""
        SELECT
            ev.student_report_path
        FROM evaluation ev
        JOIN submission sub ON ev.submission_id = sub.submission_id
        JOIN assessment a ON sub.assessment_id = a.assessment_id
        JOIN registered_course rc ON sub.registered_course_id = rc.registered_course_id
        JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
        WHERE ev.evaluation_id = %s
          AND e.student_id = %s
          AND a.portal_status = 'Closed'
    """, (evaluation_id, student["student_id"]))
    file_data = cursor.fetchone()

    cursor.close()
    connection.close()

    if not file_data:
        abort(404)

    final_path = resolve_pdf_path(file_data["student_report_path"], DUMMY_STUDENT_REPORT_PATH)

    if not final_path:
        abort(404)

    return send_file(final_path, as_attachment=False)