# S-ACM - Smart Academic Content Management System

> Enterprise-grade academic content management with AI-powered features, video streaming, and role-based access control.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [AI Router (Manus Proxy)](#ai-router-manus-proxy)
- [Video Streaming Engine](#video-streaming-engine)
- [RBAC (Role-Based Access Control)](#rbac-role-based-access-control)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Reference](#api-reference)

---

## Overview

S-ACM is a Django-based academic content management system designed for universities. It provides:

- **Multi-role access** (Admin, Instructor, Student) with granular permissions
- **AI-powered features** (summarization, question generation, document Q&A) via Manus API Proxy
- **Video streaming** with HTTP Range headers (206 Partial Content)
- **Smart archiving** based on semester and student level
- **Real-time notifications** with HTMX integration

## Key Features

| Feature | Description |
|---|---|
| **AI Summarization** | Generate markdown summaries from PDF, DOCX, PPTX files |
| **Question Matrix** | Create MCQ, True/False, Short Answer exams with scoring |
| **Document Q&A** | Ask questions about uploaded documents with context-aware answers |
| **Video Streaming** | Range-based video playback with seek support |
| **RBAC** | Three-tier role system with 15+ granular permissions |
| **Smart Archive** | Automatic course archiving based on semester progression |
| **Study Room** | Split-screen view: file viewer + AI chat assistant |
| **Excel Export** | Student roster with activity statistics |
| **Notification System** | Smart targeting, cascading filters, HTMX real-time UI |

---

## Architecture

```
S-ACM/
|-- config/                  # Django settings, URLs, WSGI/ASGI
|-- apps/
|   |-- accounts/            # User model, RBAC, decorators, mixins
|   |-- ai_features/         # AI services, models, Manus proxy client
|   |-- core/                # System settings, audit log, streaming engine
|   |-- courses/             # Course, LectureFile, enrollment logic
|   |-- instructor/          # Instructor dashboard, AI Hub, reports
|   |-- student/             # Student dashboard, study room, AI center
|   |-- notifications/       # Notification service, HTMX views
|-- templates/               # Django templates (RTL Arabic UI)
|-- static/                  # CSS, JS, images
|-- tests/                   # Comprehensive test suite
|-- media/                   # Uploaded files + AI-generated content
```

---

## Quick Start

### Windows (Automated)

```cmd
run_project.bat
```

This script will:
1. Create a Python virtual environment
2. Install all dependencies
3. Run database migrations
4. Create initial roles, permissions, and admin user
5. Start the development server

### Manual Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Run migrations
python manage.py migrate --run-syncdb

# 5. Create initial data
python manage.py setup_initial_data

# 6. Start server
python manage.py runserver 0.0.0.0:8000
```

### Default Credentials

| Role | Academic ID | Password |
|---|---|---|
| Admin | `admin` | `admin123` |

---

## Configuration

All configuration is via environment variables in `.env`:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `True` |
| `USE_POSTGRES` | Use PostgreSQL instead of SQLite | `False` |
| `MANUS_API_KEY` | Manus AI API key | (required for AI features) |
| `MANUS_BASE_URL` | Manus API proxy URL | `https://api.manus.im/api/llm-proxy/v1` |
| `AI_MODEL_NAME` | AI model to use | `gpt-4.1-mini` |
| `AI_RATE_LIMIT_PER_HOUR` | AI requests per hour | `9999` |

### Production Security

When deploying with `DEBUG=False`, the following are auto-enabled:
- `SECURE_SSL_REDIRECT`
- `CSRF_COOKIE_SECURE`
- `SESSION_COOKIE_SECURE`
- `HSTS` (1 year, preload)
- Wildcard `*` removed from `ALLOWED_HOSTS`

---

## AI Router (Manus Proxy)

The AI features use an **OpenAI-compatible proxy** via [Manus](https://manus.im):

```
Client -> GeminiService -> OpenAI Python SDK -> Manus Proxy -> gpt-4.1-mini
```

### How It Works

1. **`HydraKeyManager`** loads `MANUS_API_KEY` from environment (singleton pattern)
2. **`GeminiService`** creates an `OpenAI(base_url=MANUS_BASE_URL)` client
3. All requests use `chat.completions.create()` with system prompt
4. **`AIConfiguration`** model allows admin to change model, tokens, temperature without code changes

### Admin-Editable Settings (No Code Changes)

Via Django Admin > AI Configuration:
- `active_model`: Change AI model (e.g., `gpt-4.1-mini`, `gemini-2.5-flash`)
- `is_service_enabled`: Toggle AI service on/off
- `maintenance_message`: Custom message when service is disabled
- `chunk_size` / `chunk_overlap`: Smart text chunking parameters
- `max_output_tokens` / `temperature`: Generation parameters

### AI Endpoints

| Action | Instructor | Student |
|---|---|---|
| Generate Summary | AI Hub | Study Room / AI Center |
| Generate Questions (Matrix) | AI Hub | AI Center |
| Document Q&A | - | Study Room Chat |

---

## Video Streaming Engine

Located in `apps/core/streaming.py`:

### Range Header Support

```http
GET /stream/file/42/ HTTP/1.1
Range: bytes=0-1048575

HTTP/1.1 206 Partial Content
Content-Range: bytes 0-1048575/5242880
Content-Length: 1048576
Accept-Ranges: bytes
```

### Implementation

- **`RangeFileIterator`**: Efficient byte-range iterator with configurable chunk size
- **`StreamFileView`**: Handles Range parsing, returns 206 for videos, 200 for other files
- **`StreamMarkdownView`**: Renders AI-generated markdown as HTML with RTL support

### Status Codes

| Code | Meaning |
|---|---|
| `200` | Full file response (non-video or no Range header) |
| `206` | Partial content (Range request on video) |
| `416` | Range not satisfiable |
| `404` | File not found or access denied |

---

## RBAC (Role-Based Access Control)

### Three-Tier Roles

| Role | Dashboard | Upload | AI Generation | View Content |
|---|---|---|---|---|
| **Admin** | Admin Panel | Yes | Yes | All |
| **Instructor** | Instructor Hub | Yes | Yes | Assigned Courses |
| **Student** | Study Dashboard | No | Chat Only | Enrolled Courses |

### Enforcement Layers

1. **Decorators** (`apps/accounts/decorators.py`): `@role_required`, `@instructor_required`, `@student_required`
2. **Mixins** (`apps/accounts/views/mixins.py`): `AdminRequiredMixin`, `InstructorRequiredMixin`, `StudentRequiredMixin`
3. **Course Mixins** (`apps/courses/mixins.py`): `CourseEnrollmentMixin`, `FileAccessMixin`, `SecureFileDownloadMixin`
4. **Middleware** (`apps/core/middleware.py`): `PermissionMiddleware` for dynamic menu/permissions

### IDOR Protection

`SecureFileDownloadMixin` centralizes file access checks:
- Verifies file is not soft-deleted
- Validates course enrollment (level + major matching)
- Enforces visibility rules for students

---

## Testing

### Run Full Test Suite

```bash
python manage.py test tests.test_comprehensive -v2
```

### Test Categories (31 tests)

| Category | Tests | Description |
|---|---|---|
| **AI Service (Mock)** | 7 | Summary, questions, Q&A with mocked Manus API |
| **Streaming** | 4 | Range header 206, content-length, 416 errors |
| **RBAC Security** | 6 | Student-blocked-from-instructor, auth redirects |
| **Decorators** | 2 | `@role_required` enforcement |
| **Models** | 5 | Role checks, OTP generation, token generation |
| **Settings Audit** | 5 | CSRF, session security, AI config |
| **AI Storage** | 2 | File save/read/delete operations |

### Example: Student Blocked from Instructor Page

```python
def test_student_cannot_access_instructor_dashboard(self):
    self.client_http.force_login(self.student)
    response = self.client_http.get(reverse('instructor:dashboard'))
    self.assertIn(response.status_code, [403, 302])  # Forbidden or redirect
```

---

## Deployment

### Railway

```bash
# Procfile is included
web: gunicorn config.wsgi --bind 0.0.0.0:$PORT
```

Set environment variables in Railway dashboard (see Configuration section).

### Docker (Optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]
```

---

## API Reference

### Streaming URLs

| URL | View | Description |
|---|---|---|
| `/stream/file/<pk>/` | `StreamFileView` | Stream/download a lecture file |
| `/stream/markdown/<path>/` | `StreamMarkdownView` | Render AI markdown as HTML |

### AI URLs

| URL | View | Description |
|---|---|---|
| `/ai/` | AI Features root | AI feature hub |

### AJAX Endpoints

| URL | Method | Returns |
|---|---|---|
| `/instructor/ajax/course-files/` | GET | JSON/HTMX file list |
| `/student/ajax/course-files/` | GET | JSON/HTMX file list |
| `/student/study-room/<pk>/chat/` | POST | JSON AI response |

---

## License

This project is part of an academic capstone. All rights reserved.
