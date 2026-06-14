USE fair_assessment_system;

DROP VIEW IF EXISTS v_admin_dashboard_counts;
DROP VIEW IF EXISTS v_recent_enrollments;
DROP VIEW IF EXISTS v_recent_teacher_assignments;
DROP VIEW IF EXISTS v_admin_students;
DROP VIEW IF EXISTS v_admin_faculty;
DROP VIEW IF EXISTS v_admin_courses;
DROP VIEW IF EXISTS v_admin_teacher_assignments;
DROP VIEW IF EXISTS v_admin_enrollments;
DROP VIEW IF EXISTS v_admin_enrollment_registered_courses;

DROP FUNCTION IF EXISTS fn_email_exists;
DROP FUNCTION IF EXISTS fn_registration_exists;
DROP FUNCTION IF EXISTS fn_course_code_exists;
DROP FUNCTION IF EXISTS fn_section_available_seats;
DROP FUNCTION IF EXISTS fn_current_session_id;
DROP FUNCTION IF EXISTS fn_student_already_enrolled;

DROP PROCEDURE IF EXISTS sp_add_student;
DROP PROCEDURE IF EXISTS sp_update_student;
DROP PROCEDURE IF EXISTS sp_delete_student_safe;
DROP PROCEDURE IF EXISTS sp_add_faculty;
DROP PROCEDURE IF EXISTS sp_update_faculty;
DROP PROCEDURE IF EXISTS sp_delete_faculty_safe;
DROP PROCEDURE IF EXISTS sp_add_course;
DROP PROCEDURE IF EXISTS sp_delete_course_safe;
DROP PROCEDURE IF EXISTS sp_add_teacher_assignment;
DROP PROCEDURE IF EXISTS sp_delete_teacher_assignment_safe;
DROP PROCEDURE IF EXISTS sp_add_enrollment;
DROP PROCEDURE IF EXISTS sp_add_registered_course;

DROP TRIGGER IF EXISTS trg_prevent_submission_when_portal_closed;
DROP TRIGGER IF EXISTS trg_prevent_submission_update_when_portal_closed;
DROP TRIGGER IF EXISTS trg_calculate_evaluation_percentage_insert;
DROP TRIGGER IF EXISTS trg_calculate_evaluation_percentage_update;
DROP TRIGGER IF EXISTS trg_prevent_duplicate_active_enrollment;

CREATE VIEW v_admin_dashboard_counts AS
SELECT
    (SELECT COUNT(*) FROM student) AS total_students,
    (SELECT COUNT(*) FROM faculty) AS total_faculty,
    (SELECT COUNT(*) FROM course) AS total_courses,
    (SELECT COUNT(*) FROM enrollment) AS total_enrollments,
    (SELECT COUNT(*) FROM teacher_assignment) AS total_teacher_assignments,
    (SELECT COUNT(*) FROM users WHERE account_status = 'Active') AS active_users,
    (SELECT COUNT(*) FROM users WHERE account_status <> 'Active') AS inactive_users,
    (SELECT COUNT(*) FROM department) AS total_departments;

CREATE VIEW v_recent_enrollments AS
SELECT
    e.enrollment_id,
    s.registration_no,
    u.first_name,
    u.last_name,
    sec.section_name,
    sem.semester_no,
    acs.session_name,
    acs.academic_year,
    p.program_name,
    e.enrollment_status,
    e.enrollment_start_date
FROM enrollment e
JOIN student s ON e.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
JOIN section sec ON e.section_id = sec.section_id
JOIN semester sem ON e.semester_id = sem.semester_id
JOIN academic_session acs ON e.session_id = acs.session_id
JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
JOIN program p ON bp.program_id = p.program_id;

CREATE VIEW v_recent_teacher_assignments AS
SELECT
    ta.teacher_assignment_id,
    c.course_code,
    c.course_title,
    u.first_name,
    u.last_name,
    sec.section_name,
    sem.semester_no,
    ta.assigned_date
FROM teacher_assignment ta
JOIN course c ON ta.course_id = c.course_id
JOIN faculty f ON ta.teacher_id = f.teacher_id
JOIN users u ON f.user_id = u.user_id
JOIN section sec ON ta.section_id = sec.section_id
JOIN semester sem ON ta.semester_id = sem.semester_id;

