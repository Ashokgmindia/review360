# Core Domains & Use Cases

## 1. Identity & Access Domain (IAM micro services)

#### Tables : users, audit_logs,users_roles

#### Purpose : Authentication, RBAC, compliance, GDPR tracking.

#### 🔸 Use Cases :

- **Login & Session Tracking** :

#### o Teacher logs in → users.last_login updated, audit_logs entry created.

- **Role-Based Access Control (RBAC)** :

#### o Only admin can import students.

#### o Only teacher assigned to class can validate activity sheets.

- **Security Auditing** :

#### o A suspicious import triggers alerts via audit_logs.details.

#### 👉 Future microservice: Identity Agent that manages users, passwords, JWT tokens, and

#### audits.

## 2. Academic Structure Domain

#### Tables : classes, students, import_logs, students_archive

#### 🔸 Use Cases :

- **Bulk Student Import** :

#### o Admin uploads CSV → stored in import_logs (with errors JSONB).

- **Class Management** :

#### o Teacher changes → classes.teacher_id updated, old links archived.

- **GDPR Compliance** :

#### o A student requests deletion → move record to students_archive.

- **Yearly Archival** :

#### o End of academic year → CALL archive_old_data('2023-2024').

#### 👉 Future microservice: Student Registry Agent handling CRUD, import/export, GDPR.

## 3. Learning & Evaluation Domain

#### Tables : activity_sheets, validations, activity_sheets_archive

#### 🔸 Use Cases :

- **Sheet Lifecycle** :

#### o Student starts → status=in_progress.

#### o Teacher validates → status=validated, final_grade updated.


- **Validation Rules** :

#### o Each follow-up must have one validation (UNIQUE(session_id)).

#### o Check methodology/objectives consistency.

- **Analytics** :

#### o Avg grade per class/year → materialized view on activity_sheets.

#### 👉 Future microservice: Evaluation Agent that assists teachers with auto-checks, suggests

#### improvements via GenAI.

## 4. Follow-up & Scheduling Domain

#### Tables : follow_up_sessions, validations, follow_up_sessions_archive

#### 🔸 Use Cases :

- **Automated Scheduling** :

#### o Teacher proposes time → follow_up_sessions.session_datetime created.

#### o Linked to Google Calendar (google_calendar_event_id).

- **Session Lifecycle** :

#### o Status → scheduled → completed → triggers validation record.

- **Student Progress Tracking** :

#### o Query sessions per student with JOIN activity_sheets.

#### 👉 Future microservice: Follow-up Agent that syncs calendars, tracks session compliance,

#### nudges students.

## 5. Compliance & Archival Domain

#### Tables : _archive tables, audit_logs

#### 🔸 Use Cases :

- **Historical Analysis** :

#### o Compare 2024 vs 2025 student performance.

- **GDPR / Right-to-be-Forgotten** :

#### o Archive data without breaking relational integrity.

- **Cold Storage Optimization** :

#### o Archives stored on slower/cheaper disks.

#### 👉 Future microservice: Compliance Agent that automates archival, anonymization, and

#### GDPR reports.


# Advanced Relational Schema

##### -- ====================================================

