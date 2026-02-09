# UniCore-OS - خطة التنفيذ الشاملة لنظام S-ACM
## Smart Academic Content Management System - Enterprise Edition v2

> **تاريخ التوثيق:** 2026-02-09
> **الحالة:** Phase 1-4 مكتملة | Phase 5-6 قيد التنفيذ
> **الاختبارات:** 57 اختبار - جميعها ناجحة (All Green)
> **Django Check:** 0 مشاكل

---

## 1. ملخص المشروع

S-ACM (Smart Academic Content Management) هو نظام إدارة محتوى أكاديمي ذكي يجمع بين:
- **إدارة المقررات والملفات** للمدرسين والطلاب
- **محرك ذكاء اصطناعي** (Gemini AI) للتلخيص وتوليد الأسئلة والمحادثة مع المستندات
- **نظام إشعارات متقدم** مع دعم البث والإشعارات المجدولة
- **لوحات تحكم** مخصصة لكل دور (Admin/Instructor/Student)

---

## 2. البنية التقنية

| المكون | التقنية |
|--------|---------|
| Backend | Django 6.0 (Python 3.12) |
| Database | SQLite (Dev) / PostgreSQL (Prod) |
| AI Engine | Google Gemini API (2.5-flash, 3-pro-preview) |
| Frontend | Bootstrap 5 RTL + HTMX |
| Admin Panel | Django Unfold |
| الاتجاه | RTL (العربية) |

### نماذج الذكاء الاصطناعي (JSON Guidance Block - scamV9)

```json
{
  "High_Intelligence_Core": "gemini-3-pro-preview",
  "High_Performance_Core": "gemini-3-flash-preview (1M token, up to 65536)",
  "Security_Audit_Unit": "deep-research-pro-preview-12-2025",
  "Default_Model": "gemini-2.5-flash",
  "Fallback": "gemini-2.0-flash"
}
```

---

## 3. الإصلاحات المنجزة

### 3.1 إصلاحات حرجة (Phase 1)

| Bug ID | الوصف | الحالة |
|--------|-------|--------|
| BUG-001 | GEMINI_API_KEY مضاف في .env وsettings.py يقرأه | مكتمل |
| BUG-002 | إنشاء جميع Templates AI المفقودة (4 قوالب) | مكتمل |
| BUG-003 | ProfileView لا يمرر Form - تم إعادة كتابة كـ View مع GET/POST | مكتمل |
| BUG-004 | حقل old_password vs current_password - القالب يستخدم current_password الصحيح | مكتمل |
| BUG-005 | OPENAI_BASE_URL مصحح إلى generativelanguage.googleapis.com | مكتمل |
| BUG-006 | SECRET_KEY مكرر - تم التنظيف | مكتمل |
| BUG-008 | Profile وChange Password تستخدم base.html - تم التحويل لـ dashboard_base.html | مكتمل |
| BUG-009 | Sidebar المدرس لا يحتوي روابط الإشعارات - تم الإضافة | مكتمل |

### 3.2 إصلاح قالب الإشعارات (Phase 2C)

- **المشكلة:** `notifications/list.html` كان يستخدم `notification.title` مباشرة لكن الـ queryset يرجع `NotificationRecipient`
- **الحل:** تعديل القالب لاستخدام `nr.notification.title`, `nr.notification.body`, `nr.notification.course` إلخ

---

## 4. الملفات المعدلة والجديدة

### 4.1 ملفات معدلة (9 ملفات)

| الملف | التعديل |
|-------|---------|
| `.env` | إضافة GEMINI_API_KEY, AI_MODEL_NAME, تنظيف المكرر |
| `config/settings.py` | قراءة GEMINI_API_KEY, AI_MODEL_NAME, إعدادات الأمان |
| `apps/accounts/views/profile.py` | إعادة كتابة ProfileView كـ View + تمرير Form + active_page |
| `apps/ai_features/models.py` | إضافة نماذج Gemini 2.5/3 في MODEL_CHOICES, تحديث max_output_tokens |
| `apps/ai_features/services.py` | استخدام AI_MODEL_NAME من settings |
| `apps/core/context_processors.py` | عداد إشعارات حقيقي + آخر 5 إشعارات للـ dropdown |
| `templates/layouts/dashboard_base.html` | Navbar dropdown إشعارات + Sidebar محسن للمدرس والطالب |
| `templates/accounts/profile.html` | إعادة تصميم كاملة - dashboard_base + avatar + upload + activities |
| `templates/accounts/change_password.html` | إعادة تصميم - dashboard_base + معلومات أمان |

