# Fair and Unbiased Assessment System

## Overview

The **Fair and Unbiased Assessment System** is a database-driven web application designed for managing academic assessments in a university environment. The system supports structured handling of students, faculty members, departments, programs, batches, sections, academic sessions, courses, teacher assignments, enrollments, registered courses, assessments, submissions, evaluations, and report metadata.

The main purpose of the system is to provide a fair, organized, and transparent assessment workflow. Faculty members can create assessment portals, manage submissions, evaluate student work, and generate reports. Students can view their enrolled courses, upload submissions, and access their evaluation reports when available. Admin users manage the academic structure and maintain the database records required for the complete workflow.

This project is developed as part of the **Software Engineering course** and is being improved incrementally through different milestones. The current implementation focuses strongly on database design, normalization, database connectivity, SQL implementation, and functional web-based modules.

---

## Main Objectives

* Design a normalized relational database for an academic assessment system.
* Manage students, faculty, courses, sections, sessions, and enrollments in a structured way.
* Preserve student academic history across sessions and semesters.
* Link students with courses through enrollment and registered course records.
* Allow faculty members to create and manage session-based assessments.
* Control student submissions using open and closed assessment portals.
* Store evaluation marks, feedback, percentage, and report metadata.
* Reduce duplicate, inconsistent, and redundant academic records.
* Support database-level validation using keys, constraints, views, procedures, functions, and triggers.

---

## Key Features

### Admin Features

* Manage student records.
* Manage faculty records.
* Manage course records.
* Manage teacher assignments.
* Manage student enrollments.
* Register students in assigned courses.
* Search and filter students, faculty, courses, teacher assignments, and enrollments.
* Prevent invalid insertions using database checks and backend validation.
* Maintain academic structure through normalized relational tables.

### Faculty Features

* Faculty login and dashboard.
* View assigned courses according to academic session.
* View course details and enrolled students.
* Create assessments for assigned courses.
* Open and close assessment portals.
* View submitted student work.
* Perform dummy AI-based evaluation for testing.
* Generate or view class report metadata.
* View student evaluation report metadata.

### Student Features

* Student login and dashboard.
* View current session courses.
* Open course detail pages.
* View assessment portals.
* Upload PDF submissions when the portal is open.
* Re-upload submission before the portal is closed.
* View evaluated marks and feedback.
* View student report when evaluation is completed and report is available.

---

## Database Design

The system uses a **MySQL relational database** designed according to real university academic workflow. The database is normalized up to **Third Normal Form (3NF)** to reduce redundancy and improve data consistency.

### Main Database Tables

* `users`
* `student`
* `faculty`
* `department`
* `program`
* `batch`
* `batch_program`
* `academic_session`
* `semester`
* `section`
* `course`
* `teacher_assignment`
* `enrollment`
* `registered_course`
* `assessment`
* `submission`
* `evaluation`
* `user_phone`
* `attendance`
* `result`
* `campus`
* `room`

---

## Important Database Relationships

### User Specialization

The system uses a common `users` table for authentication and profile information.

* One user can be a student.
* One user can be a faculty member.
* Admin users are also stored in the `users` table.

```text
users
 ├── student
 └── faculty
```

### Academic Structure

Departments offer programs and courses. Batches are connected with programs through the `batch_program` table.

```text
department → program
department → course
batch + program → batch_program
batch_program → section
batch_program → student
```

### Enrollment and Registered Courses

Student enrollment is stored separately from registered courses. This helps preserve academic history and avoids repeating multiple course columns inside the enrollment table.

```text
student → enrollment → registered_course → teacher_assignment
```

### Teacher Assignment

A teacher assignment connects one faculty member with one course, semester, and section.

```text
faculty + course + semester + section → teacher_assignment
```

### Assessment and Submission Flow

Assessments are created by faculty for a specific teacher assignment and academic session. Submissions are linked through `registered_course`, not directly through student or enrollment, so the system knows the exact course registration and teacher assignment.

