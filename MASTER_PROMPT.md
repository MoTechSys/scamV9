# MASTER PROMPT - S-ACM System Complete Fix & Enhancement

## CONTEXT
You are working on **S-ACM (Smart Academic Content Management)** - a Django 5.x web application for managing academic content. The system uses Bootstrap 5 RTL, HTMX, and integrates with AI (Manus API Proxy / OpenAI-compatible). The project must be **production-ready within 3 hours**.

**Tech Stack:** Django 5.2.10 | SQLite (dev) / PostgreSQL (prod) | Bootstrap 5 RTL | HTMX 1.9 | OpenAI Python SDK via Manus Proxy | Celery (optional)

**Project Structure:**
```
webapp/
  apps/
    accounts/    # Users, Roles, RBAC, Auth
    ai_features/ # AI Models, Services (GeminiService), Views
    core/        # SystemSetting, AuditLog, Context Processors
    courses/     # Course, LectureFile, InstructorCourse
    instructor/  # Instructor dashboard, AI Hub, Reports
    student/     # Student dashboard, Study Room, AI Center
    notifications/ # Notification system
  config/        # settings.py, urls.py
  templates/     # HTML templates
  static/        # CSS, JS, fonts
  media/         # Uploaded files + AI generated .md files
```

---

## PHASE 1: CRITICAL BUGS TO FIX (MUST FIX)

### Bug 1: Font Performance - Remove Tajawal CDN & Local Font Loading
**Problem:** The system loads `Tajawal` font both from Google Fonts CDN AND local @font-face woff2 files in `static/css/style.css` AND `templates/layouts/dashboard_base.html`. The local woff2 files may not exist (`static/fonts/Tajawal-*.woff2`), causing 404 errors and slowing page load significantly.

**Fix Required:**
1. In `templates/layouts/dashboard_base.html` - **REMOVE** the Google Fonts `<link>` tag:
   ```html
   <!-- REMOVE THIS LINE -->
   <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap" rel="stylesheet">
   ```
2. In `static/css/style.css` - **REMOVE** all `@font-face` declarations for Tajawal (lines 24-50+).
3. In `static/css/style.css` - Update the CSS variable for font-family to use **system fonts only**:
   ```css
   --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans Arabic', sans-serif;
   ```
4. In `templates/student/study_room.html` - The `<style>` block already has system font fallback, verify it does NOT reference Tajawal.
5. Search the entire codebase for any remaining `Tajawal` or `fonts.googleapis.com` references and remove them all.

### Bug 2: AI Chat Rate Limit - Remove the 10-request limit
**Problem:** The student AI chat in `StudyRoomView` calls `AIUsageLog.check_rate_limit(request.user)` which enforces a per-hour limit from `AIConfiguration.user_rate_limit_per_hour` (default=10). The user explicitly wants **UNLIMITED** AI chat usage.

**Fix Required:**
1. In `apps/student/views.py` -> `AIChatView.post()` - **REMOVE** or bypass the rate limit check:
   ```python
   # REMOVE these lines:
   if not AIUsageLog.check_rate_limit(request.user):
       error = '...'
       ...
       return redirect(...)
   ```
2. In `apps/ai_features/views.py` -> `AIRateLimitMixin` - Already returns True/9999, which is correct. Leave as-is.
3. In `apps/ai_features/models.py` -> `AIConfiguration` - Change `user_rate_limit_per_hour` default from `10` to `9999`.
4. In `config/settings.py` - Already has `AI_RATE_LIMIT_PER_HOUR = 9999`. Correct.
5. In `apps/student/views.py` -> `MultiContextProcessView.post()` - **REMOVE** rate limit check there too:
   ```python
   # REMOVE these lines:
   if not AIUsageLog.check_rate_limit(request.user):
       messages.error(request, '...')
       return redirect('student:ai_center')
   ```
6. In the dashboard template and AI center template - Remove the "remaining requests" badge display or set it to show "unlimited".

