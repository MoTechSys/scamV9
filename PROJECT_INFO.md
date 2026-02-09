# S-ACM Project Information
# Smart Academic Content Management System
# نظام إدارة المحتوى الأكاديمي الذكي

---

## Overview | نظرة عامة

S-ACM is a Django-based Learning Management System (LMS) designed for Arabic-speaking universities. It provides smart academic content management with AI-powered features using Google Gemini.

**Core Features:**
- Multi-role user management (Admin, Instructor, Student)
- Course and lecture file management
- AI-powered content analysis (summary, questions, Q&A)
- Notification system
- Audit logging

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 4.x (Python 3.11+) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI Service | Google Gemini 2.0 Flash |
| Async Tasks | Celery + Redis |
| Frontend | Django Templates + HTMX |
| CSS | Vanilla CSS |

---

## Project Structure

```
ScamV4/
├── config/                    # Django settings
│   ├── settings.py           # Main configuration
│   ├── urls.py               # Root URL routing
│   ├── celery.py             # Celery configuration
│   └── wsgi.py / asgi.py     # WSGI/ASGI servers
│
├── apps/                      # Django applications
│   ├── accounts/             # User management
│   ├── courses/              # Course & file management
│   ├── notifications/        # Notification system
│   ├── ai_features/          # AI services (Gemini)
│   └── core/                 # Core utilities
│
├── templates/                 # HTML templates
│   ├── admin_panel/          # Admin dashboard
│   ├── instructor_panel/     # Instructor dashboard
│   ├── student_panel/        # Student dashboard
│   └── accounts/             # Auth templates
│
├── static/                    # Static files (CSS/JS)
├── media/                     # Uploaded files
└── manage.py                 # Django management
```

---

## Apps Architecture

### 1. accounts (إدارة المستخدمين)

**Path:** `apps/accounts/`

**Models:**
| Model | Description |
|-------|-------------|
| `User` | Custom user model (academic_id as username) |
| `Role` | User roles (Admin, Instructor, Student) |
| `Permission` | System permissions |
| `RolePermission` | Many-to-Many: Role ↔ Permission |
| `Major` | Academic majors/departments |
| `Level` | Academic levels (1-8) |
| `Semester` | Academic semesters |
| `VerificationCode` | OTP codes for activation |
| `PasswordResetToken` | Password reset tokens |
| `UserActivity` | User activity logs |

**Views Structure:**
```
apps/accounts/views/
├── __init__.py      # Exports all views
├── mixins.py        # Access control mixins
│   ├── AdminRequiredMixin
│   ├── InstructorRequiredMixin
│   └── StudentRequiredMixin
├── auth.py          # Authentication views
│   ├── LoginView, LogoutView
│   ├── ActivationStep1-4Views
│   └── PasswordResetViews
├── profile.py       # User profile views
└── admin.py         # Admin panel views
```

**Key Files:**
- `forms.py` - User forms
- `decorators.py` - Function decorators (@student_required, @instructor_required)
- `services.py` - Business logic

---

### 2. courses (إدارة المقررات)

**Path:** `apps/courses/`

**Models:**
| Model | Description |
|-------|-------------|
| `Course` | Academic courses |
| `CourseMajor` | Many-to-Many: Course ↔ Major |
| `InstructorCourse` | Many-to-Many: Instructor ↔ Course |
| `LectureFile` | Uploaded files (hybrid: local + URLs) |

**LectureFile Types:**
- Lecture, Summary, Exam, Assignment, Reference, Other

**Views Structure:**
```
apps/courses/views/
├── __init__.py      # Exports all views
├── student.py       # Student views
│   ├── StudentDashboardView
│   ├── StudentCourseListView
│   └── StudentCourseDetailView
├── instructor.py    # Instructor views
│   ├── InstructorDashboardView
│   ├── FileUploadView
│   └── InstructorAIGenerationView
├── admin.py         # Admin course management
├── common.py        # Shared views (file download/view)
│   ├── FileDownloadView (IDOR protected)
│   └── FileViewView
└── htmx.py          # HTMX partial views
```

**Key Files:**
- `services.py` - EnhancedCourseService, EnhancedFileService
- `mixins.py` - CourseEnrollmentMixin, SecureFileDownloadMixin

---

### 3. notifications v2 (نظام الإشعارات المتكامل)

**Path:** `apps/notifications/`

**Models:**
| Model | Description |
|-------|-------------|
| `Notification` | Notification content with GenericForeignKey for smart linking |
| `NotificationRecipient` | User-specific delivery with read/deleted/archived states |
| `NotificationPreference` | Per-user email notification preferences |

**Notification Types:**
- general, course, file_upload, assignment, exam, grade, announcement, system, welcome

**Priority Levels (with Badge Colors):**
- low (secondary), normal (info), high (warning), urgent (danger)

**GenericForeignKey:**
- Links notifications to any Django model (LectureFile, Course, etc.)
- Enables smart navigation: clicking notification goes to related content

