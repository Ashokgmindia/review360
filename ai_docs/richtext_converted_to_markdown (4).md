1\. Class

Represents an academic batch/section.

● College Admin

○ Create / Update / Delete classes

○ Assign teacher, semester, program, section

○ Manage academic year and max\_students

● Teacher

○ View assigned classes

○ Limited updates (room number, schedule)

● Student

○ View their class information

2\. Student

Represents enrolled students.

● College Admin

○ Full CRUD on student profiles

○ Assign department, class, academic year

○ Manage student status (enrolled, graduated, dropped)

● Teacher

○ Upload/import student details of their own class (Excel/CSV)

○ View and update limited academic information of their students

○ Cannot delete student profiles

● Student

○ View and update personal details (email, phone, address, guardian info, profile

photo)

○ Cannot change academic details (class, department, academic year, status)

3\. ImportLog

Tracks bulk imports.

● College Admin

○ Upload/import teacher data (complete college-level import)

○ View all import logs (teachers, students)

● Teacher

○ Upload/import student data for their own class only

○ View logs of their own imports

● Student

○ No access

4\. Department

Represents academic departments.

● College Admin

○ Create / Update / Delete departments

○ Assign Head of Department

● Teacher

○ View department details

○ Update department information if assigned as HoD

● Student

○ View their department information

5\. Subject

Represents academic subjects.

● College Admin

○ Create / Update / Delete subjects

○ Assign subjects to departments and semesters

● Teacher

○ View assigned subjects

○ Upload syllabus files for subjects they handle

● Student

○ View subjects for their class/department

6\. Teacher

Represents faculty members.

● College Admin

○ Create / Update / Delete teacher profiles

○ Bulk import teacher data (Excel/CSV)

○ Assign department, designation, roles, HoD responsibilities

● Teacher

○ Update their own profile (contact details, research, resume)

○ Cannot change department or employee\_id

● Student

○ View teacher information (name, designation, subject handled)

7\. FollowUpSession

Represents student–teacher academic sessions.

● College Admin

○ View all sessions in the college

○ Update or delete sessions if necessary

● Teacher

○ Create follow-up sessions for their students

○ Update session details (status, notes, reschedule)

○ Cancel sessions

● Student

○ View their assigned sessions

○ Request reschedule (if workflow allows)

8\. ActivitySheet

Represents student work (projects, ADOC, DRCV).

● College Admin

○ View all activity sheets

● Teacher

○ View student activity sheets in their classes

○ Update status (in\_progress, completed, validated)

○ Provide grades

● Student

○ Create and update their own activity sheets (before validation)

○ Cannot modify grades or validation

9\. Validation

Represents teacher validation of activity sheets.

● College Admin

○ View all validations

● Teacher

○ Validate assigned student activity sheets

○ Assign grades, comments, and validation flags

● Student

○ View validation results

gi