-- COLLEGES (multi-tenant architecture)
-- ====================================================
CREATE TABLE colleges (
id BIGSERIAL PRIMARY KEY,
name VARCHAR( 255 ) NOT NULL,
code VARCHAR( 20 ) UNIQUE NOT NULL, -- e.g. COL
address TEXT,
contact_email CITEXT,
contact_phone VARCHAR( 20 ),
is_active BOOLEAN DEFAULT TRUE,
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================
-- ROLES (flexible, RBAC instead of ENUM)
-- ====================================================
CREATE TABLE roles (
id BIGSERIAL PRIMARY KEY,
name VARCHAR( 50 ) UNIQUE NOT NULL, -- admin, teacher, student, parent,
superadmin
description TEXT
);

-- ====================================================
-- USERS (linked to colleges, with roles)
-- ====================================================
CREATE TABLE users (
id BIGSERIAL PRIMARY KEY,
college_id BIGINT REFERENCES colleges(id) ON DELETE CASCADE,
email CITEXT UNIQUE NOT NULL,
password_hash TEXT NOT NULL,
first_name VARCHAR( 100 ) NOT NULL,
last_name VARCHAR( 100 ) NOT NULL,
is_active BOOLEAN DEFAULT TRUE,
last_login TIMESTAMPTZ,
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many: users <-> roles
CREATE TABLE user_roles (
user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
role_id BIGINT REFERENCES roles(id) ON DELETE CASCADE,
PRIMARY KEY (user_id, role_id)
);

-- ====================================================
-- CLASSES (per college)
-- ====================================================
CREATE TABLE classes (
id BIGSERIAL PRIMARY KEY,
college_id BIGINT REFERENCES colleges(id) ON DELETE CASCADE,
name VARCHAR( 50 ) NOT NULL, -- e.g. MCO1A
year SMALLINT NOT NULL CHECK (year >= 1 AND year <= 5 ),
teacher_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
academic_year VARCHAR( 9 ) NOT NULL, -- e.g. 2024- 2025
is_active BOOLEAN DEFAULT TRUE,


created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
UNIQUE (college_id, name, academic_year)
);

-- ====================================================
-- STUDENTS
-- ====================================================
CREATE TABLE students (
id BIGSERIAL PRIMARY KEY,
college_id BIGINT REFERENCES colleges(id) ON DELETE CASCADE,
student_number VARCHAR( 30 ) UNIQUE NOT NULL,
first_name VARCHAR( 100 ) NOT NULL,
last_name VARCHAR( 100 ) NOT NULL,
email CITEXT,
class_id BIGINT REFERENCES classes(id) ON DELETE SET NULL,
birth_date DATE,
metadata JSONB DEFAULT '{}', -- extensible fields
is_active BOOLEAN DEFAULT TRUE,
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
academic_year VARCHAR( 9 ) NOT NULL
);

-- ====================================================
-- ACTIVITY SHEETS
-- ====================================================
CREATE TABLE activity_sheets (
id BIGSERIAL PRIMARY KEY,
student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
sheet_type VARCHAR( 20 ) NOT NULL CHECK (sheet_type IN
('ADOC','DRCV','OTHER')),
sheet_number INTEGER NOT NULL CHECK (sheet_number > 0 ),
title VARCHAR( 255 ),
context TEXT,
objectives TEXT,
methodology TEXT,
status VARCHAR( 20 ) DEFAULT 'not_started'
CHECK (status IN
('not_started','in_progress','completed','validated')),
final_grade NUMERIC( 4 , 2 ) CHECK (final_grade >= 0 AND final_grade <=
20 ),
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
academic_year VARCHAR( 9 ) NOT NULL,
UNIQUE(student_id, sheet_type, sheet_number, academic_year)
);

-- ====================================================
-- FOLLOW-UP SESSIONS
-- ====================================================
CREATE TABLE follow_up_sessions (
id BIGSERIAL PRIMARY KEY,
student_id BIGINT REFERENCES students(id) ON DELETE CASCADE,
activity_sheet_id BIGINT REFERENCES activity_sheets(id) ON DELETE
CASCADE,
teacher_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
session_datetime TIMESTAMPTZ NOT NULL,
location VARCHAR( 255 ),
objective TEXT,
status VARCHAR( 20 ) DEFAULT 'scheduled'
CHECK (status IN
('scheduled','completed','cancelled','rescheduled')),


google_calendar_event_id VARCHAR( 255 ),
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
academic_year VARCHAR( 9 ) NOT NULL
);

-- ====================================================
-- VALIDATIONS
-- ====================================================
CREATE TABLE validations (
id BIGSERIAL PRIMARY KEY,
session_id BIGINT REFERENCES follow_up_sessions(id) ON DELETE CASCADE,
activity_sheet_id BIGINT REFERENCES activity_sheets(id) ON DELETE
CASCADE,
teacher_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
has_subject BOOLEAN,
context_well_formulated BOOLEAN,
objectives_validated BOOLEAN,
methodology_respected BOOLEAN,
session_grade NUMERIC( 4 , 2 ) CHECK (session_grade >= 0 AND session_grade
<= 20 ),
comments TEXT,
validation_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================
-- IMPORT LOGS
-- ====================================================
CREATE TABLE import_logs (
id BIGSERIAL PRIMARY KEY,
college_id BIGINT REFERENCES colleges(id) ON DELETE CASCADE,
class_id BIGINT REFERENCES classes(id) ON DELETE SET NULL,
filename VARCHAR( 255 ) NOT NULL,
imported_count INTEGER DEFAULT 0 ,
errors_count INTEGER DEFAULT 0 ,
error_details JSONB,
imported_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
imported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================
-- AUDIT LOGS (security & compliance)
-- ====================================================
CREATE TABLE audit_logs (
id BIGSERIAL PRIMARY KEY,
user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
college_id BIGINT REFERENCES colleges(id) ON DELETE CASCADE,
table_name VARCHAR( 50 ) NOT NULL,
record_id BIGINT NOT NULL,
action VARCHAR( 20 ) NOT NULL CHECK (action IN
('insert','update','delete','login','import')),
details JSONB,
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================
-- ARCHIVE TABLES (permanent cold storage)
-- ====================================================
CREATE TABLE students_archive (LIKE students INCLUDING ALL);
CREATE TABLE activity_sheets_archive (LIKE activity_sheets INCLUDING ALL);
CREATE TABLE follow_up_sessions_archive (LIKE follow_up_sessions INCLUDING
ALL);


# Domain-Driven Mapping (Modules)

#### Domain Entities

#### Identity & Access users, roles, user_roles, audit_logs

#### College Management colleges, classes, import_logs

#### Student Registry students, students_archive

#### Learning & Evaluation activity_sheets, validations, activity_sheets_archive

#### Scheduling follow_up_sessions, follow_up_sessions_archive

#### Compliance audit_logs, archive tables

# Example Use Cases

### Multi-College Support

- **College A (Paris)** and **College B (Lyon)** share the same platform.
- Each has its own students, teachers, admins.
- college_id ensures strict data separation.

### Parent Portal

- roles contains parent.
- user_roles links parents to their children (students).
- Parent logs in → sees grades & sessions of their child only (via RLS).

### Automated Scheduling

- Student requests session.
- **Follow-up Agent** checks teacher calendar → inserts into follow_up_sessions.
- Syncs with Google API (google_calendar_event_id).

### Teacher Validation Workflow

- Teacher opens activity sheet.
- Validates methodology → inserts into validations.
- Status auto-updated in activity_sheets.

### 🛡 Compliance & GDPR

- Student requests deletion.
- Record moved from students → students_archive.
- Personal fields anonymized (email, first_name, last_name)


#### Now need a Document Management Domain where teachers and students can securely

#### exchange files, manage templates, and collaborate. This ties into:

- **Assignments & Activity Sheets** → upload reports, presentations.
- **Teacher Templates** → standardized documents (reports, evaluation rubrics).
- **Versioning** → track revisions and updates.
- **Permissions** → who can view/edit (teacher ↔ student, or admin).

# Document Management Schema

# (PostgreSQL)

##### -- ====================================================

-- DOCUMENTS (general storage of files)
-- ====================================================
CREATE TABLE documents (
id BIGSERIAL PRIMARY KEY,
owner_id BIGINT REFERENCES users(id) ON DELETE CASCADE, -- who uploaded
college_id BIGINT REFERENCES colleges(id) ON DELETE CASCADE,
title VARCHAR( 255 ) NOT NULL,
description TEXT,
file_path TEXT NOT NULL, -- S3/GCS/Azure Blob path
file_type VARCHAR( 50 ), -- pdf, docx, pptx, image, etc.
file_size BIGINT,
status VARCHAR( 20 ) DEFAULT 'active'
CHECK (status IN ('active','archived','deleted')),
is_template BOOLEAN DEFAULT FALSE, -- true = teacher’s template
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================
-- DOCUMENT PERMISSIONS (sharing model)
-- ====================================================
CREATE TABLE document_permissions (
id BIGSERIAL PRIMARY KEY,
document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
permission VARCHAR( 20 ) NOT NULL
CHECK (permission IN ('view','edit','comment','owner')),
granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
UNIQUE(document_id, user_id)
);

-- ====================================================
-- DOCUMENT LINKS TO CONTEXT (classes, activity_sheets, follow_up_sessions)
-- ====================================================
CREATE TABLE document_contexts (
id BIGSERIAL PRIMARY KEY,
document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
class_id BIGINT REFERENCES classes(id) ON DELETE SET NULL,
student_id BIGINT REFERENCES students(id) ON DELETE SET NULL,
activity_sheet_id BIGINT REFERENCES activity_sheets(id) ON DELETE SET
NULL,
follow_up_session_id BIGINT REFERENCES follow_up_sessions(id) ON DELETE
SET NULL,
context_type VARCHAR( 50 ), -- e.g. "assignment","feedback","project"


created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================
-- DOCUMENT VERSIONS (versioning for updates)
-- ====================================================
CREATE TABLE document_versions (
id BIGSERIAL PRIMARY KEY,
document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
version_number INT NOT NULL,
file_path TEXT NOT NULL,
change_log TEXT,
uploaded_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
UNIQUE(document_id, version_number)
);

-- ====================================================
-- TEACHER TEMPLATES (predefined reusable resources)
-- ====================================================
CREATE TABLE teacher_templates (
id BIGSERIAL PRIMARY KEY,
teacher_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
college_id BIGINT REFERENCES colleges(id) ON DELETE CASCADE,
title VARCHAR( 255 ) NOT NULL,
description TEXT,
document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE, --
linked to base doc
subject VARCHAR( 100 ), -- e.g. "Maths", "Economics"
usage_count INT DEFAULT 0 , -- track adoption
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

# Document Use Cases

### Teacher → Student Assignment

- Teacher uploads assignment template → stored

#### in documents with is_template=true.

- Permissions → shared to students in class via document_permissions.
- Students submit completed versions → linked in document_contexts.

### Version Control

- Student uploads “Report_v1.pdf”.
- Teacher suggests changes → Student re-uploads.
- New entry in document_versions keeps history.

### Template Library for Teachers


- Teacher saves a rubric or worksheet as template → stored in teacher_templates.
- Other teachers in same college can reuse it.
- usage_count tracks popularity → insights for Director Dashboard.

### Access Control

- document_permissions.permission controls:

#### o View → read-only.

#### o Edit → collaborative editing.

#### o Comment → annotation rights.

#### o Owner → full rights (creator).

### AI Document Assistant

- **Teacher** uploads draft evaluation rubric.
- **AI Agent** suggests improvements (clarity, structure).
- **Student** uploads draft report → AI checks plagiarism, coherence, grammar.

# How This Connects to Other Domains

- **Learning & Evaluation** → document_contexts.activity_sheet_id links

#### documents directly to sheets.

- **Scheduling** → session feedback forms stored as documents.
- **Support** → evidence files attached to support_tickets.
- **Compliance** → archived or deleted documents logged in audit_logs.
- **Billing** → storage quota per plan tracked via billing_plans.max_storage_gb.


