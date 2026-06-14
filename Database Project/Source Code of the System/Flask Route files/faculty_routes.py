from flask import Blueprint, render_template, redirect, url_for, session, request, flash, send_file, abort
from db import get_db_connection
import random
import os

faculty_bp = Blueprint("faculty", __name__)

BASE_PROJECT_PATH = r"C:\Users\admin\Desktop\Fair and Un biased System"

DUMMY_CLASS_REPORT_PATH = os.path.join(BASE_PROJECT_PATH, "dummy_class_assessment_report.pdf")
DUMMY_SUBMISSION_PATH = os.path.join(BASE_PROJECT_PATH, "dummy_student_submission.pdf")
DUMMY_STUDENT_REPORT_PATH = os.path.join(BASE_PROJECT_PATH, "dummy_student_evaluation_report.pdf")


def faculty_required():
    return "user_id" in session and session.get("role") == "Faculty"


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


def get_logged_in_faculty(cursor):
    cursor.execute("""
        SELECT
            f.teacher_id,
            f.designation,
            f.department_id,
            u.user_id,
            u.first_name,
            u.last_name,
            u.email,
            d.department_name
        FROM faculty f
        JOIN users u ON f.user_id = u.user_id
        JOIN department d ON f.department_id = d.department_id
        WHERE f.user_id = %s
    """, (session["user_id"],))

    return cursor.fetchone()


def get_faculty_sessions_and_selected(cursor, teacher_id):
    current_session = get_current_session(cursor)

    cursor.execute("""
        SELECT DISTINCT
            acs.session_id,
            acs.session_name,
            acs.academic_year,
            acs.start_date,
            acs.end_date
        FROM academic_session acs
        JOIN enrollment e ON acs.session_id = e.session_id
        JOIN registered_course rc ON e.enrollment_id = rc.enrollment_id
        JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
        WHERE ta.teacher_id = %s
        ORDER BY acs.start_date DESC
    """, (teacher_id,))

    sessions = cursor.fetchall()

    selected_session_id = request.args.get("session_id")

    if not selected_session_id:
        if current_session:
            current_id = str(current_session["session_id"])
            available_ids = [str(s["session_id"]) for s in sessions]

            if current_id in available_ids:
                selected_session_id = current_id
            elif sessions:
                selected_session_id = str(sessions[0]["session_id"])
        elif sessions:
            selected_session_id = str(sessions[0]["session_id"])

    current_session_id = str(current_session["session_id"]) if current_session else None
    is_current_session = selected_session_id == current_session_id

    return sessions, selected_session_id, current_session, is_current_session


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


