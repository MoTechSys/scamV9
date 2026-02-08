# S-ACM Enterprise Edition - Architecture Blueprint
# نظام إدارة المحتوى الأكاديمي الذكي - المخطط المعماري الشامل

> **Version:** 2.0 Enterprise  
> **Date:** 2026-02-08  
> **Architect:** Senior AI Software Architect  
> **Stack:** Django 5.x + Bootstrap 5 (RTL) + Google Gemini AI + HTTP Streaming

---

## 1. System Sitemap (Full URL Tree)

```
/                                        [core:home]           Landing Page
/dashboard/                              [core:dashboard_redirect] Role-based redirect
/health/                                 [core:health_check]   Health endpoint
/about/                                  [core:about]          About page
/contact/                                [core:contact]        Contact page

/accounts/
  login/                                 [accounts:login]
  logout/                                [accounts:logout]
  activate/                              [accounts:activation_step1]
  activate/email/                        [accounts:activation_step2]
  activate/verify/                       [accounts:activation_verify_otp]
  activate/password/                     [accounts:activation_set_password]
  password-reset/                        [accounts:password_reset_request]
  password-reset/<token>/                [accounts:password_reset_confirm]
  profile/                               [accounts:profile]
  profile/update/                        [accounts:profile_update]
  profile/change-password/               [accounts:change_password]

/instructor/                                                 ** NEW UNIFIED PREFIX **
  dashboard/                             [instructor:dashboard]
  courses/                               [instructor:course_list]
  courses/<pk>/                          [instructor:course_detail]
  files/upload/                          [instructor:file_upload]
  files/<pk>/update/                     [instructor:file_update]
  files/<pk>/delete/                     [instructor:file_delete]
  files/<pk>/toggle/                     [instructor:file_toggle_visibility]
  files/bulk-action/                     [instructor:file_bulk_action]       ** NEW **
  trash/                                 [instructor:trash_list]             ** NEW **
  trash/<pk>/restore/                    [instructor:trash_restore]          ** NEW **
  trash/<pk>/destroy/                    [instructor:trash_destroy]          ** NEW **
  trash/empty/                           [instructor:trash_empty]            ** NEW **
  ai/                                    [instructor:ai_hub]                 ** NEW **
  ai/generate/                           [instructor:ai_generate]            ** NEW **
  ai/archives/                           [instructor:ai_archives]            ** NEW **
  ai/archives/<pk>/delete/               [instructor:ai_archive_delete]      ** NEW **
  roster/<course_pk>/                    [instructor:student_roster]          ** NEW **
  roster/<course_pk>/export/             [instructor:roster_export_excel]     ** NEW **

/student/                                                    ** NEW UNIFIED PREFIX **
  dashboard/                             [student:dashboard]
  courses/                               [student:course_list]
  courses/<pk>/                          [student:course_detail]
  study-room/<file_pk>/                  [student:study_room]                ** NEW **
  ai/chat/<file_pk>/                     [student:ai_chat]                   ** NEW **
  ai/chat/<file_pk>/clear/               [student:ai_chat_clear]             ** NEW **

/stream/                                                     ** NEW STREAMING ENGINE **
  file/<pk>/                             [streaming:stream_file]
  markdown/<pk>/                         [streaming:stream_markdown]

/ai/                                                         (Legacy - kept for compatibility)
  summarize/<file_id>/                   [ai_features:summarize]
  questions/<file_id>/                   [ai_features:questions]
  ask/<file_id>/                         [ai_features:ask_document]
  ask/<file_id>/clear/                   [ai_features:clear_chat]
  usage/                                 [ai_features:usage_stats]

/notifications/
  list/                                  [notifications:list]
  ...existing notification URLs...

/courses/                                (Legacy - admin routes kept)
  admin/courses/                         [courses:admin_course_list]
  admin/courses/create/                  [courses:admin_course_create]
  admin/courses/<pk>/                    [courses:admin_course_detail]
  admin/courses/<pk>/update/             [courses:admin_course_update]
  admin/courses/<pk>/assign-instructor/  [courses:admin_instructor_assign]
  admin/courses/<pk>/assign-majors/      [courses:admin_course_major_assign]
  files/<pk>/download/                   [courses:file_download]
  files/<pk>/view/                       [courses:file_view]
```

