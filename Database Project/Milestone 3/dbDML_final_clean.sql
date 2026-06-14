USE fair_assessment_system;

SET @dummy_submission_path = 'C:/Users/admin/Desktop/Fair and Un biased System/dummy_student_submission.pdf';
SET @dummy_student_report_path = 'C:/Users/admin/Desktop/Fair and Un biased System/dummy_student_evaluation_report.pdf';
SET @dummy_class_report_path = 'C:/Users/admin/Desktop/Fair and Un biased System/dummy_class_assessment_report.pdf';

INSERT INTO users
(user_id, first_name, last_name, email, password_hash, role, gender, account_status, created_at)
VALUES
(1, 'System', 'Admin', 'admin@namal.edu.pk', 'hashed_password_123', 'Admin', 'Male', 'Active', '2025-08-01 09:00:00'),
(2, 'Rafay', 'Khan', 'rafay.khan@namal.edu.pk', 'faculty_hash_456', 'Faculty', 'Male', 'Active', '2025-08-01 09:05:00'),
(3, 'Asiya', 'Batool', 'asiya.batool@namal.edu.pk', 'faculty_hash_456', 'Faculty', 'Female', 'Active', '2025-08-01 09:10:00'),
(4, 'Ramzan', 'Shahid', 'ramzan.shahid@namal.edu.pk', 'faculty_hash_456', 'Faculty', 'Male', 'Active', '2025-08-01 09:15:00'),
(5, 'Abdul', 'Rehman', 'abdul.rehman01@students.namal.edu.pk', 'student_hash_789', 'Student', 'Male', 'Active', '2025-08-10 10:00:00'),
(6, 'Sara', 'Ahmed', 'sara.ahmed02@students.namal.edu.pk', 'student_hash_789', 'Student', 'Female', 'Active', '2025-08-10 10:05:00'),
(7, 'Ali', 'Hassan', 'ali.hassan03@students.namal.edu.pk', 'student_hash_789', 'Student', 'Male', 'Active', '2025-08-10 10:10:00'),
(8, 'Ayesha', 'Malik', 'ayesha.malik04@students.namal.edu.pk', 'student_hash_789', 'Student', 'Female', 'Active', '2025-08-10 10:15:00'),
(9, 'Bilal', 'Khan', 'bilal.khan05@students.namal.edu.pk', 'student_hash_789', 'Student', 'Male', 'Active', '2025-08-10 10:20:00');

INSERT INTO department
(department_id, department_name, department_code)
VALUES
(1, 'Computer Science', 'CS'),
(2, 'Management Sciences', 'MS');

INSERT INTO program
(program_id, department_id, program_name, program_code, degree_level, total_semester)
VALUES
(1, 1, 'BS Computer Science', 'BSCS', 'Undergraduate', 8),
(2, 1, 'BS Artificial Intelligence', 'BSAI', 'Undergraduate', 8),
(3, 2, 'Bachelor of Business Administration', 'BBA', 'Undergraduate', 8),
(4, 2, 'BS Accounting and Finance', 'BSAF', 'Undergraduate', 8);

INSERT INTO batch
(batch_id, batch_name, start_year, batch_status)
VALUES
(1, 'Batch 2024', 2024, 'Active'),
(2, 'Batch 2025', 2025, 'Active');

INSERT INTO batch_program
(batch_program_id, batch_id, program_id, expected_graduation)
VALUES
(1, 1, 1, 2028),
(2, 1, 2, 2028),
(3, 1, 3, 2028),
(4, 1, 4, 2028),
(5, 2, 1, 2029),
(6, 2, 2, 2029),
(7, 2, 3, 2029),
(8, 2, 4, 2029);

INSERT INTO academic_session
(session_id, session_name, academic_year, start_date, end_date)
VALUES
(1, 'Fall', '2025', '2025-08-15', '2025-12-31'),
(2, 'Spring', '2026', '2026-01-15', '2026-07-15');

INSERT INTO semester
(semester_id, semester_no)
VALUES
(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8);

INSERT INTO faculty
(teacher_id, user_id, department_id, designation)
VALUES
(1, 2, 1, 'Lecturer'),
(2, 3, 1, 'Lecturer'),
(3, 4, 1, 'Assistant Professor');

INSERT INTO student
(student_id, user_id, batch_program_id, registration_no, student_status)
VALUES
(1, 5, 1, 'NUM-BSCS-2024-01', 'Active'),
(2, 6, 1, 'NUM-BSCS-2024-02', 'Active'),
(3, 7, 1, 'NUM-BSCS-2024-03', 'Active'),
(4, 8, 1, 'NUM-BSCS-2024-04', 'Active'),
(5, 9, 1, 'NUM-BSCS-2024-05', 'Active');

INSERT INTO user_phone
(phone_id, user_id, phone_no)
VALUES
(1, 2, '0300-1111111'),
(2, 3, '0300-2222222'),
(3, 4, '0300-3333333'),
(4, 5, '0300-4444444'),
(5, 6, '0300-5555555');

