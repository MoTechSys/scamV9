# CHANGELOG - Enterprise v3 Refactoring

<div dir="rtl">

## [v3.0.0] - 2026-02-09 - Notification System v3 & Sidebar Enhancement

### Phase: Notification Management System Overhaul

#### 1. صفحة إدارة الإشعارات الرئيسية (Management Page)
- **قبل**: الإشعارات كانت مجرد عناصر جانبية متفرقة في القائمة
- **بعد**: صفحة رئيسية كاملة مخصصة للإشعارات تحتوي على 5 أقسام:
  - **صندوق الوارد**: عرض الإشعارات مع فلاتر (الكل، غير مقروءة، مؤرشفة، أولوية عالية)
  - **إرسال إشعار**: نموذج إنشاء إشعار جديد مع استهداف ذكي
  - **الإشعارات المرسلة**: قائمة الإشعارات المرسلة مع إمكانية الحذف والإخفاء
  - **الإشعارات التلقائية**: عرض وإدارة الإشعارات التلقائية وإعدادات البريد
  - **سلة المهملات**: سلة موحدة للإشعارات الواردة والمرسلة

#### 2. إصلاح خلل اختيار المستلمين (Recipients Bug Fix)
- **المشكلة**: عند اختيار الخيار الثاني أو الثالث في المستلمون، الحقول الديناميكية لا تعمل
- **الحل**: إعادة هيكلة نظام الاستهداف بالكامل:
  - فصل نوع المستلمين (طلاب/دكاترة) عن نوع الاستهداف
  - JavaScript ديناميكي يغير خيارات الاستهداف حسب نوع المستلمين
  - إضافة دعم الاستهداف: `major_instructors`, `specific_instructor`
  - HTMX بحث عن الدكاترة (`HtmxSearchInstructors`)

#### 3. حذف/إخفاء الإشعارات المرسلة
- **جديد**: الدكتور يمكنه الآن:
  - إخفاء إشعار مرسل من القائمة (`is_hidden_by_sender`)
  - حذف إشعار مرسل (نقل لسلة المهملات) (`is_deleted_by_sender`)
  - استعادة إشعار مرسل من سلة المهملات
- **حقول جديدة في النموذج**:
  - `Notification.is_hidden_by_sender`
  - `Notification.is_deleted_by_sender`
  - `Notification.sender_deleted_at`

#### 4. سلة المهملات الموحدة
- سلة مهملات واحدة تعرض:
  - الإشعارات الواردة المحذوفة
  - الإشعارات المرسلة المحذوفة
- زر إفراغ السلة يحذف الكل نهائياً

#### 5. القائمة الجانبية: طي/توسيع مع أيقونات
- **جديد**: زر طي/توسيع القائمة الجانبية
- عند الطي: تظهر الأيقونات فقط مع Tooltip عند hover
- الحالة محفوظة في `localStorage` بين الجلسات
- تصميم سلس مع `transition` و `animation`
- متجاوب: على الموبايل القائمة كاملة مع overlay

#### 6. تحسينات التصميم
- تصميم متجاوب بالكامل (Responsive)
- تبديل سلس بين الأقسام في صفحة الإدارة
- أنماط مخصصة للعناصر الجديدة
- Filter pills للفلترة السريعة

### الملفات المعدلة
| الملف | التغيير |
|-------|---------|
| `apps/notifications/models.py` | إضافة حقول حذف/إخفاء المرسل |
| `apps/notifications/forms.py` | إعادة هيكلة نموذج الإرسال مع دعم الدكاترة |
| `apps/notifications/services.py` | إضافة خدمات إدارة الإشعارات المرسلة |
| `apps/notifications/urls.py` | إضافة URLs جديدة للإدارة |
| `apps/notifications/views/__init__.py` | تحديث الاستيرادات |
| `apps/notifications/views/common.py` | إضافة NotificationManagementView |
| `apps/notifications/views/composer.py` | إضافة views حذف/إخفاء المرسل |
| `apps/notifications/views/htmx.py` | إصلاح البحث + إضافة بحث الدكاترة |
| `templates/notifications/management.html` | صفحة الإدارة الرئيسية الجديدة |
| `templates/layouts/dashboard_base.html` | القائمة الجانبية مع طي/توسيع |
| `apps/notifications/migrations/0003_*` | Migration للحقول الجديدة |