```text
teacher_assignment + academic_session → assessment
assessment + registered_course → submission
submission → evaluation
```

---

## Database Normalization

The database is normalized up to **3NF**.

### First Normal Form (1NF)

* All attributes are atomic.
* Multiple phone numbers are stored in `user_phone`.
* Multiple registered courses are stored in `registered_course`.

### Second Normal Form (2NF)

* Non-key attributes depend on the complete key.
* Relationship-specific data is stored in associative tables such as:

  * `batch_program`
  * `teacher_assignment`
  * `enrollment`
  * `registered_course`

### Third Normal Form (3NF)

* Transitive dependencies are removed.
* `student` does not store current semester or section.
* `section` is stored in `enrollment`.
* `program` is separated from `batch`.
* `academic_session` stores actual Spring/Fall session dates.
* `semester` stores only semester level.
* `submission` uses `registered_course_id` to avoid ambiguous submission ownership.

---

## SQL Implementation

The database implementation is divided into multiple SQL scripts.

### DDL Script

The DDL file creates the complete database structure.

```text
dbDDL_final_clean.sql
```

It includes:

* Database creation.
* Table creation.
* Primary keys.
* Foreign keys.
* Unique constraints.
* Required columns.
* Relationship constraints.

### DML Script

The DML file inserts meaningful test data for the system.

```text
dbDML_final_clean.sql
```

It includes sample data for:

* Admin user.
* Faculty users.
* Student users.
* Departments.
* Programs.
* Batches.
* Sections.
* Sessions.
* Courses.
* Teacher assignments.
* Enrollments.
* Registered courses.
* Assessments.
* Submissions.
* Evaluations.

### Routines Script

The routines file adds database-level support objects.

```text
dbRoutines_final.sql
```

It includes:

* Views.
* Stored procedures.
* Functions.
* Triggers.

---

## Views

Views are used to simplify repeated admin queries and reporting operations.

### Main Views

* `v_admin_dashboard_counts`
* `v_recent_enrollments`
* `v_recent_teacher_assignments`
* `v_admin_students`
* `v_admin_faculty`
* `v_admin_courses`
* `v_admin_teacher_assignments`
* `v_admin_enrollments`
* `v_admin_enrollment_registered_courses`

These views help display dashboard counts, student records, faculty records, course records, teacher assignments, enrollments, and registered course details without writing long joins repeatedly in the backend.

---

## Stored Procedures

Stored procedures are used for controlled insertion, update, and deletion operations.

### Main Procedures

* `sp_add_student`
* `sp_update_student`
* `sp_delete_student_safe`
* `sp_add_faculty`
* `sp_update_faculty`
* `sp_delete_faculty_safe`
* `sp_add_course`
* `sp_delete_course_safe`
* `sp_add_teacher_assignment`
* `sp_delete_teacher_assignment_safe`
* `sp_add_enrollment`
* `sp_add_registered_course`

These procedures help keep database operations consistent and prevent invalid data from being inserted or deleted.

---

## Functions

Functions are used for repeated validation checks.

### Main Functions

* `fn_email_exists`
* `fn_registration_exists`
* `fn_course_code_exists`
* `fn_section_available_seats`
* `fn_current_session_id`
* `fn_student_already_enrolled`

These functions help check duplicate emails, duplicate registration numbers, duplicate course codes, available section seats, current academic session, and duplicate active enrollments.

---

## Triggers

Triggers are used to enforce database-level rules automatically.

### Main Triggers

* `trg_prevent_submission_when_portal_closed`
* `trg_prevent_submission_update_when_portal_closed`
* `trg_calculate_evaluation_percentage_insert`
* `trg_calculate_evaluation_percentage_update`
* `trg_prevent_duplicate_active_enrollment`

These triggers prevent submission when an assessment portal is closed, prevent re-upload after portal closure, calculate evaluation percentage automatically, and block duplicate active enrollments.

---

## Technology Stack