**Django Signals (Auto-Notifications):**
| Signal | Trigger | Recipients |
|--------|---------|------------|
| `handle_user_activation` | User account activated | The activated user (welcome) |
| `handle_file_upload` | New LectureFile created (visible) | All course students |
| `handle_file_visibility_change` | File changed to visible | All course students |

**Signals Configuration:**
- Signals are registered in `apps.py` via `ready()` method
- Signal file: `apps/notifications/signals.py`

**Service Layer (Central API):**
```python
from apps.notifications.services import NotificationService

# === Creating Notifications ===
NotificationService.create_notification(title, body, recipients=users, ...)
NotificationService.notify_file_upload(file_obj, course)
NotificationService.notify_new_user(user)
NotificationService.notify_assignment(assignment_obj, course, sender)
NotificationService.notify_exam(exam_obj, course, sender)
NotificationService.notify_grade(student, course, message)
NotificationService.notify_system(title, body, users=None)

# === Smart Targeting ===
users = NotificationService.get_targeted_users(
    target_type='course_students',  # or: major_students, all_students, all_instructors, everyone, specific_student
    major=major_obj, level=level_obj, course=course_obj
)

# === Reading ===
NotificationService.get_unread_count(user)
NotificationService.get_user_notifications(user, filter_type='all')  # all, unread, archived, trash
NotificationService.get_recent_notifications(user, limit=5)
NotificationService.get_sent_notifications(user)

# === Operations ===
NotificationService.mark_as_read(notification_id, user)
NotificationService.mark_all_as_read(user)
NotificationService.soft_delete(notification_id, user)
NotificationService.restore_from_trash(notification_id, user)
NotificationService.empty_trash(user)
NotificationService.archive_notification(notification_id, user)

# === HTMX Helpers ===
NotificationService.get_majors_for_targeting()
NotificationService.get_levels_for_major(major_id)
NotificationService.get_students_count(major_id, level_id, course_id)
```

**Backward Compatibility:**
```python
# NotificationManager alias still works for old code
from apps.notifications.services import NotificationManager
NotificationManager.create_file_upload_notification(file_obj, course)
NotificationManager.get_unread_count(user)
```

**Views Structure:**
```
apps/notifications/views/
├── __init__.py      # Exports all views
├── common.py        # User-facing views (all roles)
│   ├── NotificationListView (with filter tabs: all/unread/archived)
│   ├── NotificationDetailView (auto mark-as-read + smart navigation)
│   ├── NotificationTrashView (soft-deleted notifications)
│   ├── MarkAsReadView / MarkAllAsReadView
│   ├── DeleteNotificationView / RestoreNotificationView / EmptyTrashView
│   ├── ArchiveNotificationView
│   ├── UnreadCountView (JSON API for HTMX)
│   └── PreferencesView (email notification settings)
├── composer.py      # Notification creation (Admin/Instructor)
│   ├── ComposerView (smart targeting with HTMX cascading dropdowns)
│   └── SentNotificationsView
└── htmx.py          # HTMX dynamic endpoints
    ├── HtmxLevelsForMajor (cascading: Major -> Levels)
    ├── HtmxStudentsCount (live recipient count)
    ├── HtmxBellUpdate (Navbar bell polling every 30s)
    └── HtmxSearchStudents (student search autocomplete)
```

**URL Patterns:**
```
/notifications/              # List (with ?filter=all|unread|archived)
/notifications/<pk>/         # Detail
/notifications/<pk>/read/    # Mark as read
/notifications/mark-all-read/# Mark all read
/notifications/<pk>/delete/  # Soft delete
/notifications/<pk>/restore/ # Restore from trash
/notifications/<pk>/archive/ # Archive
/notifications/trash/        # Trash view
/notifications/trash/empty/  # Empty trash
/notifications/compose/      # Composer (Admin/Instructor)
/notifications/sent/         # Sent list
/notifications/preferences/  # Email preferences
/notifications/htmx/bell/   # HTMX bell update
/notifications/htmx/levels/ # HTMX cascading dropdown
/notifications/htmx/students-count/ # HTMX target count
/notifications/htmx/search-students/ # HTMX student search
```

**Tests:** 35 tests covering Models, Services, Targeting Logic, Views, and HTMX endpoints

---

### 4. ai_features (الذكاء الاصطناعي)

**Path:** `apps/ai_features/`

**Services:**
```python
# GeminiService - Main AI service class
class GeminiService:
    def generate_summary(text: str) -> str
    def generate_questions(text: str, type: QuestionType, count: int) -> List[Question]
    def ask_document(text: str, question: str) -> str
    def extract_text_from_file(file_obj: LectureFile) -> str
```

**Text Extractors:**
- `PDFExtractor` - PyPDF2
- `DocxExtractor` - python-docx
- `PptxExtractor` - python-pptx

**Features:**
- Caching with Django cache
- Retry on failure (exponential backoff)
- Rate limiting handling

---

### 5. core (الأدوات الأساسية)

**Path:** `apps/core/`

**Models:**
| Model | Description |
|-------|-------------|
| `SystemSetting` | Key-value system settings |
| `AuditLog` | Comprehensive audit trail |

**AuditLog Actions:**
- create, update, delete, login, logout, export, import, promote