---

## [v2.0.0] - 2026-02-08 - Enterprise Performance & AI Governance

### Phase 0: Deep Code Audit (Findings)

#### apps/instructor/views.py - Memory Bloat
- **Problem**: `InstructorDashboardView.get_context_data()` loaded ALL files into Python memory:
  ```python
  files = list(LectureFile.objects.filter(...))  # Loads entire table
  total_downloads = sum(f.download_count for f in files)  # O(n) Python loop
  sorted(files, key=lambda x: x.download_count, reverse=True)[:5]  # O(n log n) sort
  ```
- **Impact**: Memory usage scales linearly with file count. With 10K files = ~50MB per request.

#### apps/student/views.py - N+1 Query Explosion
- **Problem**: `StudentDashboardView` executed 3 queries per course in a loop:
  ```python
  for course in current_courses:  # N courses
      course.files.filter(...).count()  # +1 query
      StudentProgress.objects.filter(...).count()  # +1 query
      course.instructor_courses.select_related()  # +1 query
  ```
- **Impact**: 1 + 3N database queries. With 10 courses = 31 queries per dashboard load.

#### apps/ai_features - Single-Key Fragility
- **Problem**: Single API key from `.env`, no rotation, no health tracking.
- **Impact**: One rate limit = entire AI service down.

---

### Phase 1: Extreme Performance Refactoring

#### 1.1 Instructor Dashboard (DB Aggregation)
**File**: `apps/instructor/views.py`

| Metric | Before | After |
|--------|--------|-------|
| File stats | Python `sum()` over list | `LectureFile.objects.aggregate(Sum, Count)` |
| Recent uploads | `sorted(files, ...)[:5]` | `.order_by('-upload_date')[:5]` (DB LIMIT) |
| Top files | `sorted(files, ...)[:5]` | `.order_by('-download_count')[:5]` (DB LIMIT) |
| Memory | O(n) - all files in RAM | O(1) - only aggregated values |
| DB Queries | 1 heavy + Python processing | 6 lightweight optimized queries |

#### 1.2 Student Dashboard (2-Query Architecture)
**File**: `apps/student/views.py`

| Metric | Before | After |
|--------|--------|-------|
| Query count | 1 + 3N (N = course count) | 2 queries total |
| Technique | Loop with per-course queries | `annotate()` + `Prefetch` |
| File counts | `course.files.filter().count()` per course | `annotate(visible_file_count=Count(...))` |
| Progress | `StudentProgress.objects.filter().count()` per course | `annotate(viewed_file_count=Count(...))` |
| Instructor | `.select_related()` per course | `Prefetch('instructor_courses')` |

#### 1.3 Database Indexes
**File**: `apps/courses/models.py`

Added 4 composite indexes to `LectureFile`:
- `idx_lf_course_vis` - (course, is_visible)
- `idx_lf_uploader_del` - (uploader, is_deleted)
- `idx_lf_upload_stats` - (uploader, is_deleted, upload_date)
- `idx_lf_crs_vis_del` - (course, is_visible, is_deleted)

---

### Phase 2: TANK AI Engine (Dynamic Governance)

#### 2.1 AIConfiguration Singleton Model
**File**: `apps/ai_features/models.py`

New singleton model storing:
- `active_model`: Dropdown (gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-pro)
- `chunk_size`: Integer (1000-100000, default 30000)
- `chunk_overlap`: Integer (0-5000, default 500)
- `max_output_tokens`: Integer (100-8192, default 2000)
- `temperature`: Float (0.0-2.0, default 0.3)
- `user_rate_limit_per_hour`: Integer (1-1000, default 10)
- `is_service_enabled`: Boolean (service kill switch)
- `maintenance_message`: Custom message when disabled

**Pattern**: `AIConfiguration.get_config()` with 5-minute cache.

#### 2.2 APIKey Model (Encrypted)
**File**: `apps/ai_features/models.py`

Fields:
- `_encrypted_key`: XOR + Base64 encrypted (derived from SECRET_KEY)
- `key_hint`: Last 4 chars for identification
- `status`: active | cooldown | disabled | error
- `error_count`: Consecutive error counter (auto-disable at 5)
- `total_requests`: Lifetime counter
- `last_latency_ms`: Response time tracking
- `rpm_limit`: Requests Per Minute limit (default 15)
- `cooldown_until`: Automatic 60s cooldown on 429
- `tokens_used_today`: Daily token tracking
- `priority`: Round-robin ordering

