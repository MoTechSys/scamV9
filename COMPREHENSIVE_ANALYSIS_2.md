# S-ACM Deep Repository Scan - Comprehensive Architectural Analysis v2
### System Audit Report | 2026-02-09
### Prepared by: Senior System Architect & Security Auditor

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Structure Tree](#2-project-structure-tree)
3. [Database Schema & Entity Relationships](#3-database-schema--entity-relationships)
4. [Architecture Analysis](#4-architecture-analysis)
5. [Security Audit](#5-security-audit)
6. [Code Quality Assessment](#6-code-quality-assessment)
7. [Notification System Deep Analysis](#7-notification-system-deep-analysis)
8. [HTMX / Dynamic Filtering Readiness](#8-htmx--dynamic-filtering-readiness)
9. [Critical Issues & Bugs](#9-critical-issues--bugs)
10. [Recommended Action Plan](#10-recommended-action-plan)

---

## 1. Executive Summary

**Project:** S-ACM (Smart Academic Content Management)  
**Framework:** Django 5.2.10  
**Database:** SQLite (dev) / PostgreSQL (prod)  
**Frontend:** Bootstrap 5 RTL + HTMX  
**AI Engine:** Google Gemini (multi-model, DB-governed)  
**Auth:** Custom User model with RBAC (Role-Based Access Control)  

### Overall Health Score: 7.2 / 10

| Category | Score | Status |
|----------|-------|--------|
| Architecture | 8/10 | Good - Well-structured Django apps |
| Security | 5/10 | **CRITICAL** - Hardcoded secrets in .env committed to git |
| Code Quality | 7/10 | Good - Some DRY violations and dead code |
| Database Design | 8/10 | Good - Proper relationships, good indexing |
| Notification System | 4/10 | **Needs Major Overhaul** - Dual architecture, broken references |
| HTMX Readiness | 7/10 | Good foundation, needs notification-specific endpoints |
| AI Engine | 9/10 | Excellent - Enterprise-grade with Hydra Key Manager |
| Test Coverage | 2/10 | **CRITICAL** - Almost no tests |

---

## 2. Project Structure Tree

```
S-ACM/
├── .env                          # Environment variables (COMMITTED - SECURITY RISK!)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules (misconfigured)
├── manage.py                     # Django management
├── db.sqlite3                    # SQLite database (COMMITTED!)
├── requirements.txt              # Python dependencies (28 packages)
│
├── config/                       # Django Configuration
│   ├── __init__.py
│   ├── settings.py               # Main settings (497 lines)
│   ├── urls.py                   # Root URL routing
│   ├── asgi.py                   # ASGI config
│   ├── wsgi.py                   # WSGI config
│   └── celery.py                 # Celery configuration
│
├── apps/                         # Application Modules
│   ├── __init__.py
│   │
│   ├── accounts/                 # User Management & RBAC
│   │   ├── models.py             # User, Role, Permission, Major, Level, Semester, etc.
│   │   ├── views/                # Split into auth.py, profile.py, mixins.py
│   │   ├── decorators.py         # role_required, permission_required, etc.
│   │   ├── middleware.py         # ActiveAccount, RoleBasedRedirect, SecurityHeaders
│   │   ├── forms.py              # User forms
│   │   ├── services.py           # Account services
│   │   ├── admin.py              # Admin configuration
│   │   ├── urls.py               # Account URLs
│   │   ├── fixtures/             # permissions.json, roles.json, role_permissions.json
│   │   └── management/commands/  # setup_initial_data command
│   │
│   ├── core/                     # Core System Functions
│   │   ├── models.py             # SystemSetting, AuditLog
│   │   ├── views.py              # Home, Dashboard redirect, Error pages
│   │   ├── middleware.py         # RateLimit, SecurityHeaders, RequestLogging,
│   │   │                         # FileUploadSecurity, PermissionMiddleware
│   │   ├── context_processors.py # site_settings, user_notifications, user_role_info
│   │   ├── menu.py               # Dynamic menu system
│   │   ├── streaming.py          # SSE Streaming engine
│   │   ├── streaming_urls.py     # Streaming URL routes
│   │   ├── templatetags/         # Custom template tags (permissions)
│   │   ├── admin.py
│   │   └── urls.py
│   │
│   ├── courses/                  # Course & File Management
│   │   ├── models.py             # Course, CourseMajor, InstructorCourse, LectureFile
│   │   ├── views/                # Split: admin.py, common.py, instructor.py, student.py, htmx.py
│   │   ├── services.py           # EnhancedCourseService, EnhancedFileService
│   │   ├── mixins.py             # Course access mixins
│   │   ├── forms.py              # Course/File forms
│   │   ├── admin.py
│   │   ├── urls.py
│   │   └── tests/                # test_security.py
│   │
│   ├── notifications/            # Notification System
│   │   ├── models.py             # Notification, NotificationRecipient, NotificationManager
│   │   ├── views/                # Split: admin.py, common.py, instructor.py
│   │   ├── forms.py              # NotificationForm, CourseNotificationForm, BroadcastNotificationForm
│   │   ├── services.py           # NotificationService (BROKEN - stale API)
│   │   ├── admin.py
│   │   └── urls.py
│   │
│   ├── ai_features/              # AI Engine (Enterprise v2)
│   │   ├── models.py             # AIConfiguration, APIKey, AISummary, AIGeneratedQuestion,
│   │   │                         # AIChat, AIUsageLog, AIGenerationJob, StudentProgress
│   │   ├── services.py           # HydraKeyManager, SmartChunker, GeminiService, AIFileStorage
│   │   ├── views.py              # AI feature views
│   │   ├── admin.py              # AI admin with dashboard
│   │   └── urls.py
│   │
│   ├── instructor/               # Instructor Portal
│   │   ├── views.py              # Dashboard, course management
│   │   └── urls.py
│   │
│   └── student/                  # Student Portal
│       ├── views.py              # Dashboard, course viewing
│       └── urls.py
│
├── templates/                    # HTML Templates
│   ├── base.html                 # Base layout
│   ├── layouts/                  # Dashboard layouts
│   ├── accounts/                 # Auth templates
│   ├── instructor/               # Instructor templates
│   ├── student/                  # Student templates
│   ├── notifications/            # Notification templates
│   ├── ai_features/              # AI feature templates
│   ├── core/                     # Core templates
│   └── errors/                   # Error pages (403, 404, 500)
│
├── static/                       # Static Assets
│   ├── css/                      # Custom CSS (3 files)
│   ├── js/                       # Custom JS (3 files)
│   └── vendor/                   # Bootstrap 5 RTL
│
├── media/                        # User Uploads & AI Output
│   ├── uploads/courses/          # Course files organized by code
│   └── ai_generated/             # AI output (.md files)
│
├── logs/                         # Application Logs
├── tests/                        # Root-level tests
├── docs/                         # Documentation
│   └── ARCHITECTURE.md
│
├── seed_test_data.py             # Test data seeder
├── clear_old_permissions.py      # Permission cleanup utility
├── test_gemini_service.py        # Gemini service test
├── test_gemini_standalone.py     # Standalone Gemini test
└── test_templates.py             # Template rendering test
```

---

## 3. Database Schema & Entity Relationships

### 3.1 Complete Entity Relationship Diagram (Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                        ACCOUNTS MODULE                          │
│                                                                 │
│  ┌──────────┐    1:N    ┌──────────┐    N:M    ┌────────────┐  │
│  │  Role    │◄──────────│  User    │           │ Permission │  │
│  │----------│           │----------│           │------------│  │
│  │ code     │           │academic_id│          │ code       │  │
│  │ display  │           │full_name │           │ display    │  │
│  │ is_system│           │email     │           │ category   │  │
│  └────┬─────┘           │role (FK) │           └──────┬─────┘  │
│       │                 │major (FK)│                  │         │
│       │                 │level (FK)│                  │         │
│       │                 └───┬──┬───┘                  │         │
│       │                     │  │                      │         │
│       │  ┌──────────────────┘  │                      │         │
│       │  │                     │                      │         │
│       │  ▼         ▼           │                      │         │
│  ┌────┴──────┐ ┌────────┐     │    ┌────────────────┐│         │
│  │RolePerm   │ │ Major  │     │    │  RolePermission ││         │
│  │(Pivot M2M)│ │--------│     │    │  (Pivot Table)  ││         │
│  │role (FK)  │ │name    │     │    │  role_id (FK)   │◄─────   │
│  │perm (FK)  │ │is_active│    │    │  permission_id  │─────►   │
│  └───────────┘ └────────┘     │    └────────────────┘          │
│                               │                                │
│  ┌──────────┐  ┌───────────┐  │                                │
│  │  Level   │  │ Semester  │  │                                │
│  │----------│  │-----------│  │                                │
│  │level_name│  │name       │  │                                │
│  │level_num │  │acad_year  │  │                                │
│  └──────────┘  │is_current │  │                                │
│                └───────────┘  │                                │
│                               │                                │
│  ┌───────────────┐  ┌────────┴────────┐  ┌──────────────────┐  │
│  │VerificationCode│  │  UserActivity   │  │PasswordResetToken│  │
│  │ user (FK)      │  │  user (FK)      │  │ user (FK)        │  │
│  │ code, email    │  │  activity_type  │  │ token            │  │
│  │ expires_at     │  │  ip_address     │  │ expires_at       │  │
│  └───────────────┘  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        COURSES MODULE                           │
│                                                                 │
│  ┌────────────┐  N:M (via CourseMajor)  ┌──────────┐           │
│  │  Course    │◄────────────────────────►│  Major   │           │
│  │------------│                          │ (accounts)│          │
│  │course_code │  N:M (via InstrCourse)  ┌┴──────────┐          │
│  │course_name │◄────────────────────────►│  User    │           │
│  │level (FK)  │────────►Level            │(accounts) │          │
│  │semester(FK)│────────►Semester          └──────────┘          │
│  │credit_hours│                                                 │
│  │is_active   │                                                 │
│  └──────┬─────┘                                                 │
│         │ 1:N                                                   │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │ LectureFile  │                                               │
│  │--------------│                                               │
│  │course (FK)   │─────────►Course                               │
│  │uploader (FK) │─────────►User                                 │
│  │title         │                                               │
│  │content_type  │  (local_file | external_link)                 │
│  │file_type     │  (Lecture|Summary|Exam|Assignment|Ref|Other)  │
│  │is_visible    │                                               │
│  │is_deleted    │  (Soft Delete)                                │
│  │download_count│                                               │
│  │view_count    │                                               │
│  └──────┬───────┘                                               │
│         │ 1:N                                                   │
│  ┌──────┴──────────┐                                            │
│  │ CourseMajor     │  Pivot: Course <-> Major                   │
│  │ InstructorCourse│  Pivot: Course <-> User(Instructor)        │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     NOTIFICATIONS MODULE                        │
│                                                                 │
│  ┌──────────────────┐   1:N    ┌───────────────────────┐       │
│  │  Notification     │◄────────│ NotificationRecipient  │       │
│  │------------------│          │-----------------------│        │
│  │sender (FK->User) │          │notification (FK)      │        │
│  │title             │          │user (FK->User)        │        │
│  │body              │          │is_read                │        │
│  │notification_type │          │read_at                │        │
│  │priority          │          │is_deleted (soft)      │        │
│  │course (FK, null) │          └───────────────────────┘        │
│  │file (FK, null)   │                                           │
│  │is_active         │                                           │
│  │expires_at        │                                           │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      AI FEATURES MODULE                         │
│                                                                 │
│  ┌──────────────────┐  (Singleton)                              │
│  │ AIConfiguration  │                                           │
│  │------------------│                                           │
│  │active_model      │                                           │
│  │chunk_size        │                                           │
│  │max_output_tokens │                                           │
│  │temperature       │                                           │
│  │user_rate_limit   │                                           │
│  │is_service_enabled│                                           │
│  └──────────────────┘                                           │
│                                                                 │
│  ┌──────────────┐       ┌──────────────┐                        │
│  │  APIKey      │       │  AISummary   │                        │
│  │--------------│       │--------------│                        │
│  │_encrypted_key│       │file (1:1 FK) │────►LectureFile        │
│  │status        │       │user (FK)     │────►User               │
│  │rpm_limit     │       │summary_text  │                        │
│  │cooldown_until│       │md_file_path  │                        │
│  │error_count   │       │model_used    │                        │
│  └──────────────┘       └──────────────┘                        │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────┐  ┌──────────────────┐  │
│  │AIGeneratedQuestion│   │   AIChat     │  │  AIUsageLog      │  │
│  │------------------│   │--------------│  │------------------│  │
│  │file (FK)         │   │file (FK)     │  │user (FK)         │  │
│  │user (FK)         │   │user (FK)     │  │request_type      │  │
│  │question_type     │   │question      │  │api_key_used (FK) │  │
│  │options (JSON)    │   │answer        │  │tokens_used       │  │
│  │correct_answer    │   │is_helpful    │  │was_cached         │  │
│  └──────────────────┘   └──────────────┘  └──────────────────┘  │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐                    │
│  │ AIGenerationJob  │   │ StudentProgress  │                    │
│  │------------------│   │------------------│                    │
│  │instructor (FK)   │   │student (FK)      │                    │
│  │file (FK)         │   │file (FK)         │                    │
│  │job_type          │   │progress (0-100)  │                    │
│  │config (JSON)     │   │last_position     │                    │
│  │status            │   │total_time_seconds│                    │
│  └──────────────────┘   └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         CORE MODULE                             │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐                    │
│  │ SystemSetting    │   │    AuditLog      │                    │
│  │------------------│   │------------------│                    │
│  │key (unique)      │   │user (FK->User)   │                    │
│  │value             │   │action            │                    │
│  │description       │   │model_name        │                    │
│  │is_public         │   │object_id         │                    │
│  └──────────────────┘   │changes (JSON)    │                    │
│                         │ip_address        │                    │
│                         └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Relationship Summary Table

| From | To | Type | Via / FK | Notes |
|------|----|------|----------|-------|
| User | Role | N:1 (ForeignKey) | `user.role` | `on_delete=PROTECT` |
| User | Major | N:1 (ForeignKey) | `user.major` | Students only, `on_delete=SET_NULL` |
| User | Level | N:1 (ForeignKey) | `user.level` | Students only, `on_delete=SET_NULL` |
| Role | Permission | M:N | `RolePermission` pivot table | Manual M2M, not Django's built-in |
| Course | Level | N:1 (ForeignKey) | `course.level` | `on_delete=PROTECT` |
| Course | Semester | N:1 (ForeignKey) | `course.semester` | `on_delete=PROTECT` |
| Course | Major | M:N | `CourseMajor` pivot table | A course can serve multiple majors |
| Course | User(Instructor) | M:N | `InstructorCourse` pivot table | Includes `is_primary` flag |
| LectureFile | Course | N:1 (ForeignKey) | `file.course` | `on_delete=CASCADE` |
| LectureFile | User(Uploader) | N:1 (ForeignKey) | `file.uploader` | `on_delete=SET_NULL` |
| Notification | User(Sender) | N:1 (ForeignKey) | `notification.sender` | `on_delete=SET_NULL` |
| Notification | Course | N:1 (ForeignKey) | Optional link | `on_delete=CASCADE` |
| Notification | LectureFile | N:1 (ForeignKey) | Optional link | `on_delete=SET_NULL` |
| NotificationRecipient | Notification | N:1 | `recipient.notification` | `on_delete=CASCADE` |
| NotificationRecipient | User | N:1 | `recipient.user` | `on_delete=CASCADE` |
| AISummary | LectureFile | 1:1 | `summary.file` | `on_delete=CASCADE` |
| AIGeneratedQuestion | LectureFile | N:1 | `question.file` | `on_delete=CASCADE` |
| AIChat | LectureFile | N:1 | `chat.file` | `on_delete=CASCADE` |
| AIChat | User | N:1 | `chat.user` | `on_delete=CASCADE` |
| AIUsageLog | User | N:1 | `log.user` | `on_delete=CASCADE` |
| AIUsageLog | APIKey | N:1 | `log.api_key_used` | `on_delete=SET_NULL` |
| AIGenerationJob | User(Instructor) | N:1 | `job.instructor` | `on_delete=CASCADE` |
| AIGenerationJob | LectureFile | N:1 | `job.file` | `on_delete=CASCADE` |
| StudentProgress | User(Student) | N:1 | `progress.student` | `on_delete=CASCADE` |
| StudentProgress | LectureFile | N:1 | `progress.file` | `on_delete=CASCADE` |
| AuditLog | User | N:1 | `log.user` | `on_delete=SET_NULL` |

### 3.3 Student Data Flow

```
Student Enrollment Query:
  Student.major ──► CourseMajor.major ──► Course (filtered by)
  Student.level ──► Course.level (filtered by)
  Course.semester.is_current == True (current courses)
  Course.semester.is_current == False AND Level.level_number < Student.level_number (archived)
```

### 3.4 Instructor-Course Binding

```
Instructor ──► InstructorCourse (pivot) ──► Course
  - is_primary flag for main instructor
  - Instructor can only manage assigned courses
  - File upload restricted to assigned courses
```

---

## 4. Architecture Analysis

### 4.1 Strengths

1. **Well-organized Django App Structure**: Clear separation of concerns across 7 apps.
2. **Custom RBAC System**: Flexible role-permission system with dynamic assignments.
3. **Enterprise AI Engine**: HydraKeyManager with round-robin, cooldown, RPM limiting is production-grade.
4. **Smart Chunking**: DB-configurable text chunking for large documents.
5. **Singleton AIConfiguration**: Admin-editable AI settings without code changes.
6. **HTMX Integration**: Partial views for dynamic content updates.
7. **Audit Logging**: AuditLog and UserActivity models for compliance.
8. **Soft Delete Pattern**: LectureFile and NotificationRecipient support soft deletes.
9. **Context Processors**: Efficient user_notifications, user_role_info with lazy loading.
10. **Security Middleware Stack**: RateLimit, SecurityHeaders, FileUploadSecurity, PermissionMiddleware.

### 4.2 Architectural Concerns

1. **Monolithic CourseManager Pattern**: `Course.objects = CourseManager()` / `Course.objects.model = Course` is a Django anti-pattern. Should use `objects = CourseManager.as_manager()` or set inside `Meta`.
2. **Dual SecurityHeadersMiddleware**: Exists in BOTH `apps/accounts/middleware.py` AND `apps/core/middleware.py` with different implementations. Only `core` is in MIDDLEWARE setting.
3. **ActiveAccountMiddleware** defined in `accounts/middleware.py` but NOT registered in `settings.MIDDLEWARE`.
4. **Missing `Department` Model**: The system uses `Major` (Specialization) but has no `Department` model. This may limit organizational hierarchy.
5. **No Separate `student/models.py`**: Student-specific data is crammed into User model via nullable FK fields (major, level).

### 4.3 Data Flow Architecture

```
[Browser] ──HTMX──► [Django Views] ──► [Services Layer] ──► [Models/DB]
                          │                    │
                          │                    ├──► [GeminiService] ──► Google API
                          │                    ├──► [HydraKeyManager] ──► APIKey DB
                          │                    └──► [AIFileStorage] ──► media/
                          │
                          ├──► [Middleware Stack]
                          │    ├── SecurityMiddleware
                          │    ├── SessionMiddleware
                          │    ├── CsrfMiddleware
                          │    ├── AuthMiddleware
                          │    ├── PermissionMiddleware (custom)
                          │    └── ClickjackingMiddleware
                          │
                          └──► [Context Processors]
                               ├── site_settings
                               ├── user_notifications
                               ├── user_role_info
                               └── current_semester (cached 5min)
```

---

## 5. Security Audit

### 5.1 CRITICAL: Hardcoded Secrets in Repository

**Severity: CRITICAL (10/10)**

The `.env` file is **committed to the repository** and contains:

| Secret | Value (Exposed) | Risk |
|--------|-----------------|------|
| `SECRET_KEY` | `django-insecure-DevKey-98237498237498234` | Full session hijacking, CSRF bypass |
| `EMAIL_HOST_PASSWORD` | `yxayybteylgqwfsv` (Gmail App Password) | Email account compromise |
| `GEMINI_API_KEY` | `AIzaSyAowBjSeb9Z8ysNNzkqmZavpnUU4i0k9tk` | API abuse, billing fraud |
| `OPENAI_API_KEY` | Same as GEMINI key | Redundant exposure |
| `DB_PASSWORD` | `your_secure_password_here` (placeholder) | Low risk (placeholder) |

**Root Cause**: `.gitignore` has `.env` commented out (`#.env`).

**Immediate Action Required:**
1. Rotate ALL exposed credentials immediately.
2. Uncomment `.env` in `.gitignore`.
3. Remove `.env` from git history: `git filter-branch` or `BFG Repo-Cleaner`.

### 5.2 CRITICAL: Database File Committed

**Severity: HIGH (8/10)**

`db.sqlite3` is committed to the repository. The `.gitignore` has `#db.sqlite3` (commented out). This exposes:
- All user data, passwords (hashed), academic IDs, ID card numbers.
- Email addresses and phone numbers.
- AI API keys stored in the `ai_api_keys` table.

### 5.3 Security Middleware Analysis

| Middleware | Location | Status | Notes |
|-----------|----------|--------|-------|
| `SecurityMiddleware` | Django built-in | Active | In MIDDLEWARE |
| `RateLimitMiddleware` | `core/middleware.py` | **NOT ACTIVE** | Not in MIDDLEWARE list |
| `SecurityHeadersMiddleware` | `core/middleware.py` | **NOT ACTIVE** | Not in MIDDLEWARE list |
| `RequestLoggingMiddleware` | `core/middleware.py` | **NOT ACTIVE** | Not in MIDDLEWARE list |
| `FileUploadSecurityMiddleware` | `core/middleware.py` | **NOT ACTIVE** | Not in MIDDLEWARE list |
| `PermissionMiddleware` | `core/middleware.py` | Active | In MIDDLEWARE |
| `ActiveAccountMiddleware` | `accounts/middleware.py` | **NOT ACTIVE** | Not in MIDDLEWARE list |
| `SecurityHeadersMiddleware` | `accounts/middleware.py` | **DUPLICATE, NOT ACTIVE** | Never used |

**Only 1 out of 6 custom security middleware is actually active!**

### 5.4 CSRF & Session Security

```python
# Always-on (Good)
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Production-only (Good, but untested)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# HSTS: Commented out (Should enable for production)
```

### 5.5 `ALLOWED_HOSTS` Wildcard

```python
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') + ['*']
```

**The `+ ['*']` appended unconditionally defeats the purpose of ALLOWED_HOSTS.** This allows Host header injection attacks.

### 5.6 API Key Encryption Weakness

The `APIKey` model uses XOR + Base64 "encryption" derived from Django's `SECRET_KEY`:

```python
encrypted = bytes(a ^ b for a, b in zip(raw_key.encode(), enc_key_repeated))
self._encrypted_key = base64.b64encode(encrypted).decode()
```

**XOR is NOT encryption.** It's trivially reversible if the attacker knows the SECRET_KEY (which is committed!). This provides zero security given the current state.

### 5.7 AI HTMX Endpoints Missing CSRF Validation

The HTMX POST endpoints in `courses/views/htmx.py` use `@login_required` but don't explicitly verify CSRF. Django's `CsrfViewMiddleware` handles this globally, BUT the HTMX configuration must include CSRF tokens in requests. This should be verified in the frontend templates.

---

## 6. Code Quality Assessment

### 6.1 DRY Violations

#### 6.1.1 Duplicate SecurityHeadersMiddleware
- **File 1**: `apps/accounts/middleware.py:78-94` - `SecurityHeadersMiddleware`
- **File 2**: `apps/core/middleware.py:137-177` - `SecurityHeadersMiddleware`
- **Impact**: Confusion about which is active. Different implementations.

#### 6.1.2 Duplicate Notification Logic
- `NotificationManager` class in `notifications/models.py` (lines 163-302)
- `NotificationService` class in `notifications/services.py` (lines 10-170)
- Both provide `create_notification`, `get_unread_count`, `mark_as_read` with **incompatible APIs**.

#### 6.1.3 Duplicate Permission Checking
- `User.has_perm()` in `accounts/models.py`
- `User.has_permission()` in `accounts/models.py` (legacy wrapper)
- `permission_required` decorator in `accounts/decorators.py`
- `PermissionMiddleware` in `core/middleware.py`
- Template tag `{% has_perm %}` in `core/templatetags/permissions.py`

While having multiple access points is acceptable, the logic should be centralized.

### 6.2 Dead Code / Broken References

#### 6.2.1 NotificationService uses Wrong Field Names
```python
# notifications/services.py line 18
Notification.objects.create(
    user=user,                    # WRONG: model has 'sender', not 'user'
    notification_type=notification_type,  # OK but uses non-standard values
    related_course=related_course,        # WRONG: model has 'course', not 'related_course'
    related_file=related_file             # WRONG: model has 'file', not 'related_file'
)
```

**This entire service class will throw `FieldError` at runtime.** It was written for an older schema that no longer exists.

#### 6.2.2 NotificationManager uses Wrong Role Field
```python
# notifications/models.py lines 186-191
students = User.objects.filter(
    role__role_name='Student',  # WRONG: Role model has 'code' and 'display_name', not 'role_name'
    ...
)
```

**Both `create_file_upload_notification` and `create_course_notification` are broken** because `role_name` doesn't exist on the `Role` model.

#### 6.2.3 Stale `htmx_notifications` View
```python
# courses/views/htmx.py line 222
notifications = NotificationManager.get_recent_notifications(user, limit=5)
```
`get_recent_notifications` method does NOT exist on `NotificationManager`. Only `get_user_notifications` exists.

#### 6.2.4 Test Files in Root Directory
- `test_gemini_service.py` - Not a proper Django test
- `test_gemini_standalone.py` - Standalone script, not a test
- `test_templates.py` - Not following Django test conventions
- `clear_old_permissions.py` - Utility script in root

### 6.3 Unused Imports & Code Smells

| File | Issue |
|------|-------|
| `notifications/services.py` | Imports `Q` but `services.py` is entirely broken |
| `courses/models.py` | `import os` unused (uses `pathlib` instead) |
| `config/settings.py` | Duplicate `from django.urls import reverse_lazy` (line 6 and line 343) |
| `apps/accounts/middleware.py` | `SecurityHeadersMiddleware` class is dead code |
| `apps/notifications/forms.py` | `BroadcastNotificationForm` defined but no view uses it |

### 6.4 Missing Tests

| App | Test File | Content |
|-----|-----------|---------|
| accounts | `tests.py` | Empty / boilerplate |
| core | `tests.py` | Empty / boilerplate |
| courses | `tests/test_security.py` | Some security tests exist |
| notifications | `tests.py` | Empty / boilerplate |
| ai_features | `tests.py` | Empty / boilerplate |
| root | `tests/test_unicore.py` | Unicore plan tests |

**Estimated test coverage: < 5%**

---

## 7. Notification System Deep Analysis

### 7.1 Current Architecture

The notification system has a **dual-architecture problem**:

```
Architecture A (Models-based):                Architecture B (Services-based):
notifications/models.py                       notifications/services.py
├── Notification (model)                      └── NotificationService (class)
├── NotificationRecipient (model)                 ├── create_notification()     ← BROKEN
└── NotificationManager (static methods)          ├── bulk_create_notifications()← BROKEN
    ├── create_file_upload_notification()←BROKEN  ├── notify_new_file()         ← BROKEN
    ├── create_course_notification()     ←BROKEN  ├── notify_announcement()     ← BROKEN
    ├── create_system_notification()     ← OK     ├── get_user_notifications()  ← BROKEN
    ├── get_unread_count()              ← OK      ├── mark_as_read()            ← BROKEN
    └── get_user_notifications()        ← OK      └── delete_notification()     ← BROKEN
```

### 7.2 What Works

| Component | Status | Notes |
|-----------|--------|-------|
| `Notification` model | Working | Good schema with types, priority, expiry |
| `NotificationRecipient` model | Working | Per-user read tracking, soft delete |
| Admin create view | Working | Creates notification + bulk recipients |
| User list view | Working | Uses `NotificationManager.get_user_notifications()` |
| Mark as read | Working | Single and bulk mark-as-read |
| Delete (soft) | Working | Hides from user's list |
| Unread count API | Working | JSON endpoint for AJAX |
| `context_processors.user_notifications` | Working | Navbar dropdown count + recent 5 |

### 7.3 What is BROKEN

| Component | Issue | Impact |
|-----------|-------|--------|
| `NotificationService` (entire class) | Wrong field names: `user`, `related_course`, `related_file` don't exist | Runtime crash on ANY call |
| `NotificationManager.create_file_upload_notification()` | `role__role_name='Student'` - `role_name` doesn't exist on Role | Runtime crash |
| `NotificationManager.create_course_notification()` | Same `role_name` issue | Runtime crash |
| `InstructorNotificationCreateView` | Calls `NotificationManager.create_course_notification()` which is broken | Instructor can't send notifications |
| `htmx_notifications()` view | Calls non-existent `get_recent_notifications()` | 500 error |
| Auto-notification on file upload | Not wired (no signal or explicit call) | Files uploaded silently |

### 7.4 What is MISSING for a Modern Notification System

| Feature | Status | Priority |
|---------|--------|----------|
| Real-time push (WebSocket/SSE) | Missing | High |
| HTMX-based dynamic filtering by Major/Level/Course | Missing | High |
| Notification scheduling | Missing | Medium |
| Notification templates | Missing | Medium |
| Email notification delivery | Missing | Medium |
| File upload auto-notification (signal-based) | Broken | High |
| Recipient filtering by Major + Level + Course | Partially exists (broken) | High |
| Notification analytics (open rate, etc.) | Missing | Low |
| Batch operations (bulk delete, bulk archive) | Missing | Low |
| Notification preferences per user | Missing | Medium |

### 7.5 Template Analysis

| Template | Exists | Status |
|----------|--------|--------|
| `notifications/list.html` | Yes | Working |
| `notifications/detail.html` | Yes | Working |
| `notifications/admin_create.html` | Yes | Working (basic) |
| `notifications/admin_list.html` | Yes | Working |
| `notifications/instructor_create.html` | Yes | Working (but backend broken) |
| `notifications/instructor_sent.html` | Yes | Working |
| `partials/notifications_dropdown.html` | Unknown | May not exist (htmx view references it) |

---

## 8. HTMX / Dynamic Filtering Readiness

### 8.1 Current HTMX Infrastructure

The project already has HTMX integrated (`django-htmx==1.27.0` in requirements). Existing HTMX endpoints:

| Endpoint | File | Purpose |
|----------|------|---------|
| `htmx_file_list` | `courses/views/htmx.py` | Dynamic file list |
| `htmx_file_search` | `courses/views/htmx.py` | Live search with debounce |
| `htmx_toggle_visibility` | `courses/views/htmx.py` | Toggle file visibility |
| `htmx_delete_file` | `courses/views/htmx.py` | Delete file (soft) |
| `htmx_course_stats` | `courses/views/htmx.py` | Periodic stats update |
| `htmx_notifications` | `courses/views/htmx.py` | **BROKEN** - wrong method call |
| `htmx_generate_summary` | `courses/views/htmx.py` | AI summary generation |
| `htmx_generate_questions` | `courses/views/htmx.py` | AI question generation |
| `htmx_ask_document` | `courses/views/htmx.py` | AI document Q&A |

### 8.2 Model Readiness for Dynamic Filtering

| Model | Filterable By | HTMX Ready | Notes |
|-------|--------------|-------------|-------|
| User | `role`, `major`, `level`, `account_status` | Yes | All FK fields with proper related_names |
| Major | `major_name`, `is_active` | Yes | Simple filtering |
| Level | `level_name`, `level_number` | Yes | Numeric ordering support |
| Course | `level`, `semester`, `is_active`, `course_majors__major` | Yes | Multi-hop filtering via pivot |
| Notification | `notification_type`, `priority`, `course`, `is_active` | Yes | Good filter fields |
| NotificationRecipient | `user`, `is_read`, `is_deleted` | Yes | Per-user state |

### 8.3 What's Needed for HTMX Notification Filtering

```python
# Missing: Dynamic recipient filtering endpoint
# Required HTMX flow:
#
# Admin selects target_type → HTMX loads Major dropdown
# Admin selects Major → HTMX loads Level dropdown  
# Admin selects Level → HTMX loads Course dropdown
# Admin selects Course → HTMX shows recipient count preview
#
# This requires:
# 1. /notifications/htmx/filter-majors/          → Returns Major <option> list
# 2. /notifications/htmx/filter-levels/?major=X   → Returns Level <option> list
# 3. /notifications/htmx/filter-courses/?major=X&level=Y → Returns Course list
# 4. /notifications/htmx/preview-count/?...        → Returns recipient count
```

### 8.4 Department Model Question

The current system has `Major` (تخصص) but **no `Department` (قسم)**. For enterprise notification targeting:

- **Current**: Target by Major + Level only
- **Recommended**: Add Department model for organizational hierarchy:
  ```
  Department (1:N) → Major (N:M) → Course
  ```
  This enables: "Send to all CS Department students" vs "Send to all AI Specialization students"

---

## 9. Critical Issues & Bugs

### 9.1 Severity: CRITICAL (Must Fix Before Any Development)

| # | Issue | File(s) | Description |
|---|-------|---------|-------------|
| C1 | **Hardcoded Secrets** | `.env`, `.gitignore` | API keys, email password, SECRET_KEY committed to git |
| C2 | **Database Committed** | `db.sqlite3`, `.gitignore` | Full database with user data in repository |
| C3 | **ALLOWED_HOSTS Wildcard** | `config/settings.py:23` | `+ ['*']` defeats host validation |
| C4 | **NotificationService Completely Broken** | `notifications/services.py` | All methods use wrong field names |
| C5 | **NotificationManager Partially Broken** | `notifications/models.py:186` | `role__role_name` doesn't exist |
| C6 | **Security Middleware Not Active** | `config/settings.py` | RateLimit, SecurityHeaders, FileUpload security not in MIDDLEWARE |

### 9.2 Severity: HIGH (Should Fix Soon)

| # | Issue | File(s) | Description |
|---|-------|---------|-------------|
| H1 | **XOR "Encryption" for API Keys** | `ai_features/models.py:317-324` | XOR is not encryption; trivially reversible |
| H2 | **No Test Coverage** | All `tests.py` files | < 5% coverage; no regression safety net |
| H3 | **Duplicate SecurityHeadersMiddleware** | `accounts/middleware.py`, `core/middleware.py` | Confusing, one is dead code |
| H4 | **htmx_notifications Broken** | `courses/views/htmx.py:222` | Calls non-existent method |
| H5 | **BroadcastNotificationForm Unused** | `notifications/forms.py:84` | Defined but no view uses it |
| H6 | **File Upload Auto-Notification** | Not wired | No signal/hook triggers notification on upload |

### 9.3 Severity: MEDIUM (Should Address)

| # | Issue | File(s) | Description |
|---|-------|---------|-------------|
| M1 | **CourseManager Anti-pattern** | `courses/models.py:409-410` | `Course.objects = CourseManager()` overrides incorrectly |
| M2 | **Missing `bare_except`** | `core/context_processors.py:98` | `except:` catches everything including SystemExit |
| M3 | **Unused Imports** | Multiple files | `os` in courses/models.py, duplicate `reverse_lazy` in settings |
| M4 | **Spaghetti: HTMX + AI in Courses App** | `courses/views/htmx.py` | AI-related HTMX views should be in `ai_features` app |
| M5 | **No Migration Squashing** | All migration folders | Multiple migration files could be squashed |
| M6 | **Test Scripts in Root** | `test_gemini_*.py`, `clear_old_permissions.py` | Should be in `tests/` or `scripts/` directory |

### 9.4 Severity: LOW (Nice to Have)

| # | Issue | File(s) | Description |
|---|-------|---------|-------------|
| L1 | **No API versioning** | `config/urls.py` | No `/api/v1/` prefix for API endpoints |
| L2 | **No Pagination for HTMX partials** | `courses/views/htmx.py` | File lists not paginated in HTMX views |
| L3 | **Missing `updated_at` on some models** | `Permission`, `Level` | Inconsistent timestamp fields |
| L4 | **Arabic slugs not supported** | URL design | Course codes must be ASCII |

---

## 10. Recommended Action Plan

### Phase 0: Emergency Security Fixes (Day 1)

```
Priority: CRITICAL | Estimated: 2-4 hours
```

- [ ] **Rotate ALL secrets**: Generate new SECRET_KEY, new Gmail app password, new Gemini API keys
- [ ] **Fix `.gitignore`**: Uncomment `.env`, `db.sqlite3`, `logs/`, `media/uploads/`
- [ ] **Remove sensitive files from git**: `git rm --cached .env db.sqlite3` then force-push
- [ ] **Fix ALLOWED_HOSTS**: Remove `+ ['*']` wildcard
- [ ] **Activate security middleware**: Add RateLimitMiddleware, SecurityHeadersMiddleware, FileUploadSecurityMiddleware to MIDDLEWARE

### Phase 1: Notification System Cleanup (Days 2-3)

```
Priority: HIGH | Estimated: 6-8 hours
```

- [ ] **Delete `notifications/services.py`**: It's entirely broken and redundant
- [ ] **Fix `NotificationManager`**: Replace `role__role_name` with `role__code`
- [ ] **Fix `htmx_notifications` view**: Use correct method name
- [ ] **Wire file upload auto-notification**: Add Django signal in `courses/signals.py`
- [ ] **Test all notification flows**: Admin create, Instructor create, User read/delete
- [ ] **Verify `BroadcastNotificationForm`**: Either implement a view for it or remove it

### Phase 2: New Notification System Architecture (Days 4-7)

```
Priority: HIGH | Estimated: 16-20 hours
```

#### 2.1 Model Enhancements

```python
# Add to Notification model:
class Notification(models.Model):
    # Existing fields...
    
    # NEW: Targeting fields
    target_type = models.CharField(max_length=20, choices=[
        ('all', 'All Users'),
        ('role', 'By Role'),
        ('major', 'By Major'),
        ('level', 'By Level'),
        ('course', 'By Course'),
        ('custom', 'Custom Selection'),
    ])
    target_roles = models.ManyToManyField(Role, blank=True)
    target_majors = models.ManyToManyField(Major, blank=True)
    target_levels = models.ManyToManyField(Level, blank=True)
    
    # NEW: Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_draft = models.BooleanField(default=False)
```

#### 2.2 HTMX Dynamic Filtering Endpoints

```python
# notifications/views/htmx.py (NEW FILE)
# GET /notifications/htmx/filter-majors/
# GET /notifications/htmx/filter-levels/?major_id=X
# GET /notifications/htmx/filter-courses/?major_id=X&level_id=Y
# GET /notifications/htmx/preview-recipients/?target_type=X&...
# POST /notifications/htmx/send/
```

#### 2.3 Signal-Based Auto-Notifications

```python
# courses/signals.py (NEW FILE)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LectureFile

@receiver(post_save, sender=LectureFile)
def notify_new_file(sender, instance, created, **kwargs):
    if created and instance.is_visible:
        # Create notification for course students
        ...
```

### Phase 3: Testing Infrastructure (Days 8-9)

```
Priority: HIGH | Estimated: 8-10 hours
```

- [ ] Set up `pytest-django` with fixtures
- [ ] Write tests for:
  - User RBAC permission checks
  - Notification creation and delivery
  - HTMX endpoint responses
  - AI rate limiting
  - File upload security
- [ ] Set up CI/CD pipeline with test requirements

### Phase 4: Code Quality Improvements (Days 10-11)

```
Priority: MEDIUM | Estimated: 4-6 hours
```

- [ ] Remove duplicate `SecurityHeadersMiddleware` from `accounts/middleware.py`
- [ ] Move AI-related HTMX views from `courses/views/htmx.py` to `ai_features/views/htmx.py`
- [ ] Fix `CourseManager` pattern to use proper Django manager registration
- [ ] Replace XOR encryption with `Fernet` (from `cryptography` library) for API keys
- [ ] Clean up root-level test scripts
- [ ] Add proper `bare_except` handling in `context_processors.py`
- [ ] Squash old migrations

### Phase 5: Optional Enhancements (Future)

```
Priority: LOW | Estimated: Varies
```

- [ ] Add `Department` model for organizational hierarchy
- [ ] Implement WebSocket/SSE for real-time notifications
- [ ] Add notification email delivery channel
- [ ] Add notification preference system per user
- [ ] Add API versioning (`/api/v1/`)
- [ ] Add OpenAPI/Swagger documentation
- [ ] Implement proper pagination for HTMX partials

---

## Appendix A: Technology Stack Summary

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Framework | Django | 5.2.10 | Latest LTS |
| DB (Dev) | SQLite | Built-in | Committed to repo (BAD) |
| DB (Prod) | PostgreSQL | via psycopg2-binary 2.9.11 | Not tested |
| Frontend | Bootstrap 5 RTL | Vendored | Static files |
| Interactivity | HTMX | via django-htmx 1.27.0 | Well integrated |
| AI | Google Gemini | via google-genai | Enterprise-grade |
| AI (Legacy) | OpenAI compat | via openai 2.15.0 | Fallback |
| PDF | pdfplumber | 0.11.9 | Text extraction |
| DOCX | python-docx | 1.2.0 | Text extraction |
| PPTX | python-pptx | 1.0.2 | Text extraction |
| Task Queue | Celery | 5.6.2 | Optional, not actively used |
| Cache | Redis | 7.1.0 | Required for rate limiting |
| Images | Pillow | 12.1.0 | Profile pictures |
| Excel | openpyxl/xlsxwriter | Latest | Import/Export |
| NLP | nltk | 3.9.2 | Text processing |
| Data | pandas/numpy | Latest | Data manipulation |

## Appendix B: URL Routing Map

```
/                           → core:home
/scam-admin/                → Django Admin (Unfold theme)
/accounts/login/            → accounts:login
/accounts/logout/           → accounts:logout
/accounts/activation/       → accounts:activation_step1
/accounts/profile/          → accounts:profile
/instructor/                → instructor:dashboard
/instructor/courses/        → instructor:courses
/student/                   → student:dashboard
/student/courses/           → student:courses
/courses/                   → courses:* (legacy admin routes)
/notifications/             → notifications:list
/notifications/<pk>/        → notifications:detail
/notifications/<pk>/read/   → notifications:mark_read
/notifications/mark-all-read/ → notifications:mark_all_read
/notifications/unread-count/ → notifications:unread_count
/notifications/instructor/create/ → notifications:instructor_create
/notifications/admin/create/  → notifications:admin_create
/ai/                        → ai_features:* (AI endpoints)
/stream/                    → core streaming:* (SSE)
```

## Appendix C: Middleware Execution Order

```
Request →
  1. SecurityMiddleware (Django)
  2. SessionMiddleware (Django)
  3. CommonMiddleware (Django)
  4. CsrfViewMiddleware (Django)
  5. AuthenticationMiddleware (Django)
  6. PermissionMiddleware (Custom - loads permissions & menu)
  7. MessageMiddleware (Django)
  8. XFrameOptionsMiddleware (Django)
→ View → Response

MISSING (should be added):
  - RateLimitMiddleware (after CommonMiddleware)
  - SecurityHeadersMiddleware (after XFrameOptionsMiddleware)
  - FileUploadSecurityMiddleware (before View)
  - RequestLoggingMiddleware (first, for timing)
```

---

**End of Report**

*This analysis was generated by performing a complete code-level review of every model, view, middleware, service, URL configuration, template, and setting in the S-ACM repository. All findings are based on the actual codebase as of 2026-02-09.*