---

## Database Schema (ERD Summary)

```
User (1) ──────── (N) UserActivity
  │
  ├── Role (FK)
  ├── Major (FK)
  └── Level (FK)

Course (1) ──────── (N) LectureFile
  │
  ├── Level (FK)
  ├── Semester (FK)
  ├── (M:N) Major → CourseMajor
  └── (M:N) User (Instructor) → InstructorCourse

Notification (1) ──────── (N) NotificationRecipient ──── User
```

---

## URL Patterns

| Prefix | App | Description |
|--------|-----|-------------|
| `/accounts/` | accounts | Auth, profile, admin users |
| `/courses/` | courses | Course management |
| `/notifications/` | notifications | Notification management |
| `/ai/` | ai_features | AI endpoints |
| `/` | core | Dashboard redirects |

---

## Authentication Flow

### Account Activation (4 Steps):
1. `ActivationStep1View` - Verify academic_id + id_card_number
2. `ActivationStep2View` - Enter email, send OTP
3. `ActivationVerifyOTPView` - Verify OTP
4. `ActivationSetPasswordView` - Set password, activate account

### Login:
- Username = `academic_id`
- Supports "Remember Me"
- Redirects by role after login

---

## Role-Based Access

| Role | Dashboard | Permissions |
|------|-----------|-------------|
| Admin | `/accounts/admin/dashboard/` | Full system access |
| Instructor | `/courses/instructor/` | Manage assigned courses, upload files, AI features |
| Student | `/courses/student/` | View enrolled courses, download files |

---

## AI Integration

**Configuration (settings.py):**
```python
GEMINI_API_KEY = env('GEMINI_API_KEY')
```

**Usage Example:**
```python
from apps.ai_features.services import GeminiService

service = GeminiService()
text = service.extract_text_from_file(lecture_file)
summary = service.generate_summary(text)
questions = service.generate_questions(text, QuestionType.MCQ, count=5)
```

---

## File Upload System

**Storage Path:**
```
media/uploads/courses/{course_code}/{file_type}/{filename}
```

**Supported Types:**
- PDF, DOCX, PPTX, MP4, ZIP, JPG/PNG

**Hybrid Storage:**
- `content_type = 'local_file'` - Stored locally
- `content_type = 'external_url'` - External URL reference

---

## Important Patterns

### Relative Imports (in views packages):
```python
from ..models import Course, LectureFile
from ..forms import CourseForm
from ..services import EnhancedCourseService
```

### Mixins Usage:
```python
class MyView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'my_template.html'
```

### Soft Delete:
```python
lecture_file.is_deleted = True
lecture_file.deleted_at = timezone.now()
lecture_file.save()
```

---

## Environment Variables

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional, uses SQLite by default)
DATABASE_URL=postgres://user:pass@localhost/dbname

# AI
GEMINI_API_KEY=your-gemini-api-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
```

---

## Commands

```bash
# Setup
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Seed test data
python seed_test_data.py

# Celery (for async tasks)
celery -A config worker -l info
```

---

## Key Services

### EnhancedFileService
```python
EnhancedFileService.get_course_files(course, include_hidden=False)
EnhancedFileService.toggle_visibility(file_obj, user)
EnhancedFileService.delete_file(file_obj, user)
EnhancedFileService.check_file_access(user, file_obj)
```

### NotificationService (v2)
```python
from apps.notifications.services import NotificationService

NotificationService.create_notification(title, body, recipients=users, ...)
NotificationService.notify_file_upload(file_obj, course)
NotificationService.notify_system(title, body, users=None)
NotificationService.get_unread_count(user)
NotificationService.get_user_notifications(user, filter_type='all')
NotificationService.get_targeted_users(target_type='course_students', course=course)
```

---

## Security Features

1. **IDOR Protection** - File downloads verify user enrollment
2. **Role-Based Access** - Mixins enforce permissions
3. **Audit Logging** - All sensitive actions logged
4. **OTP Verification** - Account activation via email OTP
5. **Password Reset** - Token-based reset with expiry

---

## Template Hierarchy

```
templates/
├── base.html                 # Root template
├── admin_panel/
│   ├── base.html            # Admin layout
│   ├── dashboard.html
│   └── users/
├── instructor_panel/
│   ├── base.html            # Instructor layout
│   ├── dashboard.html
│   └── courses/
├── student_panel/
│   ├── base.html            # Student layout
│   ├── dashboard.html
│   └── courses/
└── accounts/
    ├── login.html
    └── activation/
```

---

## HTMX Integration

Used for dynamic updates without full page reloads:
- File list refresh after upload
- Notification count updates
- AI generation progress
- Visibility toggle

---

## Version & Maintenance

- **Language:** Arabic (RTL) with English code
- **Django Version:** 4.x
- **Python Version:** 3.11+
- **Last Updated:** February 2026 (Notification System v2 rebuild)

---

> **Note for AI Agents:** This project follows Django best practices with modular views packages. Always use relative imports (`..models`) when working within app packages. Check `urls.py` for route definitions and `views/__init__.py` for exported views.