INSERT INTO course
(course_id, department_id, course_code, course_title, credit_hours)
VALUES
(1, 1, 'CSC-102', 'Object Oriented Programming', 3),
(2, 1, 'CSC-211', 'Data Structures and Algorithms', 3),
(3, 1, 'CSC-224', 'Computer Organization and Assembly Language', 3),
(4, 1, 'CSC-271', 'Database Systems', 3),
(5, 1, 'CSC-310', 'Operating Systems', 3),
(6, 2, 'MGT-101', 'Principles of Management', 3),
(7, 2, 'ACC-101', 'Financial Accounting', 3);

INSERT INTO section
(section_id, batch_program_id, section_name, capacity)
VALUES
(1, 1, 'A', 45),
(2, 1, 'B', 45),
(4, 3, 'A', 40),
(5, 4, 'A', 40);

INSERT INTO teacher_assignment
(teacher_assignment_id, teacher_id, course_id, semester_id, section_id, assigned_date)
VALUES
(1, 1, 1, 3, 1, '2025-08-10'),
(2, 1, 2, 4, 1, '2026-01-10'),
(3, 3, 3, 4, 1, '2026-01-10'),
(4, 2, 4, 4, 1, '2026-01-10'),
(5, 2, 2, 4, 2, '2026-01-10');

INSERT INTO enrollment
(enrollment_id, student_id, section_id, session_id, semester_id, is_repeat, enrollment_status, enrollment_start_date, enrollment_end_date)
VALUES
(1, 1, 1, 2, 4, 'No', 'Currently enrolled', '2026-01-15', NULL),
(2, 2, 1, 2, 4, 'No', 'Currently enrolled', '2026-01-15', NULL),
(3, 3, 1, 2, 4, 'No', 'Currently enrolled', '2026-01-15', NULL),
(4, 4, 1, 2, 4, 'No', 'Currently enrolled', '2026-01-15', NULL),
(5, 5, 1, 2, 4, 'No', 'Currently enrolled', '2026-01-15', NULL),
(6, 1, 1, 1, 3, 'No', 'Completed', '2025-08-15', '2025-12-31'),
(7, 2, 1, 1, 3, 'No', 'Completed', '2025-08-15', '2025-12-31'),
(8, 3, 1, 1, 3, 'No', 'Completed', '2025-08-15', '2025-12-31');

INSERT INTO registered_course
(registered_course_id, enrollment_id, teacher_assignment_id, registration_status)
VALUES
(1, 1, 2, 'Registered'),
(2, 1, 3, 'Registered'),
(3, 1, 4, 'Registered'),
(4, 2, 2, 'Registered'),
(5, 2, 3, 'Registered'),
(6, 2, 4, 'Registered'),
(7, 3, 2, 'Registered'),
(8, 3, 3, 'Registered'),
(9, 3, 4, 'Registered'),
(10, 4, 2, 'Registered'),
(11, 4, 3, 'Registered'),
(12, 4, 4, 'Registered'),
(13, 5, 2, 'Registered'),
(14, 5, 3, 'Registered'),
(15, 5, 4, 'Registered'),
(16, 6, 1, 'Registered'),
(17, 7, 1, 'Registered'),
(18, 8, 1, 'Registered');

INSERT INTO assessment
(assessment_id, teacher_assignment_id, session_id, title, description, assessment_type, total_marks, created_at, deadline, portal_status, class_report_path, class_report_generated_at, class_report_status)
VALUES
(1, 2, 2, 'DSA Assignment 1', 'Linked list and stack implementation task.', 'Assignment', 100.00, '2026-02-01 09:00:00', '2026-02-15', 'Closed', @dummy_class_report_path, '2026-02-16 14:00:00', 'Generated'),
(2, 2, 2, 'DSA Quiz 1', 'Short quiz covering arrays, recursion and complexity basics.', 'Quiz', 20.00, '2026-03-01 09:00:00', '2026-03-10', 'Closed', NULL, NULL, 'Not Generated'),
(3, 2, 2, 'DSA Lab Task 4', 'Lab submission for queue implementation.', 'Lab Task', 30.00, '2026-06-01 09:00:00', '2026-06-25', 'Open', NULL, NULL, 'Not Generated'),
(4, 2, 2, 'DSA Project Proposal', 'Initial project proposal for the final DSA project.', 'Project', 50.00, '2026-06-05 09:00:00', '2026-06-30', 'Open', NULL, NULL, 'Not Generated'),
(5, 3, 2, 'COA Assignment 1', 'Instruction cycle and addressing mode worksheet.', 'Assignment', 50.00, '2026-02-10 09:00:00', '2026-02-25', 'Closed', @dummy_class_report_path, '2026-02-26 13:30:00', 'Generated'),
(6, 4, 2, 'Database ERD Task', 'Draw and submit ERD for academic management scenario.', 'Assignment', 40.00, '2026-06-05 09:00:00', '2026-06-28', 'Open', NULL, NULL, 'Not Generated'),
(7, 1, 1, 'OOP Final Assignment', 'Previous semester OOP class and inheritance task.', 'Assignment', 100.00, '2025-11-10 09:00:00', '2025-11-30', 'Closed', @dummy_class_report_path, '2025-12-01 10:30:00', 'Generated');

