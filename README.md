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

## Software Engineering Work

This project follows a proper Software Engineering process. The work includes both documentation and implementation.

Main Software Engineering activities include:

- Requirement gathering and analysis
- Software Requirement Specification
- Functional requirements
- Non-functional requirements
- Use case identification
- System diagrams
- UI/UX prototype design
- Database design
- Implementation
- Testing
- Documentation

---

## SRS and Diagrams

The project documentation includes the following Software Engineering artifacts:

- Software Requirement Specification
- Use Case Diagram
- Activity Diagram
- Sequence Diagram
- Class Diagram
- Entity Relationship Diagram
- Enhanced Entity Relationship Diagram
- Relational Schema
- Figma UI Prototype

These artifacts help explain the system requirements, user interaction, database structure, and implementation plan.

---


### Project Planning Context

During the initial Software Engineering planning phase, the project idea focused on AI-based fair assessment. In the current implementation phase, the system focuses on database-backed academic assessment management and prepares the structure for future AI integration.

---

## Database Design Summary

The system uses a normalized MySQL database to manage academic assessment records. The database is designed according to university workflow and supports students, faculty, departments, programs, batches, sections, sessions, courses, enrollments, registered courses, assessments, submissions, and evaluations.

The database design avoids unnecessary redundancy. For example, student section and semester history are stored through enrollment records instead of directly storing current semester or section in the student table.

Important database points:

- `users` stores common login and profile information.
- `student` and `faculty` store role-specific data.
- `batch_program` connects batches with programs.
- `enrollment` stores student academic history.
- `registered_course` stores the courses selected in an enrollment.
- `teacher_assignment` connects faculty, course, section, and semester.
- `assessment` stores session-based assessment portals.
- `submission` stores student uploads.
- `evaluation` stores marks, feedback, percentage, and report metadata.

The database is normalized up to **Third Normal Form (3NF)**.

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



## Stored Procedures

Stored procedures are used for controlled insertion, update, and deletion operations.

### Main Procedures

* `sp_add_student`
* `sp_update_student`
* `sp_delete_student_safe`
* `sp_add_faculty`
* `sp_update_faculty`
* `sp_delete_faculty_safe`

These procedures help keep database operations consistent and prevent invalid data from being inserted or deleted.

---

## Functions

Functions are used for repeated validation checks.

### Main Functions

* `fn_email_exists`
* `fn_registration_exists`
* `fn_course_code_exists`
* `fn_section_available_seats`

These functions help check duplicate emails, duplicate registration numbers, duplicate course codes, available section seats, current academic session, and duplicate active enrollments.

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