CREATE VIEW v_admin_students AS
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
    d.department_id,
    d.department_name,
    p.program_id,
    p.program_name,
    p.program_code,
    b.batch_id,
    b.batch_name,
    bp.expected_graduation
FROM student s
JOIN users u ON s.user_id = u.user_id
JOIN batch_program bp ON s.batch_program_id = bp.batch_program_id
JOIN batch b ON bp.batch_id = b.batch_id
JOIN program p ON bp.program_id = p.program_id
JOIN department d ON p.department_id = d.department_id;

CREATE VIEW v_admin_faculty AS
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
JOIN department d ON f.department_id = d.department_id;

CREATE VIEW v_admin_courses AS
SELECT
    c.course_id,
    c.department_id,
    c.course_code,
    c.course_title,
    c.credit_hours,
    d.department_name,
    d.department_code
FROM course c
JOIN department d ON c.department_id = d.department_id;

CREATE VIEW v_admin_teacher_assignments AS
SELECT
    ta.teacher_assignment_id,
    ta.teacher_id,
    ta.course_id,
    ta.semester_id,
    ta.section_id,
    ta.assigned_date,
    u.first_name,
    u.last_name,
    f.designation,
    c.course_code,
    c.course_title,
    sem.semester_no,
    sec.section_name,
    b.batch_id,
    b.batch_name,
    p.program_id,
    p.program_name,
    d.department_id,
    d.department_name
FROM teacher_assignment ta
JOIN faculty f ON ta.teacher_id = f.teacher_id
JOIN users u ON f.user_id = u.user_id
JOIN course c ON ta.course_id = c.course_id
JOIN semester sem ON ta.semester_id = sem.semester_id
JOIN section sec ON ta.section_id = sec.section_id
JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
JOIN batch b ON bp.batch_id = b.batch_id
JOIN program p ON bp.program_id = p.program_id
JOIN department d ON p.department_id = d.department_id;

CREATE VIEW v_admin_enrollments AS
SELECT
    e.enrollment_id,
    e.student_id,
    e.section_id,
    e.session_id,
    e.semester_id,
    e.enrollment_status,
    e.is_repeat,
    e.enrollment_start_date,
    e.enrollment_end_date,
    s.registration_no,
    s.student_status,
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    u.gender,
    u.account_status,
    sec.section_name,
    sem.semester_no,
    acs.session_name,
    acs.academic_year,
    acs.start_date AS session_start_date,
    b.batch_id,
    b.batch_name,
    p.program_id,
    p.program_name,
    p.program_code,
    d.department_id,
    d.department_name,
    d.department_code
FROM enrollment e
JOIN student s ON e.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
JOIN section sec ON e.section_id = sec.section_id
JOIN semester sem ON e.semester_id = sem.semester_id
JOIN academic_session acs ON e.session_id = acs.session_id
JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
JOIN batch b ON bp.batch_id = b.batch_id
JOIN program p ON bp.program_id = p.program_id
JOIN department d ON p.department_id = d.department_id;

CREATE VIEW v_admin_enrollment_registered_courses AS
SELECT
    rc.registered_course_id,
    rc.enrollment_id,
    rc.teacher_assignment_id,
    rc.registration_status,
    c.course_code,
    c.course_title,
    c.credit_hours,
    u.first_name AS teacher_first_name,
    u.last_name AS teacher_last_name
FROM registered_course rc
JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
JOIN course c ON ta.course_id = c.course_id
JOIN faculty f ON ta.teacher_id = f.teacher_id
JOIN users u ON f.user_id = u.user_id;

DELIMITER $$

