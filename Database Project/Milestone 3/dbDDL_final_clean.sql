DROP DATABASE IF EXISTS fair_assessment_system;
CREATE DATABASE fair_assessment_system;
USE fair_assessment_system;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    gender VARCHAR(10),
    account_status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_users_role CHECK (role IN ('Admin', 'Faculty', 'Student')),
    CONSTRAINT chk_users_status CHECK (account_status IN ('Active', 'Inactive'))
);

CREATE TABLE department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    department_code VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE program (
    program_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    program_name VARCHAR(100) NOT NULL,
    program_code VARCHAR(20) NOT NULL UNIQUE,
    degree_level VARCHAR(30) NOT NULL,
    total_semester INT NOT NULL,
    CONSTRAINT fk_program_department
        FOREIGN KEY (department_id) REFERENCES department(department_id),
    CONSTRAINT uq_program_department_name UNIQUE (department_id, program_name)
);

CREATE TABLE batch (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_name VARCHAR(30) NOT NULL UNIQUE,
    start_year INT NOT NULL,
    batch_status VARCHAR(20) NOT NULL DEFAULT 'Active'
);

CREATE TABLE batch_program (
    batch_program_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    program_id INT NOT NULL,
    expected_graduation INT NOT NULL,
    CONSTRAINT fk_batch_program_batch
        FOREIGN KEY (batch_id) REFERENCES batch(batch_id),
    CONSTRAINT fk_batch_program_program
        FOREIGN KEY (program_id) REFERENCES program(program_id),
    CONSTRAINT uq_batch_program UNIQUE (batch_id, program_id)
);

CREATE TABLE academic_session (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    session_name VARCHAR(30) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    CONSTRAINT uq_academic_session UNIQUE (session_name, academic_year),
    CONSTRAINT chk_session_dates CHECK (end_date >= start_date)
);

CREATE TABLE semester (
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    semester_no INT NOT NULL UNIQUE
);

CREATE TABLE faculty (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    department_id INT NOT NULL,
    designation VARCHAR(80) NOT NULL,
    CONSTRAINT fk_faculty_user
        FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_faculty_department
        FOREIGN KEY (department_id) REFERENCES department(department_id)
);

CREATE TABLE student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    batch_program_id INT NOT NULL,
    registration_no VARCHAR(50) NOT NULL UNIQUE,
    student_status VARCHAR(30) NOT NULL DEFAULT 'Active',
    CONSTRAINT fk_student_user
        FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_student_batch_program
        FOREIGN KEY (batch_program_id) REFERENCES batch_program(batch_program_id)
);

CREATE TABLE user_phone (
    phone_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    phone_no VARCHAR(30) NOT NULL,
    CONSTRAINT fk_user_phone_user
        FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT uq_user_phone UNIQUE (user_id, phone_no)
);

CREATE TABLE course (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    course_code VARCHAR(30) NOT NULL UNIQUE,
    course_title VARCHAR(150) NOT NULL,
    credit_hours INT NOT NULL,
    CONSTRAINT fk_course_department
        FOREIGN KEY (department_id) REFERENCES department(department_id)
);

CREATE TABLE section (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_program_id INT NOT NULL,
    section_name VARCHAR(20) NOT NULL,
    capacity INT NOT NULL,
    CONSTRAINT fk_section_batch_program
        FOREIGN KEY (batch_program_id) REFERENCES batch_program(batch_program_id),
    CONSTRAINT uq_section_batch_program UNIQUE (batch_program_id, section_name)
);

CREATE TABLE teacher_assignment (
    teacher_assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    course_id INT NOT NULL,
    semester_id INT NOT NULL,
    section_id INT NOT NULL,
    assigned_date DATE NOT NULL,
    CONSTRAINT fk_teacher_assignment_faculty
        FOREIGN KEY (teacher_id) REFERENCES faculty(teacher_id),
    CONSTRAINT fk_teacher_assignment_course
        FOREIGN KEY (course_id) REFERENCES course(course_id),
    CONSTRAINT fk_teacher_assignment_semester
        FOREIGN KEY (semester_id) REFERENCES semester(semester_id),
    CONSTRAINT fk_teacher_assignment_section
        FOREIGN KEY (section_id) REFERENCES section(section_id),
    CONSTRAINT uq_teacher_course_section_semester UNIQUE (teacher_id, course_id, semester_id, section_id)
);