### 4.2 ملفات جديدة (8 ملفات)

| الملف | الوصف |
|-------|-------|
| `templates/ai_features/summarize.html` | قالب التلخيص بالذكاء الاصطناعي |
| `templates/ai_features/questions.html` | قالب بنك الأسئلة AI |
| `templates/ai_features/ask_document.html` | قالب اسأل المستند (دردشة AI) |
| `templates/ai_features/usage_stats.html` | قالب إحصائيات استخدام AI |
| `templates/notifications/detail.html` | قالب تفاصيل الإشعار |
| `tests/__init__.py` | حزمة الاختبارات |
| `tests/test_unicore.py` | 57 اختبار شامل |
| `UNICORE_PLAN.md` | هذا المستند |

---

## 5. تحسينات الأمان

| الإعداد | القيمة | الوصف |
|---------|--------|-------|
| `CSRF_COOKIE_HTTPONLY` | `True` | منع JavaScript من الوصول لـ CSRF cookie |
| `SESSION_COOKIE_HTTPONLY` | `True` | منع JavaScript من الوصول لـ session cookie |
| `SECURE_REFERRER_POLICY` | `strict-origin-when-cross-origin` | سياسة referrer آمنة |
| Production: `CSRF_COOKIE_SECURE` | `True` (when DEBUG=False) | CSRF عبر HTTPS فقط |
| Production: `SESSION_COOKIE_SECURE` | `True` (when DEBUG=False) | Session عبر HTTPS فقط |
| Production: `X_FRAME_OPTIONS` | `DENY` | منع embedding في iframe |

---

## 6. إدارة مفاتيح API (Hybrid Approach)

### النهج المختلط: ENV vars + Admin DB

1. **المستوى الأول (ENV):** `GEMINI_API_KEY` في `.env` - للتطوير والـ fallback
2. **المستوى الثاني (DB):** `APIKey` model مع:
   - تشفير XOR + Base64
   - تتبع الصحة (error_count, last_error, latency)
   - Cooldown تلقائي عند 429 Rate Limit
   - RPM limit per key
   - Round-Robin rotation بين المفاتيح
3. **الأولوية:** DB > ENV (يتحقق من DB أولاً، ثم fallback للـ ENV)

### استبدال المفتاح المسرب
- **الإجراء:** المفتاح الحالي في `.env` يجب استبداله فوراً في الإنتاج
- **الخطوات:**
  1. إلغاء المفتاح المسرب من Google Cloud Console
  2. إنشاء مفتاح جديد
  3. تحديث `.env` + إضافة المفتاح الجديد في Admin Panel

---

## 7. أدوار الطالب والمدرس

### 7.1 المدرس (Instructor)

| الصلاحية | الوصف | الحالة |
|----------|-------|--------|
| إدارة المقررات | عرض وإدارة المقررات المسندة | مفعل |
| رفع الملفات | رفع/تحديث/حذف ملفات المحاضرات | مفعل |
| مركز AI | توليد ملخصات وأسئلة من الملفات | مفعل |
| إرسال إشعارات | إرسال إشعارات لطلاب المقرر | مفعل |
| عرض الإشعارات المرسلة | تتبع الإشعارات المرسلة | مفعل |
| سجل الطلاب | عرض كشوف الطلاب + تصدير Excel | مفعل |
| سلة المهملات | استرجاع/حذف الملفات المحذوفة | مفعل |

### 7.2 الطالب (Student)

| الصلاحية | الوصف | الحالة |
|----------|-------|--------|
| عرض المقررات | عرض المقررات المسجل بها | مفعل |
| غرفة الدراسة | قراءة الملفات مع تتبع التقدم | مفعل |
| أدوات AI | تلخيص وأسئلة ودردشة مع المستندات | مفعل |
| الإشعارات | استقبال وقراءة الإشعارات | مفعل |
| إحصائيات AI | عرض سجل استخدام الذكاء الاصطناعي | مفعل |
| الملف الشخصي | عرض وتحديث البيانات الشخصية | مفعل |