CREATE FUNCTION fn_email_exists(p_email VARCHAR(150), p_ignore_user_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_total INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_total
    FROM users
    WHERE email = p_email
      AND (p_ignore_user_id IS NULL OR user_id <> p_ignore_user_id);

    RETURN v_total;
END$$

CREATE FUNCTION fn_registration_exists(p_registration_no VARCHAR(50), p_ignore_student_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_total INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_total
    FROM student
    WHERE registration_no = p_registration_no
      AND (p_ignore_student_id IS NULL OR student_id <> p_ignore_student_id);

    RETURN v_total;
END$$

CREATE FUNCTION fn_course_code_exists(p_course_code VARCHAR(30), p_ignore_course_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_total INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_total
    FROM course
    WHERE course_code = p_course_code
      AND (p_ignore_course_id IS NULL OR course_id <> p_ignore_course_id);

    RETURN v_total;
END$$

CREATE FUNCTION fn_section_available_seats(p_section_id INT, p_session_id INT, p_semester_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_capacity INT DEFAULT 0;
    DECLARE v_used INT DEFAULT 0;

    SELECT capacity
    INTO v_capacity
    FROM section
    WHERE section_id = p_section_id;

    SELECT COUNT(*)
    INTO v_used
    FROM enrollment
    WHERE section_id = p_section_id
      AND session_id = p_session_id
      AND semester_id = p_semester_id
      AND enrollment_status = 'Currently enrolled';

    RETURN IFNULL(v_capacity, 0) - IFNULL(v_used, 0);
END$$

CREATE FUNCTION fn_current_session_id()
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_session_id INT DEFAULT NULL;

    SELECT session_id
    INTO v_session_id
    FROM academic_session
    WHERE CURDATE() BETWEEN start_date AND end_date
    ORDER BY start_date DESC
    LIMIT 1;

    IF v_session_id IS NULL THEN
        SELECT session_id
        INTO v_session_id
        FROM academic_session
        WHERE start_date <= CURDATE()
        ORDER BY start_date DESC
        LIMIT 1;
    END IF;

    RETURN v_session_id;
END$$

CREATE FUNCTION fn_student_already_enrolled(
    p_student_id INT,
    p_section_id INT,
    p_session_id INT,
    p_semester_id INT
)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_total INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_total
    FROM enrollment
    WHERE student_id = p_student_id
      AND section_id = p_section_id
      AND session_id = p_session_id
      AND semester_id = p_semester_id
      AND enrollment_status = 'Currently enrolled';

    RETURN v_total;
END$$

CREATE PROCEDURE sp_add_student(
    IN p_first_name VARCHAR(80),
    IN p_last_name VARCHAR(80),
    IN p_email VARCHAR(150),
    IN p_password_hash VARCHAR(255),
    IN p_gender VARCHAR(20),
    IN p_account_status VARCHAR(30),
    IN p_phone_no VARCHAR(30),
    IN p_batch_program_id INT,
    IN p_registration_no VARCHAR(50),
    IN p_student_status VARCHAR(30)
)
BEGIN
    DECLARE v_user_id INT;

    IF p_first_name = '' OR p_last_name = '' OR p_email = '' OR p_password_hash = '' OR p_registration_no = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Required student fields are missing.';
    END IF;

    IF fn_email_exists(p_email, NULL) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This email already exists.';
    END IF;

    IF fn_registration_exists(p_registration_no, NULL) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This registration number already exists.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM batch_program WHERE batch_program_id = p_batch_program_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid batch program selected.';
    END IF;

    INSERT INTO users
    (first_name, last_name, email, password_hash, role, gender, account_status, created_at)
    VALUES
    (p_first_name, p_last_name, p_email, p_password_hash, 'Student', p_gender, p_account_status, NOW());

    SET v_user_id = LAST_INSERT_ID();

    INSERT INTO student
    (user_id, batch_program_id, registration_no, student_status)
    VALUES
    (v_user_id, p_batch_program_id, p_registration_no, p_student_status);

    IF p_phone_no IS NOT NULL AND p_phone_no <> '' THEN
        INSERT INTO user_phone (user_id, phone_no)
        VALUES (v_user_id, p_phone_no);
    END IF;
END$$

CREATE PROCEDURE sp_update_student(
    IN p_student_id INT,
    IN p_first_name VARCHAR(80),
    IN p_last_name VARCHAR(80),
    IN p_email VARCHAR(150),
    IN p_password_hash VARCHAR(255),
    IN p_gender VARCHAR(20),
    IN p_account_status VARCHAR(30),
    IN p_phone_no VARCHAR(30),
    IN p_batch_program_id INT,
    IN p_registration_no VARCHAR(50),
    IN p_student_status VARCHAR(30)
)
BEGIN
    DECLARE v_user_id INT;

    SELECT user_id
    INTO v_user_id
    FROM student
    WHERE student_id = p_student_id;

    IF v_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student not found.';
    END IF;

    IF fn_email_exists(p_email, v_user_id) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This email is already used by another user.';
    END IF;

    IF fn_registration_exists(p_registration_no, p_student_id) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This registration number is already used by another student.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM batch_program WHERE batch_program_id = p_batch_program_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid batch program selected.';
    END IF;

    UPDATE users
    SET first_name = p_first_name,
        last_name = p_last_name,
        email = p_email,
        password_hash = p_password_hash,
        gender = p_gender,
        account_status = p_account_status
    WHERE user_id = v_user_id;

    UPDATE student
    SET batch_program_id = p_batch_program_id,
        registration_no = p_registration_no,
        student_status = p_student_status
    WHERE student_id = p_student_id;

    DELETE FROM user_phone WHERE user_id = v_user_id;

    IF p_phone_no IS NOT NULL AND p_phone_no <> '' THEN
        INSERT INTO user_phone (user_id, phone_no)
        VALUES (v_user_id, p_phone_no);
    END IF;
END$$

CREATE PROCEDURE sp_delete_student_safe(IN p_student_id INT)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_enrollment_count INT DEFAULT 0;

    SELECT user_id
    INTO v_user_id
    FROM student
    WHERE student_id = p_student_id;

    IF v_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student not found.';
    END IF;

    SELECT COUNT(*)
    INTO v_enrollment_count
    FROM enrollment
    WHERE student_id = p_student_id;

    IF v_enrollment_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot delete student because enrollment history exists. Deactivate the account instead.';
    END IF;

    DELETE FROM user_phone WHERE user_id = v_user_id;
    DELETE FROM student WHERE student_id = p_student_id;
    DELETE FROM users WHERE user_id = v_user_id;
END$$

CREATE PROCEDURE sp_add_faculty(
    IN p_first_name VARCHAR(80),
    IN p_last_name VARCHAR(80),
    IN p_email VARCHAR(150),
    IN p_password_hash VARCHAR(255),
    IN p_gender VARCHAR(20),
    IN p_account_status VARCHAR(30),
    IN p_phone_no VARCHAR(30),
    IN p_department_id INT,
    IN p_designation VARCHAR(80)
)
BEGIN
    DECLARE v_user_id INT;

    IF p_first_name = '' OR p_last_name = '' OR p_email = '' OR p_password_hash = '' OR p_designation = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Required faculty fields are missing.';
    END IF;

    IF fn_email_exists(p_email, NULL) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This email already exists.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM department WHERE department_id = p_department_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid department selected.';
    END IF;

    INSERT INTO users
    (first_name, last_name, email, password_hash, role, gender, account_status, created_at)
    VALUES
    (p_first_name, p_last_name, p_email, p_password_hash, 'Faculty', p_gender, p_account_status, NOW());

    SET v_user_id = LAST_INSERT_ID();

    INSERT INTO faculty
    (user_id, department_id, designation)
    VALUES
    (v_user_id, p_department_id, p_designation);

    IF p_phone_no IS NOT NULL AND p_phone_no <> '' THEN
        INSERT INTO user_phone (user_id, phone_no)
        VALUES (v_user_id, p_phone_no);
    END IF;
END$$

CREATE PROCEDURE sp_update_faculty(
    IN p_teacher_id INT,
    IN p_first_name VARCHAR(80),
    IN p_last_name VARCHAR(80),
    IN p_email VARCHAR(150),
    IN p_password_hash VARCHAR(255),
    IN p_gender VARCHAR(20),
    IN p_account_status VARCHAR(30),
    IN p_phone_no VARCHAR(30),
    IN p_department_id INT,
    IN p_designation VARCHAR(80)
)
BEGIN
    DECLARE v_user_id INT;

    SELECT user_id
    INTO v_user_id
    FROM faculty
    WHERE teacher_id = p_teacher_id;

    IF v_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Faculty member not found.';
    END IF;

    IF fn_email_exists(p_email, v_user_id) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This email is already used by another user.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM department WHERE department_id = p_department_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid department selected.';
    END IF;

    UPDATE users
    SET first_name = p_first_name,
        last_name = p_last_name,
        email = p_email,
        password_hash = p_password_hash,
        gender = p_gender,
        account_status = p_account_status
    WHERE user_id = v_user_id;

    UPDATE faculty
    SET department_id = p_department_id,
        designation = p_designation
    WHERE teacher_id = p_teacher_id;

    DELETE FROM user_phone WHERE user_id = v_user_id;

    IF p_phone_no IS NOT NULL AND p_phone_no <> '' THEN
        INSERT INTO user_phone (user_id, phone_no)
        VALUES (v_user_id, p_phone_no);
    END IF;
END$$

CREATE PROCEDURE sp_delete_faculty_safe(IN p_teacher_id INT)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_assignment_count INT DEFAULT 0;

    SELECT user_id
    INTO v_user_id
    FROM faculty
    WHERE teacher_id = p_teacher_id;

    IF v_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Faculty member not found.';
    END IF;

    SELECT COUNT(*)
    INTO v_assignment_count
    FROM teacher_assignment
    WHERE teacher_id = p_teacher_id;

    IF v_assignment_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This faculty member has teacher assignments. Deactivate the account instead of deleting.';
    END IF;

    DELETE FROM user_phone WHERE user_id = v_user_id;
    DELETE FROM faculty WHERE teacher_id = p_teacher_id;
    DELETE FROM users WHERE user_id = v_user_id;
END$$

CREATE PROCEDURE sp_add_course(
    IN p_department_id INT,
    IN p_course_code VARCHAR(30),
    IN p_course_title VARCHAR(150),
    IN p_credit_hours INT
)
BEGIN
    IF p_course_code = '' OR p_course_title = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course code and title are required.';
    END IF;

    IF p_credit_hours <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Credit hours must be greater than zero.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM department WHERE department_id = p_department_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid department selected.';
    END IF;

    IF fn_course_code_exists(p_course_code, NULL) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This course code already exists.';
    END IF;

    INSERT INTO course
    (department_id, course_code, course_title, credit_hours)
    VALUES
    (p_department_id, p_course_code, p_course_title, p_credit_hours);
END$$

CREATE PROCEDURE sp_delete_course_safe(IN p_course_id INT)
BEGIN
    DECLARE v_assignment_count INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_assignment_count
    FROM teacher_assignment
    WHERE course_id = p_course_id;

    IF v_assignment_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This course is already used in teacher assignments.';
    END IF;

    DELETE FROM course WHERE course_id = p_course_id;
END$$

CREATE PROCEDURE sp_add_teacher_assignment(
    IN p_teacher_id INT,
    IN p_course_id INT,
    IN p_semester_id INT,
    IN p_section_id INT,
    IN p_assigned_date DATE
)
BEGIN
    DECLARE v_faculty_department_id INT;
    DECLARE v_course_department_id INT;
    DECLARE v_duplicate_count INT DEFAULT 0;

    SELECT department_id
    INTO v_faculty_department_id
    FROM faculty
    WHERE teacher_id = p_teacher_id;

    SELECT department_id
    INTO v_course_department_id
    FROM course
    WHERE course_id = p_course_id;

    IF v_faculty_department_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid faculty selected.';
    END IF;

    IF v_course_department_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid course selected.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM semester WHERE semester_id = p_semester_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid semester selected.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM section WHERE section_id = p_section_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid section selected.';
    END IF;

    IF v_faculty_department_id <> v_course_department_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Faculty and course must belong to the same department.';
    END IF;

    SELECT COUNT(*)
    INTO v_duplicate_count
    FROM teacher_assignment
    WHERE teacher_id = p_teacher_id
      AND course_id = p_course_id
      AND semester_id = p_semester_id
      AND section_id = p_section_id;

    IF v_duplicate_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This teacher assignment already exists.';
    END IF;

    INSERT INTO teacher_assignment
    (teacher_id, course_id, semester_id, section_id, assigned_date)
    VALUES
    (p_teacher_id, p_course_id, p_semester_id, p_section_id, p_assigned_date);
END$$

CREATE PROCEDURE sp_delete_teacher_assignment_safe(IN p_teacher_assignment_id INT)
BEGIN
    DECLARE v_assessment_count INT DEFAULT 0;
    DECLARE v_registered_count INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_assessment_count
    FROM assessment
    WHERE teacher_assignment_id = p_teacher_assignment_id;

    SELECT COUNT(*)
    INTO v_registered_count
    FROM registered_course
    WHERE teacher_assignment_id = p_teacher_assignment_id;

    IF v_assessment_count > 0 OR v_registered_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This teacher assignment is used in assessments or registered courses.';
    END IF;

    DELETE FROM teacher_assignment
    WHERE teacher_assignment_id = p_teacher_assignment_id;
END$$

CREATE PROCEDURE sp_add_enrollment(
    IN p_student_id INT,
    IN p_section_id INT,
    IN p_session_id INT,
    IN p_semester_id INT,
    IN p_is_repeat VARCHAR(10),
    IN p_enrollment_status VARCHAR(30),
    IN p_enrollment_start_date DATE,
    IN p_enrollment_end_date DATE
)
BEGIN
    DECLARE v_student_program_id INT;
    DECLARE v_section_program_id INT;
    DECLARE v_account_status VARCHAR(30);
    DECLARE v_available_seats INT DEFAULT 0;

    SELECT bp.program_id, u.account_status
    INTO v_student_program_id, v_account_status
    FROM student s
    JOIN users u ON s.user_id = u.user_id
    JOIN batch_program bp ON s.batch_program_id = bp.batch_program_id
    WHERE s.student_id = p_student_id;

    SELECT bp.program_id
    INTO v_section_program_id
    FROM section sec
    JOIN batch_program bp ON sec.batch_program_id = bp.batch_program_id
    WHERE sec.section_id = p_section_id;

    IF v_student_program_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student not found.';
    END IF;

    IF v_account_status <> 'Active' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student account is not active.';
    END IF;

    IF v_section_program_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Selected section does not exist.';
    END IF;

    IF v_student_program_id <> v_section_program_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Selected section does not belong to this student program.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM academic_session WHERE session_id = p_session_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid academic session selected.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM semester WHERE semester_id = p_semester_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid semester selected.';
    END IF;

    IF fn_student_already_enrolled(p_student_id, p_section_id, p_session_id, p_semester_id) > 0
       AND p_is_repeat = 'No' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student is already enrolled in this section, session, and semester.';
    END IF;

    SET v_available_seats = fn_section_available_seats(p_section_id, p_session_id, p_semester_id);

    IF v_available_seats <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No available seats in this section.';
    END IF;

    INSERT INTO enrollment
    (student_id, section_id, session_id, semester_id, is_repeat,
     enrollment_status, enrollment_start_date, enrollment_end_date)
    VALUES
    (p_student_id, p_section_id, p_session_id, p_semester_id, p_is_repeat,
     p_enrollment_status, p_enrollment_start_date, p_enrollment_end_date);
END$$

CREATE PROCEDURE sp_add_registered_course(
    IN p_enrollment_id INT,
    IN p_teacher_assignment_id INT
)
BEGIN
    DECLARE v_section_id INT;
    DECLARE v_semester_id INT;
    DECLARE v_student_id INT;
    DECLARE v_course_id INT;
    DECLARE v_previous_enrollment_end DATE;
    DECLARE v_is_repeat VARCHAR(10);
    DECLARE v_duplicate_count INT DEFAULT 0;

    SELECT section_id, semester_id, student_id, is_repeat
    INTO v_section_id, v_semester_id, v_student_id, v_is_repeat
    FROM enrollment
    WHERE enrollment_id = p_enrollment_id;

    IF v_section_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Enrollment not found.';
    END IF;

    SELECT course_id
    INTO v_course_id
    FROM teacher_assignment
    WHERE teacher_assignment_id = p_teacher_assignment_id
      AND section_id = v_section_id
      AND semester_id = v_semester_id;

    IF v_course_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Selected course does not belong to the enrollment section and semester.';
    END IF;

    SELECT COUNT(*)
    INTO v_duplicate_count
    FROM registered_course
    WHERE enrollment_id = p_enrollment_id
      AND teacher_assignment_id = p_teacher_assignment_id;

    IF v_duplicate_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This registered course already exists in the enrollment.';
    END IF;

    SELECT e.enrollment_end_date
    INTO v_previous_enrollment_end
    FROM registered_course rc
    JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
    JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
    WHERE e.student_id = v_student_id
      AND ta.course_id = v_course_id
      AND e.enrollment_id <> p_enrollment_id
    ORDER BY e.enrollment_id DESC
    LIMIT 1;

    IF v_previous_enrollment_end IS NOT NULL THEN
        IF v_is_repeat = 'No' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student already has this course. Select repeat enrollment if applicable.';
        END IF;

        IF v_previous_enrollment_end >= CURDATE() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Previous enrollment for this course has not ended yet.';
        END IF;
    END IF;

    INSERT INTO registered_course
    (enrollment_id, teacher_assignment_id, registration_status)
    VALUES
    (p_enrollment_id, p_teacher_assignment_id, 'Registered');
END$$

CREATE TRIGGER trg_prevent_submission_when_portal_closed
BEFORE INSERT ON submission
FOR EACH ROW
BEGIN
    DECLARE v_portal_status VARCHAR(20);

    SELECT portal_status
    INTO v_portal_status
    FROM assessment
    WHERE assessment_id = NEW.assessment_id;

    IF v_portal_status = 'Closed' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot submit because the assessment portal is closed.';
    END IF;
END$$

CREATE TRIGGER trg_prevent_submission_update_when_portal_closed
BEFORE UPDATE ON submission
FOR EACH ROW
BEGIN
    DECLARE v_portal_status VARCHAR(20);

    SELECT portal_status
    INTO v_portal_status
    FROM assessment
    WHERE assessment_id = NEW.assessment_id;

    IF v_portal_status = 'Closed'
       AND (
            NOT (NEW.file_name <=> OLD.file_name)
            OR NOT (NEW.file_path <=> OLD.file_path)
            OR NOT (NEW.upload_time <=> OLD.upload_time)
            OR NOT (NEW.submission_status <=> OLD.submission_status)
       ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot update submission because the assessment portal is closed.';
    END IF;
END$$

CREATE TRIGGER trg_calculate_evaluation_percentage_insert
BEFORE INSERT ON evaluation
FOR EACH ROW
BEGIN
    DECLARE v_total_marks DECIMAL(8,2);

    SELECT a.total_marks
    INTO v_total_marks
    FROM submission sub
    JOIN assessment a ON sub.assessment_id = a.assessment_id
    WHERE sub.submission_id = NEW.submission_id;

    IF v_total_marks IS NULL OR v_total_marks <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid total marks for evaluation percentage.';
    END IF;

    SET NEW.percentage = ROUND((NEW.obtained_marks / v_total_marks) * 100, 2);
END$$

CREATE TRIGGER trg_calculate_evaluation_percentage_update
BEFORE UPDATE ON evaluation
FOR EACH ROW
BEGIN
    DECLARE v_total_marks DECIMAL(8,2);

    SELECT a.total_marks
    INTO v_total_marks
    FROM submission sub
    JOIN assessment a ON sub.assessment_id = a.assessment_id
    WHERE sub.submission_id = NEW.submission_id;

    IF v_total_marks IS NULL OR v_total_marks <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid total marks for evaluation percentage.';
    END IF;

    SET NEW.percentage = ROUND((NEW.obtained_marks / v_total_marks) * 100, 2);
END$$

CREATE TRIGGER trg_prevent_duplicate_active_enrollment
BEFORE INSERT ON enrollment
FOR EACH ROW
BEGIN
    DECLARE v_duplicate_count INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_duplicate_count
    FROM enrollment
    WHERE student_id = NEW.student_id
      AND section_id = NEW.section_id
      AND session_id = NEW.session_id
      AND semester_id = NEW.semester_id
      AND enrollment_status = 'Currently enrolled';

    IF v_duplicate_count > 0 AND NEW.is_repeat = 'No' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Duplicate active enrollment is not allowed.';
    END IF;
END$$

DELIMITER ;

SELECT 'Views, functions, procedures, and triggers created successfully.' AS message;