---

## 2. Entity Relationship Map

```
                            +------------------+
                            |      Role        |
                            | (admin/instructor|
                            |  /student)       |
                            +--------+---------+
                                     |
                                     | FK
                                     v
+----------+    FK    +--------------+-------------+    FK    +----------+
|  Major   |<--------+     User                    +-------->|  Level   |
+----------+         | (academic_id, full_name,    |         +----------+
     |               |  role, major, level)        |
     |               +-----+---------+------+------+
     |                     |         |      |
     |                     |         |      +-- UserActivity (1:N)
     |                     |         |
     |                     |         +-- AIChat (1:N)
     |                     |             AIUsageLog (1:N)
     |                     |
     |               InstructorCourse (M:N)
     |                     |
     |                     v
     |    CourseMajor  +---+------------+
     +-------(M:N)---->|    Course      |
                       | (code, name,   |
                       |  level, sem)   |
                       +-------+--------+
                               |
                               | FK (1:N)
                               v
                       +-------+--------+
                       |  LectureFile   |
                       | (title, file,  |
                       |  type, visible,|
                       |  is_deleted)   |
                       +--+----+----+---+
                          |    |    |
                          |    |    +-- AIGeneratedQuestion (1:N)
                          |    +------- AISummary (1:1)
                          +------------ AIChat (1:N)
```

---

## 3. Screen Wireframes

### 3.1 Split-Screen Study Room (Student)

```
+============================================================================+
|  [<] Back to Course    CS101 - Lecture 3: Data Structures    [Download] [>]|
+============================================================================+
|                                    |                                       |
|        CONTENT VIEWER (70%)        |      AI ASSISTANT (30%)              |
|                                    |                                       |
|  +------------------------------+ | +-----------------------------------+ |
|  |                              | | |  [Summarize] [Quiz Me] [Explain]  | |
|  |                              | | +-----------------------------------+ |
|  |     VIDEO PLAYER             | | |                                   | |
|  |     or                       | | |  AI Chat Messages:                | |
|  |     PDF VIEWER               | | |                                   | |
|  |     or                       | | |  [Bot]: This lecture covers       | |
|  |     MARKDOWN RENDERER        | | |  linked lists, stacks, and       | |
|  |                              | | |  queues. Key points:              | |
|  |                              | | |  - Linked list operations O(1)   | |
|  |                              | | |  - Stack LIFO principle          | |
|  |                              | | |  ...                             | |
|  |                              | | |                                   | |
|  |                              | | |  [You]: What is the difference   | |
|  |                              | | |  between stack and queue?        | |
|  |                              | | |                                   | |
|  |                              | | |  [Bot]: Great question! A stack  | |
|  |                              | | |  follows LIFO while a queue      | |
|  |                              | | |  follows FIFO...                 | |
|  |                              | | |                                   | |
|  +------------------------------+ | +-----------------------------------+ |
|                                    | +-----------------------------------+ |
|  [<< Prev]  Page 3/12  [Next >>]  | | Type your question...     [Send] | |
|                                    | +-----------------------------------+ |
+============================================================================+
```

### 3.2 Instructor AI Factory Hub