### Bug 3: AI Chat Not Persisting as Full Conversation (Chat History UX)
**Problem:** The AI chat in `student/study_room.html` works via AJAX but does NOT render previous messages properly on page reload. The chat should behave like ChatGPT/Gemini - a full continuous conversation page, not a split-pane with limited history.

**Fix Required:**
1. In `apps/student/views.py` -> `StudyRoomView.get()` - Change chat_history query to load ALL messages (remove `[:50]` limit or increase to `[:500]`):
   ```python
   chat_history = AIChat.objects.filter(
       file=file_obj, user=request.user
   ).order_by('created_at')  # Remove the [:50] limit
   ```
2. In `templates/student/study_room.html` - The AI panel should be a **full-page chat experience**, not a small 30% sidebar. Redesign the layout so:
   - The chat occupies the full right panel height
   - All conversation history is rendered with proper scrolling
   - New messages append at the bottom and auto-scroll
   - The chat area is NOT divided/fragmented - it's one continuous thread
3. Ensure chat messages are stored in `AIChat` model and persist between sessions (already working via model).
4. Add Markdown rendering for AI responses in the chat (currently using `linebreaksbr` which doesn't render Markdown properly). Use a JS Markdown library like `marked.js` to render AI bot responses.

### Bug 4: Multi-File Selection in AI Hub (Instructor)
**Problem:** The instructor AI Hub (`instructor/ai_hub.html` + `AIHubView` + `AIGenerateView`) currently shows a dropdown to select ONE file. The user wants to select MULTIPLE files from a course (like the student AI Center already does with checkboxes).

**Fix Required:**
1. In `apps/instructor/views.py` -> `CourseFilesAjaxView.get()` - Already returns file list. Modify to return **HTML checkboxes** (like `CourseFilesAjaxStudentView` does for students):
   ```python
   if request.headers.get('HX-Request'):
       files_list = list(files)
       html = ''
       for f in files_list:
           html += f'''
           <div class="form-check">
               <input class="form-check-input" type="checkbox" name="file_ids" value="{f['id']}" id="file_{f['id']}">
               <label class="form-check-label" for="file_{f['id']}">{f['title']} ({f['file_type']})</label>
           </div>'''
       return HttpResponse(html)
   ```
2. In `apps/instructor/views.py` -> `AIGenerateView.post()` - Change from `file_id = request.POST.get('file_id')` to `file_ids = request.POST.getlist('file_ids')` and process MULTIPLE files by aggregating their text (same pattern as student `MultiContextProcessView`).
3. In `templates/instructor/ai_hub.html` - Replace the single file dropdown with HTMX-loaded checkboxes (same UI pattern as `multi_context_select.html`). Add "Select All / Deselect All" button.

### Bug 5: File Viewer/Reader Missing
**Problem:** When opening files (PDF, images, documents), there is no integrated file viewer. The `study_room.html` uses `<iframe>` for PDFs and `<video>` for videos, but:
- Images have no viewer at all (just shows download link)
- Non-PDF documents (docx, pptx, txt) show only a download link
- No proper image gallery/lightbox

**Fix Required:**
1. In `templates/student/study_room.html` - Add proper file type handling:
   - **Images (.jpg, .png, .gif, .webp):** Display with `<img>` tag with zoom/lightbox functionality
   - **Text files (.txt, .md):** Read and display content inline with proper formatting
   - **DOCX/PPTX:** Show a message "Download to view" with a nice download button (these can't be rendered in browser)
   - **External links:** Properly embed YouTube videos (fix the broken iframe src generation for YouTube)
2. Fix the YouTube embed URL generation in study_room.html - current code is broken:
   ```html
   <!-- CURRENT (BROKEN): -->
   {{ file.external_link|cut:'watch?v='|cut:'https://www.youtube.com/'|cut:'https://youtu.be/' }}
   <!-- FIX: Generate proper embed URL -->
   ```
   Write a Django template filter or JavaScript function to extract YouTube video ID and create proper embed URL: `https://www.youtube.com/embed/VIDEO_ID`
3. Add a simple image viewer modal with zoom capability for image files.

### Bug 6: Reports/Statistics for Students
**Problem:** The system has `InstructorReportsView` for instructors but NO report/statistics view for students. The user wants students to be able to view their own usage reports and statistics.

**Fix Required:**
1. Create `StudentReportsView` in `apps/student/views.py`:
   - Total files viewed
   - Total AI requests (summary, questions, chat)
   - AI usage history
   - Study time per course
   - Progress across all courses
   - Recent activity timeline
2. Create template `templates/student/reports.html` with visual charts/stats
3. Add URL in `apps/student/urls.py`: `path('reports/', views.StudentReportsView.as_view(), name='reports')`
4. Add "Reports" link to student sidebar in `templates/layouts/dashboard_base.html`

### Bug 7: `requirements.txt` File Encoding Issue
**Problem:** The `requirements.txt` file has unusual spacing/encoding (each character separated by spaces). This will cause `pip install -r requirements.txt` to FAIL.

**Fix Required:**
1. Regenerate `requirements.txt` with proper formatting. The key packages needed are:
```
Django==5.2.10
python-dotenv==1.2.1
openai==2.15.0
pdfplumber==0.11.9
python-docx==1.2.0
python-pptx==1.0.2
Markdown==3.10.1
Pillow==12.1.0
openpyxl==3.1.5
gunicorn==24.0.0
psycopg2-binary==2.9.11
celery==5.6.2
redis==7.1.0
requests==2.32.5
django-htmx==1.27.0
django-crispy-forms==2.5
crispy-bootstrap5==2025.6
```
Remove unused heavy dependencies that slow deployment (nltk, numpy, pandas, weasyprint, fonttools, etc.) unless they're actually imported somewhere.

---

## PHASE 2: THE UNIFIED AI HUB (Master System Prompt & Multi-Context Engine)

### 2.1: Implement the Master System Prompt
**Location:** `apps/ai_features/services.py` -> `GeminiService`

The system prompt that gets sent to the AI model should be enhanced to follow this template:

```python
MASTER_SYSTEM_PROMPT = """
ROLE: You are 'The Smart Academic Assistant' in the S-ACM system. Your task is to process composite educational content based on specific requests.

CONTEXT UNDERSTANDING:
- You will receive texts from multiple files, separated by markers [FILE: filename].
- You must cross-reference information between files and cite sources when presenting key information.

ACTION EXECUTION:
- If 'summarize': Provide a structured summary linking all specified files.
- If 'chat': Answer precisely based on information from all combined files.
- If 'quiz': Follow these settings: [Question Type: {quiz_type}, Count: {count}, Score: {points}]. Extract questions from the core of the combined content.

CUSTOM INSTRUCTIONS:
- Follow the user's additional instruction exactly: [{user_instruction}].
- If 'simplify' is selected: Explain in easy language with real-world examples.
- If 'formulas' is selected: Extract equations in LaTeX format and organize them in tables.
- If 'translate' is selected: Keep Arabic text while placing English technical terms in parentheses.

FORMATTING RULES:
- Use full Markdown formatting (headings, tables, lists).
- Be precise, academic, and direct in your answers.
- Always respond in Arabic unless specified otherwise.
"""
```

**Implementation:**
1. In `GeminiService._generate_content()` - Add system message:
   ```python
   messages=[
       {"role": "system", "content": MASTER_SYSTEM_PROMPT},
       {"role": "user", "content": prompt}
   ]
   ```
2. In `GeminiService.ask_document()` - Use the master prompt with `[FILE: name]` markers when aggregating text.
3. In `MultiContextProcessView.post()` - The text aggregation already uses `--- [filename] ---` markers. Change to `[FILE: filename]` for consistency.

### 2.2: Multi-File Selection for Course Context
**Already partially implemented** in student `MultiContextAIView`. Ensure:
1. Course dropdown -> loads files via HTMX -> checkboxes for multiple selection
2. User can select 1+ files
3. Text aggregation uses `[FILE: filename]` markers
4. The combined text is sent with the Master System Prompt

### 2.3: Smart Chips (Intelligence Injection)
**Already implemented** in `multi_context_select.html`. Verify:
1. Chips work correctly (simplify, formulas, translate, etc.)
2. Chip text is appended to `custom_instructions` textarea
3. The custom instructions are passed to the AI service

---

## PHASE 3: COMPREHENSIVE ERROR HANDLING (Try-Catch Everywhere)

### 3.1: Add try-catch to ALL views
Wrap every view method in proper error handling:

```python
def post(self, request, ...):
    try:
        # ... view logic ...
    except SomeSpecificError as e:
        logger.error(f"Specific error: {e}", exc_info=True)
        messages.error(request, 'User-friendly Arabic message')
        return redirect(...)
    except Exception as e:
        logger.error(f"Unexpected error in ViewName: {e}", exc_info=True)
        messages.error(request, 'حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.')
        return redirect(...)
```

**Files to check and add error handling:**
1. `apps/instructor/views.py` - ALL views (especially `AIGenerateView`, `FileUploadView`, `RosterExportExcelView`)
2. `apps/student/views.py` - ALL views (especially `AIChatView`, `MultiContextProcessView`, `StudyRoomView`)
3. `apps/ai_features/views.py` - ALL views
4. `apps/accounts/views/auth.py` - Login, Activation views
5. `apps/notifications/views/` - ALL views
6. `apps/core/context_processors.py` - ALL functions (add bare except with logging)

### 3.2: Add try-catch to Services
1. `apps/ai_features/services.py` -> `GeminiService` methods - Already has good error handling, verify all paths return gracefully.
2. `apps/notifications/services.py` -> `NotificationService` - Wrap all methods.
3. `apps/courses/services.py` -> Wrap all methods.

### 3.3: Add try-catch to Template Tags and Context Processors
1. `apps/core/context_processors.py` - Each function should catch ALL exceptions and return empty/default values (partially done, improve).
2. `apps/core/templatetags/permissions.py` - Wrap in try-catch.

---

## PHASE 4: PRODUCTION READINESS

### 4.1: Security Hardening
1. In `config/settings.py`:
   - Change `SECRET_KEY` default to raise error if not set in production
   - Ensure `DEBUG = False` instructions are clear
   - Add `SECURE_BROWSER_XSS_FILTER = True`
   - Add `X_FRAME_OPTIONS = 'SAMEORIGIN'` (for iframe file viewing)
   - Remove hardcoded email password and API keys from `.env` (it's committed!)
2. In `.gitignore` - Ensure `.env` is listed (it IS listed, but the committed `.env` has real credentials!)
3. Add `whitenoise` for static file serving in production:
   ```python
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # ADD THIS
       ...
   ]
   ```

### 4.2: Static Files for Production
1. Add `whitenoise` to requirements.txt
2. Configure `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`
3. Run `python manage.py collectstatic --noinput`

### 4.3: Database Migrations Check
1. Run `python manage.py makemigrations` - Check for any unmigrated changes
2. Run `python manage.py migrate` - Apply all pending migrations
3. Run `python manage.py check --deploy` - Verify deployment readiness

### 4.4: Error Pages
Verify these templates exist and render correctly:
- `templates/errors/403.html`
- `templates/errors/404.html`
- `templates/errors/500.html`

Add custom error handlers in `config/urls.py`:
```python
handler400 = 'apps.core.views.custom_400'
handler403 = 'apps.core.views.custom_403'
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'
```

---

## PHASE 5: TESTING CHECKLIST (MUST TEST EVERYTHING)

After all fixes, test every single function:

### Authentication Tests
- [ ] Login with academic_id + password
- [ ] Account activation (3-step process)
- [ ] Password reset
- [ ] Password change
- [ ] Logout

### Instructor Tests
- [ ] Dashboard loads with correct stats
- [ ] Course list displays
- [ ] Course detail with files
- [ ] File upload (PDF, DOCX, PPTX, images)
- [ ] File toggle visibility
- [ ] File delete (soft delete to trash)
- [ ] Trash list, restore, permanent delete, empty trash
- [ ] AI Hub - select course -> load files (MULTI-SELECT) -> generate summary
- [ ] AI Hub - generate questions with matrix config
- [ ] AI Hub - archives list, view, delete
- [ ] Student roster view
- [ ] Student roster Excel export
- [ ] Reports page (all tabs)
- [ ] Settings - profile update, password change
- [ ] Notification composer - send to students

### Student Tests
- [ ] Dashboard loads with course progress
- [ ] Course list (current + archived)
- [ ] Course detail with file categories
- [ ] Study Room - PDF viewer working
- [ ] Study Room - Video player working
- [ ] Study Room - Image viewer working
- [ ] Study Room - AI Chat (send message, receive response)
- [ ] Study Room - Quick actions (summarize, quiz, explain)
- [ ] Study Room - Chat history persists on reload
- [ ] Study Room - Unlimited messages (no rate limit)
- [ ] AI Center - course selection -> multi-file selection
- [ ] AI Center - summarize action
- [ ] AI Center - chat/ask action
- [ ] AI Center - quiz generation with config
- [ ] AI Center - smart chips work
- [ ] AI Center - custom instructions
- [ ] Reports/Statistics page
- [ ] Settings - profile update
- [ ] Notification list, detail, mark as read

### AI Service Tests
- [ ] GeminiService initializes with Manus API key
- [ ] Text extraction from PDF
- [ ] Text extraction from DOCX
- [ ] Text extraction from PPTX
- [ ] Text extraction from TXT/MD
- [ ] Summary generation
- [ ] Question generation (MCQ, T/F, short answer)
- [ ] Document Q&A (ask document)
- [ ] Smart chunking for large files
- [ ] File storage (.md files saved correctly)
- [ ] Error handling for API failures
- [ ] Error handling for missing files
- [ ] Master System Prompt is sent correctly

### System Tests
- [ ] All URLs resolve (no 404 for defined routes)
- [ ] CSRF protection works
- [ ] Static files serve correctly
- [ ] Media files serve correctly
- [ ] Error pages render (403, 404, 500)
- [ ] Health check endpoint (/health/) responds
- [ ] Sidebar navigation works on mobile
- [ ] Bottom navigation works on mobile
- [ ] RTL layout is correct
- [ ] System fonts render correctly (no Tajawal loading)
- [ ] No console errors in browser
- [ ] Django `manage.py check --deploy` passes

---

## PHASE 6: GIT COMMIT & DEPLOYMENT

After ALL fixes and tests pass:

1. `git add -A`
2. `git commit -m "fix: comprehensive system fix for production deployment - AI hub multi-file, unlimited chat, font optimization, error handling, reports, file viewer"`
3. Push to remote repository
4. Create/Update Pull Request

---

## IMPORTANT NOTES FOR THE AGENT

1. **DO NOT** break existing functionality while fixing bugs. Test after each change.
2. **DO NOT** remove any existing features. Only add/fix.
3. **DO NOT** change the database schema unless absolutely necessary (avoid new migrations if possible).
4. **ALL** error messages should be in Arabic.
5. **ALL** UI text should be in Arabic (RTL direction).
6. **PRESERVE** the existing design system (CSS variables, color scheme, sidebar layout).
7. The `.env` file contains real API keys - DO NOT commit credentials to git.
8. The `requirements.txt` has encoding issues - FIX IT FIRST before installing.
9. The system uses `Manus API Proxy` (OpenAI-compatible) - NOT direct Google Gemini API.
10. The AI model default is `gpt-4.1-mini` via Manus Proxy at `https://api.manus.im/api/llm-proxy/v1`.
11. **FONT REMOVAL IS CRITICAL** - Remove ALL Tajawal font references. Use system fonts ONLY for speed.
12. **UNLIMITED CHAT IS CRITICAL** - Remove ALL rate limit checks in student AI chat views.
13. After every change, run `python manage.py check` to verify no errors.