Methods:
- `set_key(raw)` / `get_key()` - Encryption/Decryption
- `mark_success(latency_ms)` - Record success
- `mark_error(msg, is_rate_limit)` - Record error with auto-cooldown
- `is_available()` - Check if key can be used
- `check_rpm_limit()` - Cache-based RPM enforcement

#### 2.3 HydraKeyManager Service
**File**: `apps/ai_features/services.py`

Features:
- DB-first key fetching with .env fallback
- Thread-safe singleton with Lock
- Round-Robin rotation across available keys
- Automatic cooldown on 429 errors
- RPM enforcement per key via Django cache
- Health status API for admin dashboard

Flow:
```
get_next_key() -> (APIKey_obj, raw_key)
  1. Fetch active DB keys
  2. Filter: is_available() AND check_rpm_limit()
  3. Round-Robin select
  4. Fallback to .env if no DB keys
```

#### 2.4 GeminiService v2
**File**: `apps/ai_features/services.py`

All configuration now reads from DB:
- Model name: `AIConfiguration.active_model`
- Max tokens: `AIConfiguration.max_output_tokens`
- Temperature: `AIConfiguration.temperature`
- Chunk size: `AIConfiguration.chunk_size`

Service checks:
- `_check_service_enabled()` raises `GeminiServiceDisabledError` if admin disabled
- Automatic key rotation on error with Hydra manager

#### 2.5 Health Check & Calibration
**File**: `apps/ai_features/admin.py`

Admin actions:
- **Test Connection**: Sends "Hello" prompt, records latency, updates key status
- **Reset Errors**: Clears error count and cooldown
- **Activate/Deactivate**: Bulk key management

Custom admin views:
- `/admin/ai_features/apikey/ai-dashboard/`: Real-time health dashboard
- `/admin/ai_features/apikey/test-key/<id>/`: AJAX single key test

---

### Phase 3: UI/UX Modernization

#### 3.1 Notification Broadcast
**File**: `apps/notifications/forms.py`

New `BroadcastNotificationForm` with targets:
- All students in a specific course
- All students in the system
- All instructors
- Everyone

#### 3.2 Admin AI Dashboard
**Template**: `templates/admin/ai_features/ai_dashboard.html`

Shows:
- Active/Total keys count
- Today's requests, tokens, failure rate
- Per-key health cards with status badges
- Test button with AJAX feedback
- Configuration summary

#### 3.3 Admin Sidebar Navigation
**File**: `config/settings.py`

Updated Unfold sidebar with:
- AI Monitoring Dashboard link
- AI Configuration link
- API Keys management link
- Usage logs link

---

### Phase 4: Architecture Polish

#### 4.1 SmartChunker DB Integration
Reads `chunk_size` and `chunk_overlap` from `AIConfiguration` (DB).
Falls back to constants if DB is unavailable.

#### 4.2 Rate Limit DB Integration
`AIUsageLog.check_rate_limit()` and `get_remaining_requests()` now read
`user_rate_limit_per_hour` from `AIConfiguration` instead of `settings.py`.

---

### Files Modified

| File | Changes |
|------|---------|
| `apps/instructor/views.py` | Complete rewrite of Dashboard with DB aggregation |
| `apps/student/views.py` | 2-query architecture with annotate+prefetch |
| `apps/courses/models.py` | 4 new composite indexes |
| `apps/ai_features/models.py` | New: AIConfiguration, APIKey. Enhanced: AIUsageLog |
| `apps/ai_features/services.py` | New: HydraKeyManager. Rewritten: GeminiService v2 |
| `apps/ai_features/admin.py` | Complete rewrite with health check + dashboard |
| `apps/notifications/forms.py` | New: BroadcastNotificationForm |
| `config/settings.py` | Updated admin sidebar navigation |
| `templates/admin/ai_features/ai_dashboard.html` | New: AI monitoring dashboard |

### Migrations

- `courses/0002_lecturefile_idx_lf_course_vis_and_more.py` - 4 new indexes
- `ai_features/0004_aiconfiguration_apikey_aiusagelog_api_key_used_and_more.py` - New models

</div>