@faculty_bp.route("/faculty/dashboard")
def faculty_dashboard():
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    if not faculty:
        cursor.close()
        connection.close()
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.faculty_login"))

    sessions, selected_session_id, current_session, is_current_session = get_faculty_sessions_and_selected(
        cursor,
        faculty["teacher_id"]
    )

    total_courses = 0
    total_assessments = 0
    pending_evaluations = 0
    assigned_courses = []
    recent_assessments = []

    if selected_session_id:
        cursor.execute("""
            SELECT COUNT(DISTINCT ta.teacher_assignment_id) AS total_courses
            FROM teacher_assignment ta
            JOIN registered_course rc ON ta.teacher_assignment_id = rc.teacher_assignment_id
            JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
            WHERE ta.teacher_id = %s
              AND e.session_id = %s
        """, (faculty["teacher_id"], selected_session_id))
        total_courses = cursor.fetchone()["total_courses"]

        cursor.execute("""
            SELECT COUNT(DISTINCT a.assessment_id) AS total_assessments
            FROM assessment a
            JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
            WHERE ta.teacher_id = %s
              AND a.session_id = %s
        """, (faculty["teacher_id"], selected_session_id))
        total_assessments = cursor.fetchone()["total_assessments"]

        cursor.execute("""
            SELECT COUNT(DISTINCT sub.submission_id) AS pending_evaluations
            FROM submission sub
            JOIN assessment a ON sub.assessment_id = a.assessment_id
            JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
            JOIN registered_course rc ON sub.registered_course_id = rc.registered_course_id
            JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
            LEFT JOIN evaluation ev ON sub.submission_id = ev.submission_id
            WHERE ta.teacher_id = %s
              AND e.session_id = %s
              AND a.session_id = e.session_id
              AND ev.evaluation_id IS NULL
        """, (faculty["teacher_id"], selected_session_id))
        pending_evaluations = cursor.fetchone()["pending_evaluations"]

        cursor.execute("""
            SELECT
                ta.teacher_assignment_id,
                c.course_code,
                c.course_title,
                sec.section_name,
                sem.semester_no,
                b.batch_name,
                p.program_name,
                d.department_name,
                ta.assigned_date,
                COUNT(DISTINCT e.enrollment_id) AS enrolled_students
            FROM teacher_assignment ta
            JOIN course c ON ta.course_id = c.course_id
            JOIN semester sem ON ta.semester_id = sem.semester_id
            JOIN section sec ON ta.section_id = sec.section_id
            JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
            JOIN batch b ON bp.batch_id = b.batch_id
            JOIN program p ON bp.program_id = p.program_id
            JOIN department d ON p.department_id = d.department_id
            JOIN registered_course rc ON rc.teacher_assignment_id = ta.teacher_assignment_id
            JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
            WHERE ta.teacher_id = %s
              AND e.session_id = %s
            GROUP BY
                ta.teacher_assignment_id,
                c.course_code,
                c.course_title,
                sec.section_name,
                sem.semester_no,
                b.batch_name,
                p.program_name,
                d.department_name,
                ta.assigned_date
            ORDER BY c.course_code
            LIMIT 6
        """, (faculty["teacher_id"], selected_session_id))
        assigned_courses = cursor.fetchall()

        cursor.execute("""
            SELECT
                a.assessment_id,
                a.title,
                a.assessment_type,
                a.total_marks,
                a.deadline,
                a.portal_status,
                c.course_code,
                c.course_title
            FROM assessment a
            JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
            JOIN course c ON ta.course_id = c.course_id
            WHERE ta.teacher_id = %s
              AND a.session_id = %s
            ORDER BY a.created_at DESC
            LIMIT 5
        """, (faculty["teacher_id"], selected_session_id))
        recent_assessments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "faculty.html",
        faculty=faculty,
        sessions=sessions,
        selected_session_id=selected_session_id,
        current_session=current_session,
        latest_session_id=str(current_session["session_id"]) if current_session else None,
        is_current_session=is_current_session,
        total_courses=total_courses,
        total_assessments=total_assessments,
        pending_evaluations=pending_evaluations,
        assigned_courses=assigned_courses,
        recent_assessments=recent_assessments
    )


@faculty_bp.route("/faculty/courses")
def faculty_courses():
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    if not faculty:
        cursor.close()
        connection.close()
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.faculty_login"))

    sessions, selected_session_id, current_session, is_current_session = get_faculty_sessions_and_selected(
        cursor,
        faculty["teacher_id"]
    )

    courses = []

    if selected_session_id:
        cursor.execute("""
            SELECT
                ta.teacher_assignment_id,
                c.course_code,
                c.course_title,
                c.credit_hours,
                sec.section_name,
                sem.semester_no,
                b.batch_name,
                p.program_name,
                d.department_name,
                ta.assigned_date,
                COUNT(DISTINCT e.enrollment_id) AS enrolled_students
            FROM teacher_assignment ta
            JOIN course c ON ta.course_id = c.course_id
            JOIN semester sem ON ta.semester_id = sem.semester_id
            JOIN section sec ON ta.section_id = sec.section_id
            JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
            JOIN batch b ON bp.batch_id = b.batch_id
            JOIN program p ON bp.program_id = p.program_id
            JOIN department d ON p.department_id = d.department_id
            JOIN registered_course rc ON rc.teacher_assignment_id = ta.teacher_assignment_id
            JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
            WHERE ta.teacher_id = %s
              AND e.session_id = %s
            GROUP BY
                ta.teacher_assignment_id,
                c.course_code,
                c.course_title,
                c.credit_hours,
                sec.section_name,
                sem.semester_no,
                b.batch_name,
                p.program_name,
                d.department_name,
                ta.assigned_date
            ORDER BY c.course_code
        """, (faculty["teacher_id"], selected_session_id))
        courses = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "faculty_courses.html",
        faculty=faculty,
        courses=courses,
        sessions=sessions,
        selected_session_id=selected_session_id,
        current_session=current_session,
        latest_session_id=str(current_session["session_id"]) if current_session else None,
        is_current_session=is_current_session
    )