### Current Implementation

* **Frontend:** HTML, CSS, JavaScript, Jinja Templates
* **Backend:** Flask Python
* **Database:** MySQL
* **Database Connector:** MySQL Connector for Python
* **Version Control:** GitHub
* **Design Tool:** Figma

### Development Context

This project is part of a continuous **Software Engineering** course project. Earlier planning discussed a broader AI-based system concept. The current milestone focuses mainly on database design, database implementation, backend connectivity, and working web modules.

---

## Project Structure

```text
Fair and Un biased System/
│
├── app.py
├── db.py
│
├── routes/
│   ├── auth_routes.py
│   ├── admin_routes.py
│   ├── faculty_routes.py
│   └── student_routes.py
│
├── templates/
│   ├── home.html
│   ├── admin_login.html
│   ├── faculty_login.html
│   ├── student_login.html
│   ├── admindashboard.html
│   ├── faculty.html
│   ├── student_dashboard.html
│   └── other system pages
│
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
│
├── dbDDL_final_clean.sql
├── dbDML_final_clean.sql
└── dbRoutines_final.sql
```

---

## How to Run the Project

### Step 1: Run SQL Files

Open MySQL Command Line Client and run:

```sql
SOURCE C:/Users/admin/Desktop/Fair and Un biased System/dbDDL_final_clean.sql;
SOURCE C:/Users/admin/Desktop/Fair and Un biased System/dbDML_final_clean.sql;
SOURCE C:/Users/admin/Desktop/Fair and Un biased System/dbRoutines_final.sql;
```

### Step 2: Start Flask Application

Open terminal in the project folder and run:

```bash
python app.py
```

### Step 3: Open Main GUI Page

```text
http://127.0.0.1:5000/
```

---

## Login Pages

### Main Page

```text
http://127.0.0.1:5000/
```

### Admin Login

```text
http://127.0.0.1:5000/admin/login
```

### Faculty Login

```text
http://127.0.0.1:5000/faculty/login
```

### Student Login

```text
http://127.0.0.1:5000/student/login
```

---

## Sample Test Accounts

### Admin

```text
Email: admin@namal.edu.pk
Password: hashed_password_123
```

### Faculty

```text
Email: rafay.khan@namal.edu.pk
Password: faculty_hash_456
```

### Student

```text
Email: abdul.rehman01@students.namal.edu.pk
Password: student_hash_789
```

---

## Software Development Methodology

The project follows the **Incremental Software Development Methodology**. The system is developed in multiple stages, where each stage improves a specific part of the project.

### Development Stages

* Requirement gathering and analysis.
* ERD and conceptual database design.
* Logical schema and normalization.
* DDL and DML implementation.
* Backend route development.
* Admin, Faculty, and Student module implementation.
* Views, procedures, functions, and triggers.
* Testing and documentation.

---

## Meeting Minutes Google Sheet Link

```text
https://docs.google.com/spreadsheets/d/1-d0xnH4mQQOcMRUhwZXkGxccYi9RMYkxIe8fBq_9LVo/edit?usp=sharing
```

---

## Figma Design Link

```text
https://www.figma.com/design/N31rKyv6Wrl5IGfSwzfX7F/Abdul-Rehman-s-team-library?node-id=0-1&t=pRAo4BFcGFAE5w5c-1
```

---

## Main GUI Page Link

```text
http://127.0.0.1:5000/
```

---

## Submission Details

* **University:** Namal University, Mianwali
* **Course:** CSC-225: Software Engineering
* **Project Title:** Fair and Unbiased Assessment System

### Team Members

* **Abdul Rehman** — [bscs24f01@namal.edu.pk](mailto:bscs24f01@namal.edu.pk)
* **Ahmad Ali** — [bscs24f02@namal.edu.pk](mailto:bscs24f02@namal.edu.pk)
* **Junaid Gondal** — [bscs24f28@namal.edu.pk](mailto:bscs24f28@namal.edu.pk)