CREATE TABLE enrollment (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    section_id INT NOT NULL,
    session_id INT NOT NULL,
    semester_id INT NOT NULL,
    is_repeat VARCHAR(5) NOT NULL DEFAULT 'No',
    enrollment_status VARCHAR(30) NOT NULL,
    enrollment_start_date DATE NOT NULL,
    enrollment_end_date DATE NULL,
    CONSTRAINT fk_enrollment_student
        FOREIGN KEY (student_id) REFERENCES student(student_id),
    CONSTRAINT fk_enrollment_section
        FOREIGN KEY (section_id) REFERENCES section(section_id),
    CONSTRAINT fk_enrollment_session
        FOREIGN KEY (session_id) REFERENCES academic_session(session_id),
    CONSTRAINT fk_enrollment_semester
        FOREIGN KEY (semester_id) REFERENCES semester(semester_id),
    CONSTRAINT uq_student_session_semester UNIQUE (student_id, session_id, semester_id)
);

CREATE TABLE registered_course (
    registered_course_id INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT NOT NULL,
    teacher_assignment_id INT NOT NULL,
    registration_status VARCHAR(30) NOT NULL DEFAULT 'Registered',
    CONSTRAINT fk_registered_course_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollment(enrollment_id),
    CONSTRAINT fk_registered_course_teacher_assignment
        FOREIGN KEY (teacher_assignment_id) REFERENCES teacher_assignment(teacher_assignment_id),
    CONSTRAINT uq_enrollment_teacher_assignment UNIQUE (enrollment_id, teacher_assignment_id)
);

CREATE TABLE assessment (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_assignment_id INT NOT NULL,
    session_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    assessment_type VARCHAR(50) NOT NULL,
    total_marks DECIMAL(6,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deadline DATE NOT NULL,
    portal_status VARCHAR(20) NOT NULL DEFAULT 'Open',
    class_report_path VARCHAR(500) NULL,
    class_report_generated_at DATETIME NULL,
    class_report_status VARCHAR(30) NOT NULL DEFAULT 'Not Generated',
    CONSTRAINT fk_assessment_teacher_assignment
        FOREIGN KEY (teacher_assignment_id) REFERENCES teacher_assignment(teacher_assignment_id),
    CONSTRAINT fk_assessment_session
        FOREIGN KEY (session_id) REFERENCES academic_session(session_id),
    CONSTRAINT chk_assessment_portal_status CHECK (portal_status IN ('Open', 'Closed')),
    CONSTRAINT chk_assessment_report_status CHECK (class_report_status IN ('Generated', 'Not Generated'))
);

CREATE TABLE submission (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    registered_course_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    upload_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submission_status VARCHAR(30) NOT NULL DEFAULT 'Submitted',
    CONSTRAINT fk_submission_assessment
        FOREIGN KEY (assessment_id) REFERENCES assessment(assessment_id),
    CONSTRAINT fk_submission_registered_course
        FOREIGN KEY (registered_course_id) REFERENCES registered_course(registered_course_id),
    CONSTRAINT uq_submission_assessment_registered_course UNIQUE (assessment_id, registered_course_id)
);

CREATE TABLE evaluation (
    evaluation_id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT NOT NULL UNIQUE,
    obtained_marks DECIMAL(6,2) NOT NULL,
    percentage DECIMAL(6,2) NOT NULL,
    evaluated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    evaluation_status VARCHAR(30) NOT NULL DEFAULT 'Evaluated',
    feedback TEXT,
    student_report_path VARCHAR(500) NULL,
    student_report_generated_at DATETIME NULL,
    student_report_status VARCHAR(30) NOT NULL DEFAULT 'Not Generated',
    CONSTRAINT fk_evaluation_submission
        FOREIGN KEY (submission_id) REFERENCES submission(submission_id),
    CONSTRAINT chk_evaluation_report_status CHECK (student_report_status IN ('Generated', 'Not Generated'))
);

CREATE TABLE campus (
    campus_id INT AUTO_INCREMENT PRIMARY KEY,
    campus_name VARCHAR(100) NOT NULL UNIQUE,
    campus_location VARCHAR(150) NOT NULL
);

CREATE TABLE room (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    campus_id INT NOT NULL,
    room_no VARCHAR(30) NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    CONSTRAINT fk_room_campus
        FOREIGN KEY (campus_id) REFERENCES campus(campus_id),
    CONSTRAINT uq_room_campus UNIQUE (campus_id, room_no)
);

CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    registered_course_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    CONSTRAINT fk_attendance_registered_course
        FOREIGN KEY (registered_course_id) REFERENCES registered_course(registered_course_id),
    CONSTRAINT uq_attendance_course_date UNIQUE (registered_course_id, attendance_date)
);

CREATE TABLE result (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    registered_course_id INT NOT NULL,
    final_marks DECIMAL(6,2) NULL,
    grade VARCHAR(5) NULL,
    result_status VARCHAR(30) NOT NULL DEFAULT 'In Progress',
    CONSTRAINT fk_result_registered_course
        FOREIGN KEY (registered_course_id) REFERENCES registered_course(registered_course_id),
    CONSTRAINT uq_result_registered_course UNIQUE (registered_course_id)
);