INSERT INTO submission
(submission_id, assessment_id, registered_course_id, file_name, file_path, upload_time, submission_status)
VALUES
(1, 1, 1, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-02-12 18:20:00', 'Submitted'),
(2, 1, 4, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-02-13 15:40:00', 'Submitted'),
(3, 1, 7, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-02-14 16:10:00', 'Submitted'),
(4, 2, 1, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-03-08 20:10:00', 'Submitted'),
(5, 2, 4, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-03-09 19:25:00', 'Submitted'),
(6, 3, 1, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-06-10 17:00:00', 'Submitted'),
(7, 4, 7, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-06-12 21:15:00', 'Submitted'),
(8, 5, 2, 'dummy_student_submission.pdf', @dummy_submission_path, '2026-02-20 18:45:00', 'Submitted'),
(9, 7, 16, 'dummy_student_submission.pdf', @dummy_submission_path, '2025-11-25 19:20:00', 'Submitted');

INSERT INTO evaluation
(evaluation_id, submission_id, obtained_marks, percentage, evaluated_at, evaluation_status, feedback, student_report_path, student_report_generated_at, student_report_status)
VALUES
(1, 1, 82.00, 82.00, '2026-02-16 11:00:00', 'Evaluated', 'Good implementation. Minor improvement needed in edge cases.', @dummy_student_report_path, '2026-02-16 11:05:00', 'Generated'),
(2, 2, 76.00, 76.00, '2026-02-16 11:15:00', 'Evaluated', 'Correct logic with some formatting issues.', @dummy_student_report_path, '2026-02-16 11:20:00', 'Generated'),
(3, 3, 90.00, 90.00, '2026-02-16 11:30:00', 'Evaluated', 'Excellent solution and clear structure.', @dummy_student_report_path, '2026-02-16 11:35:00', 'Generated'),
(4, 8, 42.00, 84.00, '2026-02-26 10:00:00', 'Evaluated', 'Good understanding of instruction cycle.', @dummy_student_report_path, '2026-02-26 10:05:00', 'Generated'),
(5, 9, 78.00, 78.00, '2025-12-01 09:00:00', 'Evaluated', 'Good OOP concepts and class design.', @dummy_student_report_path, '2025-12-01 09:10:00', 'Generated');

INSERT INTO campus
(campus_id, campus_name, campus_location)
VALUES
(1, 'Namal Main Campus', 'Mianwali');

INSERT INTO room
(room_id, campus_id, room_no, room_type, capacity)
VALUES
(1, 1, 'CS-Lab-1', 'Computer Lab', 45),
(2, 1, 'CR-101', 'Classroom', 50);

INSERT INTO attendance
(attendance_id, registered_course_id, attendance_date, status)
VALUES
(1, 1, '2026-02-01', 'Present'),
(2, 1, '2026-02-03', 'Present'),
(3, 2, '2026-02-02', 'Present'),
(4, 3, '2026-02-04', 'Absent');

INSERT INTO result
(result_id, registered_course_id, final_marks, grade, result_status)
VALUES
(1, 16, 78.00, 'B+', 'Published'),
(2, 17, 81.00, 'A-', 'Published'),
(3, 18, 74.00, 'B', 'Published'),
(4, 1, NULL, NULL, 'In Progress'),
(5, 2, NULL, NULL, 'In Progress'),
(6, 3, NULL, NULL, 'In Progress');

SELECT 'Final clean DML inserted successfully.' AS message;

SELECT
    acs.session_name,
    acs.academic_year,
    s.registration_no,
    CONCAT(su.first_name, ' ', su.last_name) AS student_name,
    c.course_code,
    c.course_title,
    CONCAT(fu.first_name, ' ', fu.last_name) AS faculty_name,
    rc.registered_course_id,
    ta.teacher_assignment_id
FROM registered_course rc
JOIN enrollment e ON rc.enrollment_id = e.enrollment_id
JOIN academic_session acs ON e.session_id = acs.session_id
JOIN student s ON e.student_id = s.student_id
JOIN users su ON s.user_id = su.user_id
JOIN teacher_assignment ta ON rc.teacher_assignment_id = ta.teacher_assignment_id
JOIN faculty f ON ta.teacher_id = f.teacher_id
JOIN users fu ON f.user_id = fu.user_id
JOIN course c ON ta.course_id = c.course_id
ORDER BY acs.start_date, student_name, course_code;