```
+============================================================================+
|  INSTRUCTOR > AI Hub                                        [? Help]       |
+============================================================================+
|                                                                            |
|  +--- TAB BAR --------------------------------------------------------+   |
|  | [* Generator]  [ Archives ]                                        |   |
|  +--------------------------------------------------------------------+   |
|                                                                            |
|  TAB 1: GENERATOR                                                          |
|  +--------------------------------------------------------------------+   |
|  |  Source Selection                                                   |   |
|  |  +--------------+  +-------------------+                            |   |
|  |  | Course:  [v] |  | File:         [v] |                            |   |
|  |  +--------------+  +-------------------+                            |   |
|  +--------------------------------------------------------------------+   |
|  |  Question Matrix                                                    |   |
|  |  +-------------------+-------------------+------------------------+ |   |
|  |  | Type              | Count             | Score Per Q            | |   |
|  |  +-------------------+-------------------+------------------------+ |   |
|  |  | MCQ               | [5]               | [2.0]                  | |   |
|  |  | True/False        | [5]               | [1.0]                  | |   |
|  |  | Short Answer      | [3]               | [3.0]                  | |   |
|  |  +-------------------+-------------------+------------------------+ |   |
|  |  Total: 13 questions | Max Score: 24.0 points                      |   |
|  +--------------------------------------------------------------------+   |
|  |  Context Notes (Optional)                                           |   |
|  |  +----------------------------------------------------------------+ |   |
|  |  | Focus on Chapter 3 concepts. Difficulty: Medium.               | |   |
|  |  | Include practical examples.                                    | |   |
|  |  +----------------------------------------------------------------+ |   |
|  +--------------------------------------------------------------------+   |
|  |  [Also Generate Summary]                                            |   |
|  |                                                                     |   |
|  |  [========= Generate ==========]                                    |   |
|  +--------------------------------------------------------------------+   |
|                                                                            |
|  TAB 2: ARCHIVES (Hidden until tab clicked)                                |
|  +--------------------------------------------------------------------+   |
|  |  Search: [________________]  Filter: [All Types v]                  |   |
|  +--------------------------------------------------------------------+   |
|  |  Date       | File           | Type      | Items | Actions         |   |
|  |  -----------+----------------+-----------+-------+-----------------|   |
|  |  2026-02-08 | Lecture3.pdf   | Questions | 13    | [View] [Delete] |   |
|  |  2026-02-07 | Lecture2.pdf   | Summary   | -     | [View] [Delete] |   |
|  |  2026-02-05 | Chapter1.docx  | Questions | 10    | [View] [Delete] |   |
|  +--------------------------------------------------------------------+   |
+============================================================================+
```

### 3.3 Student Gamified Dashboard

```
+============================================================================+
|  STUDENT DASHBOARD                                Welcome, Ahmed!          |
+============================================================================+
|                                                                            |
|  +--- RESUME LEARNING CARD -------------------------------------------+   |
|  |  [>] Continue: CS101 - Lecture 5: Trees & Graphs                   |   |
|  |      Last accessed: 2 hours ago | Progress: 65%                     |   |
|  |      [===========================-------] 65%                       |   |
|  +--------------------------------------------------------------------+   |
|                                                                            |
|  +--- MY COURSES (Current Semester) ----------------------------------+   |
|  |                                                                     |   |
|  |  +------------------+  +------------------+  +------------------+   |   |
|  |  | CS101            |  | CS201            |  | MATH101          |   |   |
|  |  | Data Structures  |  | Databases        |  | Calculus I       |   |   |
|  |  | 12 Files         |  | 8 Files          |  | 15 Files         |   |   |
|  |  | [=======---] 70% |  | [====------] 40% |  | [=========-] 90%|   |   |
|  |  | Dr. Mohammed     |  | Dr. Fatima       |  | Dr. Ali          |   |   |
|  |  +------------------+  +------------------+  +------------------+   |   |
|  +--------------------------------------------------------------------+   |
|                                                                            |
|  +--- RECENT FILES ---------------------------------------------------+   |
|  |  [PDF] Lecture 5 - Trees          CS101   Today        [Open]       |   |
|  |  [VID] Lab Session 3              CS201   Yesterday    [Open]       |   |
|  |  [PDF] Homework 2                 MATH101 2 days ago   [Open]       |   |
|  +--------------------------------------------------------------------+   |
|                                                                            |
|  +--- QUICK STATS ---+  +--- AI USAGE ---------+                         |
|  | Courses: 5        |  | Used Today: 3/10      |                         |
|  | Files Viewed: 42  |  | Summaries: 12         |                         |
|  | This Week: 15     |  | Questions: 45         |                         |
|  +-------------------+  +----------------------+                          |
+============================================================================+
```

---

## 4. Functional Flowcharts

### 4.1 File Upload -> Streaming -> AI Pipeline