@faculty_bp.route("/faculty/courses/<int:teacher_assignment_id>")
def faculty_course_detail(teacher_assignment_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    if not faculty:
        cursor.close()
        connection.close()
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.faculty_login"))

    sessions, selected_session_id, current_session, is_current_session = get_faculty_sessions_and_selected(
        cursor,
        faculty["teacher_id"]
    )

    cursor.execute("""
        SELECT
            ta.teacher_assignment_id,
            c.course_id,
            c.course_code,
            c.course_title,
            c.credit_hours,
            sec.section_name,
            sem.semester_no,
            b.batch_name,
            p.program_name,
            d.department_name,
            ta.assigned_date
        FROM teacher_assignment ta
        JOIN course c ON ta.course_id = c.course_id
        JOIN semester sem ON ta.semester_id = sem.semester_id
        JOIN section sec ON ta.section_id = sec.section_id
        JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        JOIN department d ON p.department_id = d.department_id
        WHERE ta.teacher_assignment_id = %s
          AND ta.teacher_id = %s
    """, (teacher_assignment_id, faculty["teacher_id"]))
    course = cursor.fetchone()

    if not course:
        cursor.close()
        connection.close()
        flash("Course assignment not found.", "danger")
        return redirect(url_for("faculty.faculty_courses", session_id=selected_session_id))

    cursor.execute("""
        SELECT COUNT(DISTINCT e.enrollment_id) AS enrolled_students
        FROM enrollment e
        JOIN registered_course rc ON e.enrollment_id = rc.enrollment_id
        WHERE rc.teacher_assignment_id = %s
          AND e.session_id = %s
    """, (teacher_assignment_id, selected_session_id))
    enrolled_students = cursor.fetchone()["enrolled_students"]

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
            a.class_report_status,
            a.class_report_path,
            COUNT(DISTINCT sub.submission_id) AS total_submissions,
            COUNT(DISTINCT ev.evaluation_id) AS evaluated_submissions
        FROM assessment a
        LEFT JOIN submission sub
               ON a.assessment_id = sub.assessment_id
        LEFT JOIN registered_course rc
               ON sub.registered_course_id = rc.registered_course_id
        LEFT JOIN enrollment e
               ON rc.enrollment_id = e.enrollment_id
              AND e.session_id = a.session_id
        LEFT JOIN evaluation ev
               ON sub.submission_id = ev.submission_id
        WHERE a.teacher_assignment_id = %s
          AND a.session_id = %s
        GROUP BY
            a.assessment_id,
            a.title,
            a.description,
            a.assessment_type,
            a.total_marks,
            a.created_at,
            a.deadline,
            a.portal_status,
            a.class_report_status,
            a.class_report_path
        ORDER BY a.created_at DESC
    """, (teacher_assignment_id, selected_session_id))
    assessments = cursor.fetchall()

    cursor.execute("""
        SELECT
            s.registration_no,
            u.first_name,
            u.last_name,
            u.email,
            e.enrollment_status
        FROM enrollment e
        JOIN registered_course rc ON e.enrollment_id = rc.enrollment_id
        JOIN student s ON e.student_id = s.student_id
        JOIN users u ON s.user_id = u.user_id
        WHERE rc.teacher_assignment_id = %s
          AND e.session_id = %s
        ORDER BY s.registration_no
    """, (teacher_assignment_id, selected_session_id))
    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "faculty_course_detail.html",
        faculty=faculty,
        course=course,
        sessions=sessions,
        selected_session_id=selected_session_id,
        current_session=current_session,
        latest_session_id=str(current_session["session_id"]) if current_session else None,
        is_current_session=is_current_session,
        enrolled_students=enrolled_students,
        assessments=assessments,
        students=students
    )


@faculty_bp.route("/faculty/courses/<int:teacher_assignment_id>/assessments/add", methods=["GET", "POST"])
def create_assessment(teacher_assignment_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    if not faculty:
        cursor.close()
        connection.close()
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.faculty_login"))

    sessions, selected_session_id, current_session, is_current_session = get_faculty_sessions_and_selected(
        cursor,
        faculty["teacher_id"]
    )

    if not is_current_session:
        cursor.close()
        connection.close()
        flash("You can create assessments only for the current session.", "warning")
        return redirect(url_for("faculty.faculty_course_detail", teacher_assignment_id=teacher_assignment_id, session_id=selected_session_id))

    cursor.execute("""
        SELECT
            ta.teacher_assignment_id,
            c.course_code,
            c.course_title,
            sec.section_name,
            sem.semester_no,
            b.batch_name,
            p.program_name
        FROM teacher_assignment ta
        JOIN course c ON ta.course_id = c.course_id
        JOIN semester sem ON ta.semester_id = sem.semester_id
        JOIN section sec ON ta.section_id = sec.section_id
        JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
        JOIN batch b ON bp.batch_id = b.batch_id
        JOIN program p ON bp.program_id = p.program_id
        WHERE ta.teacher_assignment_id = %s
          AND ta.teacher_id = %s
    """, (teacher_assignment_id, faculty["teacher_id"]))
    course = cursor.fetchone()

    if not course:
        cursor.close()
        connection.close()
        flash("Course assignment not found.", "danger")
        return redirect(url_for("faculty.faculty_courses", session_id=selected_session_id))

    cursor.execute("""
        SELECT COUNT(*) AS enrolled_students
        FROM registered_course rc
        JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
        WHERE rc.teacher_assignment_id = %s
          AND e.session_id = %s
          AND e.enrollment_status = 'Currently enrolled'
    """, (teacher_assignment_id, selected_session_id))
    enrolled_students = cursor.fetchone()["enrolled_students"]

    if enrolled_students == 0:
        cursor.close()
        connection.close()
        flash("Cannot create assessment because no students are enrolled in this course for this session.", "warning")
        return redirect(url_for("faculty.faculty_course_detail", teacher_assignment_id=teacher_assignment_id, session_id=selected_session_id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        assessment_type = request.form.get("assessment_type", "").strip()
        total_marks = request.form.get("total_marks", "").strip()
        deadline = request.form.get("deadline", "").strip()

        if not title:
            flash("Assessment title is required.", "warning")
        elif not assessment_type:
            flash("Assessment type is required.", "warning")
        elif not deadline:
            flash("Deadline is required.", "warning")
        else:
            try:
                total_marks_value = float(total_marks)

                if total_marks_value <= 0:
                    flash("Total marks must be greater than zero.", "warning")
                else:
                    cursor.execute("""
                        INSERT INTO assessment
                        (teacher_assignment_id, session_id, title, description, assessment_type,
                         total_marks, created_at, deadline, portal_status,
                         class_report_path, class_report_generated_at, class_report_status)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, 'Open', NULL, NULL, 'Not Generated')
                    """, (
                        teacher_assignment_id,
                        selected_session_id,
                        title,
                        description,
                        assessment_type,
                        total_marks_value,
                        deadline
                    ))

                    connection.commit()
                    flash("Assessment created successfully.", "success")
                    return redirect(url_for("faculty.faculty_course_detail", teacher_assignment_id=teacher_assignment_id, session_id=selected_session_id))

            except ValueError:
                flash("Total marks must be a valid number.", "danger")
            except Exception as error:
                connection.rollback()
                flash(f"Error creating assessment: {error}", "danger")

    cursor.close()
    connection.close()

    return render_template(
        "faculty_assessment_add.html",
        faculty=faculty,
        course=course,
        selected_session_id=selected_session_id
    )


@faculty_bp.route("/faculty/assessments/<int:assessment_id>/toggle-portal", methods=["POST"])
def toggle_assessment_portal(assessment_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    selected_session_id = request.form.get("session_id")
    action = request.form.get("action")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    if not faculty:
        cursor.close()
        connection.close()
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.faculty_login"))

    sessions, selected_session_id_from_helper, current_session, is_current_session = get_faculty_sessions_and_selected(
        cursor,
        faculty["teacher_id"]
    )

    if not is_current_session:
        cursor.close()
        connection.close()
        flash("Portal can be opened or closed only for the current session.", "warning")
        return redirect(url_for("faculty.faculty_dashboard", session_id=selected_session_id))

    cursor.execute("""
        SELECT
            a.assessment_id,
            a.teacher_assignment_id,
            a.portal_status,
            ta.teacher_id
        FROM assessment a
        JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
        WHERE a.assessment_id = %s
          AND ta.teacher_id = %s
          AND a.session_id = %s
    """, (assessment_id, faculty["teacher_id"], selected_session_id))
    assessment = cursor.fetchone()

    if not assessment:
        cursor.close()
        connection.close()
        flash("Assessment not found.", "danger")
        return redirect(url_for("faculty.faculty_dashboard", session_id=selected_session_id))

    try:
        if action == "close":
            cursor.execute("""
                UPDATE assessment
                SET portal_status = 'Closed',
                    class_report_path = %s,
                    class_report_generated_at = NOW(),
                    class_report_status = 'Generated'
                WHERE assessment_id = %s
            """, (DUMMY_CLASS_REPORT_PATH, assessment_id))
            flash("Portal closed successfully.", "success")

        elif action == "open":
            cursor.execute("""
                UPDATE assessment
                SET portal_status = 'Open'
                WHERE assessment_id = %s
            """, (assessment_id,))
            flash("Portal opened successfully.", "success")

        else:
            flash("Invalid portal action.", "danger")

        connection.commit()

    except Exception as error:
        connection.rollback()
        flash(f"Error updating portal: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for(
        "faculty.faculty_course_detail",
        teacher_assignment_id=assessment["teacher_assignment_id"],
        session_id=selected_session_id
    ))


@faculty_bp.route("/faculty/assessments/<int:assessment_id>/submissions")
def assessment_submissions(assessment_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    if not faculty:
        cursor.close()
        connection.close()
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.faculty_login"))

    sessions, selected_session_id, current_session, is_current_session = get_faculty_sessions_and_selected(
        cursor,
        faculty["teacher_id"]
    )

    cursor.execute("""
        SELECT
            a.assessment_id,
            a.title,
            a.description,
            a.assessment_type,
            a.total_marks,
            a.deadline,
            a.portal_status,
            a.class_report_path,
            a.class_report_status,
            ta.teacher_assignment_id,
            c.course_code,
            c.course_title
        FROM assessment a
        JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
        JOIN course c ON ta.course_id = c.course_id
        WHERE a.assessment_id = %s
          AND ta.teacher_id = %s
          AND a.session_id = %s
    """, (assessment_id, faculty["teacher_id"], selected_session_id))
    assessment = cursor.fetchone()

    if not assessment:
        cursor.close()
        connection.close()
        flash("Assessment not found for selected session.", "danger")
        return redirect(url_for("faculty.faculty_dashboard", session_id=selected_session_id))

    cursor.execute("""
        SELECT
            rc.registered_course_id,
            e.enrollment_id,
            s.student_id,
            s.registration_no,
            u.first_name,
            u.last_name,
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
        JOIN student s ON e.student_id = s.student_id
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN submission sub
               ON sub.registered_course_id = rc.registered_course_id
              AND sub.assessment_id = %s
        LEFT JOIN evaluation ev ON sub.submission_id = ev.submission_id
        WHERE rc.teacher_assignment_id = %s
          AND e.session_id = %s
        ORDER BY s.registration_no
    """, (assessment_id, assessment["teacher_assignment_id"], selected_session_id))
    submissions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "faculty_submissions.html",
        faculty=faculty,
        assessment=assessment,
        submissions=submissions,
        sessions=sessions,
        selected_session_id=selected_session_id,
        current_session=current_session,
        latest_session_id=str(current_session["session_id"]) if current_session else None,
        is_current_session=is_current_session
    )


@faculty_bp.route("/faculty/assessments/<int:assessment_id>/ai-check", methods=["POST"])
def ai_check_assessment(assessment_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    selected_session_id = request.form.get("session_id")
    selected_submission_ids = request.form.getlist("submission_ids")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    if not faculty:
        cursor.close()
        connection.close()
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.faculty_login"))

    cursor.execute("""
        SELECT
            a.assessment_id,
            a.total_marks,
            a.portal_status,
            ta.teacher_assignment_id
        FROM assessment a
        JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
        WHERE a.assessment_id = %s
          AND ta.teacher_id = %s
          AND a.session_id = %s
    """, (assessment_id, faculty["teacher_id"], selected_session_id))
    assessment = cursor.fetchone()

    if not assessment:
        cursor.close()
        connection.close()
        flash("Assessment not found.", "danger")
        return redirect(url_for("faculty.faculty_dashboard", session_id=selected_session_id))

    if not selected_submission_ids:
        cursor.close()
        connection.close()
        flash("Please select submitted students first.", "warning")
        return redirect(url_for("faculty.assessment_submissions", assessment_id=assessment_id, session_id=selected_session_id))

    try:
        total_marks = float(assessment["total_marks"])

        for submission_id in selected_submission_ids:
            cursor.execute("""
                SELECT
                    sub.submission_id
                FROM submission sub
                JOIN registered_course rc ON sub.registered_course_id = rc.registered_course_id
                JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
                WHERE sub.submission_id = %s
                  AND sub.assessment_id = %s
                  AND e.session_id = %s
            """, (submission_id, assessment_id, selected_session_id))
            valid_submission = cursor.fetchone()

            if valid_submission:
                obtained_marks = round(random.uniform(total_marks * 0.55, total_marks * 0.95), 2)
                percentage = round((obtained_marks / total_marks) * 100, 2)

                cursor.execute("""
                    UPDATE submission
                    SET file_name = 'dummy_student_submission.pdf',
                        file_path = %s,
                        submission_status = 'Submitted'
                    WHERE submission_id = %s
                """, (DUMMY_SUBMISSION_PATH, submission_id))

                cursor.execute("""
                    INSERT INTO evaluation
                    (submission_id, obtained_marks, percentage, evaluated_at,
                     evaluation_status, feedback,
                     student_report_path, student_report_generated_at, student_report_status)
                    VALUES (%s, %s, %s, NOW(), 'Evaluated',
                            'AI-based dummy evaluation completed successfully.',
                            %s, NOW(), 'Generated')
                    ON DUPLICATE KEY UPDATE
                        obtained_marks = VALUES(obtained_marks),
                        percentage = VALUES(percentage),
                        evaluated_at = NOW(),
                        evaluation_status = 'Evaluated',
                        feedback = VALUES(feedback),
                        student_report_path = VALUES(student_report_path),
                        student_report_generated_at = NOW(),
                        student_report_status = 'Generated'
                """, (
                    submission_id,
                    obtained_marks,
                    percentage,
                    DUMMY_STUDENT_REPORT_PATH
                ))

        connection.commit()
        flash("AI checking completed and marks updated successfully.", "success")

    except Exception as error:
        connection.rollback()
        flash(f"Error during AI checking: {error}", "danger")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("faculty.assessment_submissions", assessment_id=assessment_id, session_id=selected_session_id))


@faculty_bp.route("/faculty/files/submission/<int:submission_id>")
def view_submission_file(submission_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    cursor.execute("""
        SELECT
            sub.file_path
        FROM submission sub
        JOIN assessment a ON sub.assessment_id = a.assessment_id
        JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
        WHERE sub.submission_id = %s
          AND ta.teacher_id = %s
    """, (submission_id, faculty["teacher_id"]))
    file_data = cursor.fetchone()

    cursor.close()
    connection.close()

    if not file_data:
        abort(404)

    final_path = resolve_pdf_path(file_data["file_path"], DUMMY_SUBMISSION_PATH)

    if not final_path:
        abort(404)

    return send_file(final_path, as_attachment=False)


@faculty_bp.route("/faculty/files/student-report/<int:evaluation_id>")
def view_student_report(evaluation_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    cursor.execute("""
        SELECT
            ev.student_report_path
        FROM evaluation ev
        JOIN submission sub ON ev.submission_id = sub.submission_id
        JOIN assessment a ON sub.assessment_id = a.assessment_id
        JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
        WHERE ev.evaluation_id = %s
          AND ta.teacher_id = %s
    """, (evaluation_id, faculty["teacher_id"]))
    file_data = cursor.fetchone()

    cursor.close()
    connection.close()

    if not file_data:
        abort(404)

    final_path = resolve_pdf_path(file_data["student_report_path"], DUMMY_STUDENT_REPORT_PATH)

    if not final_path:
        abort(404)

    return send_file(final_path, as_attachment=False)


@faculty_bp.route("/faculty/files/class-report/<int:assessment_id>")
def view_class_report(assessment_id):
    if not faculty_required():
        return redirect(url_for("auth.faculty_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    faculty = get_logged_in_faculty(cursor)

    cursor.execute("""
        SELECT
            a.class_report_path
        FROM assessment a
        JOIN teacher_assignment ta ON a.teacher_assignment_id = ta.teacher_assignment_id
        WHERE a.assessment_id = %s
          AND ta.teacher_id = %s
          AND a.portal_status = 'Closed'
    """, (assessment_id, faculty["teacher_id"]))
    file_data = cursor.fetchone()

    cursor.close()
    connection.close()

    if not file_data:
        abort(404)

    final_path = resolve_pdf_path(file_data["class_report_path"], DUMMY_CLASS_REPORT_PATH)

    if not final_path:
        abort(404)

    return send_file(final_path, as_attachment=False)