### 7.3 المدير (Admin)

| الصلاحية | الوصف | الحالة |
|----------|-------|--------|
| إدارة المستخدمين | إضافة/تعديل/حذف المستخدمين والأدوار | مفعل |
| إدارة المقررات | إنشاء وإدارة المقررات والتخصصات | مفعل |
| محرك AI | تكوين AI (النموذج، التوكنات، Rate Limit) | مفعل |
| مفاتيح API | إدارة المفاتيح مع مراقبة الصحة | مفعل |
| إشعارات عامة | إرسال إشعارات لجميع المستخدمين | مفعل |
| سجلات التدقيق | مراقبة النشاطات والأمان | مفعل |

---

## 8. نتائج الاختبارات

### ملخص: 57 اختبار - جميعها ناجحة

| الفئة | العدد | الحالة |
|-------|-------|--------|
| Accounts Models (Role, User) | 8 | All Green |
| Accounts Forms (Profile, Password, Login) | 7 | All Green |
| Accounts Views (Profile, ChangePassword) | 8 | All Green |
| Notification Models | 6 | All Green |
| Notification Views | 6 | All Green |
| AI Features Models (Config, APIKey) | 5 | All Green |
| URL Resolution | 7 | All Green |
| Context Processors | 4 | All Green |
| Security Settings | 3 | All Green |
| Template Rendering | 3 | All Green |
| **المجموع** | **57** | **All Green** |

```
Ran 57 tests in 63.5s
OK
```

---

## 9. Sidebar - إدارة الإشعارات

### القائمة الجانبية للمدرس (محدّثة)

```
الرئيسية
  - لوحة التحكم
  - مقرراتي
الأدوات
  - مركز AI
  - سلة المهملات
التواصل
  - الإشعارات (مع عداد غير المقروءة)
  - إرسال إشعار
  - الإشعارات المرسلة
```

### Navbar Dropdown (محدّث)

- عداد الإشعارات غير المقروءة (حقيقي من DB)
- آخر 5 إشعارات مع العنوان والوقت
- زر "عرض الكل" + "تحديد الكل كمقروء"

---

## 10. خطة التنفيذ المستقبلية

### المرحلة التالية (Phase 6-8)

| المرحلة | المهام | الأولوية |
|---------|--------|----------|
| Phase 6 | الإشعارات المجدولة (Scheduled Notifications) | متوسط |
| Phase 7 | تقارير الإشعارات (إحصائيات: مرسلة/مقروءة/نسبة) | متوسط |
| Phase 7 | تنبيهات ذكية للطالب (Alerts) | متوسط |
| Phase 8 | تنظيف الكود القديم (Dead Code Cleanup) | منخفض |
| Phase 8 | تحسينات الأداء (N+1, Caching) | متوسط |

### ملاحظات التحذير (Tasks 5 & 7 - Yellow Flag)

1. **Task 5 - ملفات Admin القديمة:**
   - يوجد admin panel templates قديمة تحتاج تنظيف
   - Unfold admin يغطي معظم الوظائف
   - **التوصية:** حذف القوالب القديمة غير المستخدمة بعد التحقق

2. **Task 7 - الأمان والأداء:**
   - تم تطبيق: CSRF_COOKIE_HTTPONLY, SESSION_COOKIE_HTTPONLY, SECURE_REFERRER_POLICY
   - **متبقي للإنتاج:** استبدال GEMINI_API_KEY المسرب، HSTS headers, SSL redirect
   - **الأداء:** InstructorDashboardView يستخدم DB aggregation (محسّن)

---

## 11. الروابط والمراجع

| الوصف | الرابط |
|-------|--------|
| GitHub Repository | https://github.com/MoTechSys/scamV9 |
| التحليل الشامل | `S-ACM_FULL_ANALYSIS.md` |
| خطة UniCore | `UNICORE_PLAN.md` (هذا المستند) |

---

## 12. HTTP Status

```
Django System Check: 0 issues
Tests: 57/57 PASSED
HTTP Status: 200 OK
Modified Files: 9
New Files: 8
```

---

*تم إعداد هذا المستند بواسطة Claude AI - تاريخ: 2026-02-09*