```
                    INSTRUCTOR
                        |
                [Upload File Form]
                        |
                        v
            +-------------------+
            | FileUploadView    |
            | - Validate form   |
            | - Save to media/  |
            | - Create LectureFile
            | - Log UserActivity|
            | - Send Notification
            +--------+----------+
                     |
          Auto-AI?   |
         +---+-------+--------+
         |                    |
    [YES: auto_generate_ai]  [NO]
         |                    |
         v                    v
  +------+------+        (Upload Done)
  | AI Service  |
  | - Extract text
  | - Generate Summary
  | - Save as .md file
  | - Store path in DB
  +------+------+
         |
         v
    (Summary Ready)


                    STUDENT
                        |
                [Opens Course File]
                        |
                        v
            +-------------------+
            | Study Room View   |
            | Split Screen      |
            +--------+----------+
                     |
        +------------+------------+
        |                         |
   LEFT PANEL (70%)          RIGHT PANEL (30%)
        |                         |
        v                         v
  +-----+------+          +------+-------+
  | StreamFile |          | AI Chat      |
  | View       |          | - Load MD    |
  |            |          | - Send Q     |
  | Range      |          | - Get Answer |
  | Headers    |          | - Context    |
  | Support    |          |   Aware      |
  +-----+------+          +------+-------+
        |                         |
        v                         v
  [Video/PDF/MD             [Summarize]
   Streamed to              [Quiz Me]
   Browser]                 [Ask Question]
                                  |
                                  v
                          +-------+--------+
                          | GeminiService  |
                          | - Round Robin  |
                          |   Key Manager  |
                          | - Smart Chunk  |
                          | - user_notes   |
                          | - Save .md     |
                          +----------------+
```

### 4.2 AI Key Manager - Round Robin Flow

```
  .env File:
  GEMINI_API_KEY_1=key_aaa
  GEMINI_API_KEY_2=key_bbb
  ...
  GEMINI_API_KEY_10=key_jjj

         Request Comes In
              |
              v
     +--------+--------+
     | KeyManager      |
     | - Load all keys |
     | - current_index |
     +--------+--------+
              |
              v
     Pick key[current_index % len(keys)]
              |
              v
     +--------+--------+
     | Try API Call     |
     +--------+--------+
              |
         +----+----+
         |         |
     [Success]  [Rate Limit / Error]
         |         |
         v         v
     Return     Increment index
     Result     Try next key
                (up to len(keys) retries)
```

### 4.3 File-Based AI Storage

```
  AI generates content
         |
         v
  +------+-------+
  | Save to File |
  | media/ai_generated/
  |   summary_{file_id}_{timestamp}.md
  |   questions_{file_id}_{timestamp}.md
  +------+-------+
         |
         v
  +------+-------+
  | Store Path   |
  | in DB Model  |
  | (AISummary   |
  |  .md_file_path)
  +------+-------+
         |
         v
  +------+-------+
  | Serve via    |
  | StreamFileView
  | with Range   |
  | Headers      |
  +--------------+
```

---

## 5. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| AI Key Management | Round-Robin across 10 keys | Maximize throughput, avoid rate limits |
| AI Output Storage | File-based (.md) | Reduce DB bloat, enable streaming |
| Content Delivery | Range Header streaming | Efficient video/PDF delivery |
| UI Framework | Bootstrap 5 RTL + Soft-UI | Arabic-first, mobile responsive |
| Sidebar | Off-canvas mobile, fixed desktop | UX best practice |
| AI Chat | Context-aware with file content | Smart chunking for large files |

---

## 6. New Models (Additions)

### AIGenerationJob (tracks AI generation history)
```python
class AIGenerationJob(models.Model):
    instructor     = FK(User)
    file           = FK(LectureFile)
    job_type       = CharField  # 'summary', 'questions', 'mixed'
    config         = JSONField  # {mcq_count, essay_count, scores, notes}
    md_file_path   = CharField  # Path to generated .md file
    status         = CharField  # 'pending', 'completed', 'failed'
    created_at     = DateTimeField
```

### StudentProgress (tracks study progress)
```python
class StudentProgress(models.Model):
    student        = FK(User)
    file           = FK(LectureFile)
    progress       = IntegerField  # 0-100 percentage
    last_position  = CharField     # video timestamp or page number
    last_accessed  = DateTimeField
```

---

## 7. Security Considerations

1. **IDOR Protection**: All file access goes through `SecureFileDownloadMixin`
2. **Role Enforcement**: `InstructorRequiredMixin` / `StudentRequiredMixin` on all views
3. **Rate Limiting**: AI requests limited to N/hour per user
4. **File Validation**: Extension whitelist, size limits on upload
5. **CSRF**: Django CSRF middleware on all POST endpoints
6. **Audit Trail**: All sensitive actions logged to `AuditLog`

---

*End of Architecture Blueprint*
