"""
HTMX Partial Views - عروض جزئية للـ HTMX
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Views جزئية تُرجع HTML fragments للتحديث الديناميكي
بدون إعادة تحميل الصفحة الكاملة

الاستخدام:
- يتم استدعاء هذه الـ Views من الـ Frontend باستخدام HTMX
- تُرجع HTML fragments بدلاً من صفحات كاملة
- تدعم التحديث الجزئي والتفاعل السلس
"""

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.db.models import Q

from ..models import Course, LectureFile
from ..services import EnhancedCourseService, EnhancedFileService
from apps.accounts.decorators import student_required, instructor_required


# ========== File List Partials ==========

@login_required
@require_http_methods(["GET"])
def htmx_file_list(request, course_id):
    """
    عرض قائمة الملفات بشكل جزئي
    
    يستخدم مع HTMX لتحديث قائمة الملفات بدون إعادة تحميل الصفحة
    
    HTMX Usage:
        <div hx-get="{% url 'courses:htmx_file_list' course.id %}"
             hx-trigger="load, fileUploaded from:body"
             hx-swap="innerHTML">
        </div>
    """
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    # تحديد ما إذا كان يجب تضمين الملفات المخفية
    include_hidden = user.is_admin() or user.is_instructor()
    
    # الحصول على الملفات مصنفة
    files_by_type = EnhancedFileService.get_files_by_type(course, include_hidden)
    
    # فلترة حسب النوع إذا تم تحديده
    file_type = request.GET.get('type')
    if file_type and file_type in files_by_type:
        files = files_by_type[file_type]
    else:
        files = EnhancedFileService.get_course_files(course, include_hidden)
    
    context = {
        'files': files,
        'files_by_type': files_by_type,
        'course': course,
        'selected_type': file_type,
        'can_manage': user.is_admin() or user.is_instructor()
    }
    
    return render(request, 'courses/partials/file_list.html', context)


@login_required
@require_http_methods(["GET"])
def htmx_file_search(request, course_id):
    """
    بحث في الملفات بشكل جزئي
    
    يستخدم مع HTMX للبحث الفوري مع debounce
    
    HTMX Usage:
        <input type="search" 
               hx-get="{% url 'courses:htmx_file_search' course.id %}"
               hx-trigger="keyup changed delay:300ms"
               hx-target="#file-results">
    """
    course = get_object_or_404(Course, pk=course_id)
    query = request.GET.get('q', '').strip()
    
    user = request.user
    include_hidden = user.is_admin() or user.is_instructor()
    
    files = EnhancedFileService.get_course_files(course, include_hidden)
    
    if query:
        files = files.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    context = {
        'files': files,
        'query': query,
        'course': course,
        'can_manage': user.is_admin() or user.is_instructor()
    }
    
    return render(request, 'courses/partials/file_search_results.html', context)


# ========== File Actions Partials ==========

@login_required
@require_http_methods(["POST"])
def htmx_toggle_visibility(request, file_id):
    """
    تبديل ظهور الملف بشكل جزئي
    
    يُرجع الزر المحدث فقط بدلاً من إعادة تحميل الصفحة
    
    HTMX Usage:
        <button hx-post="{% url 'courses:htmx_toggle_visibility' file.id %}"
                hx-swap="outerHTML">
            ...
        </button>
    """
    file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
    
    # التحقق من الصلاحية
    user = request.user
    if not (user.is_admin() or (user.is_instructor() and file_obj.uploader == user)):
        return HttpResponse("غير مصرح", status=403)
    
    # تبديل الظهور
    new_visibility = EnhancedFileService.toggle_visibility(file_obj, user)
    
    context = {
        'file': file_obj,
        'is_visible': new_visibility
    }
    
    return render(request, 'courses/partials/visibility_button.html', context)


@login_required
@require_http_methods(["DELETE", "POST"])
def htmx_delete_file(request, file_id):
    """
    حذف ملف بشكل جزئي
    
    يُرجع رسالة نجاح أو يحذف العنصر من DOM
    
    HTMX Usage:
        <button hx-delete="{% url 'courses:htmx_delete_file' file.id %}"
                hx-confirm="هل أنت متأكد من حذف هذا الملف؟"
                hx-target="closest .file-item"
                hx-swap="outerHTML">
            ...
        </button>
    """
    file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
    
    # التحقق من الصلاحية
    user = request.user
    if not (user.is_admin() or (user.is_instructor() and file_obj.uploader == user)):
        return HttpResponse("غير مصرح", status=403)
    
    # حذف الملف
    success = EnhancedFileService.delete_file(file_obj, user)
    
    if success:
        # إرجاع عنصر فارغ ليتم حذفه من DOM
        response = HttpResponse("")
        response['HX-Trigger'] = 'fileDeleted'
        return response
    else:
        return HttpResponse("فشل الحذف", status=500)


# ========== Course Statistics Partial ==========

@login_required
@require_http_methods(["GET"])
def htmx_course_stats(request, course_id):
    """
    عرض إحصائيات المقرر بشكل جزئي
    
    يستخدم للتحديث الدوري للإحصائيات
    
    HTMX Usage:
        <div hx-get="{% url 'courses:htmx_course_stats' course.id %}"
             hx-trigger="every 30s"
             hx-swap="innerHTML">
        </div>
    """
    course = get_object_or_404(Course, pk=course_id)
    stats = EnhancedCourseService.get_course_statistics(course)
    
    context = {
        'course': course,
        'stats': stats
    }
    
    return render(request, 'courses/partials/course_stats.html', context)


# ========== Notifications Partial ==========

@login_required
@require_http_methods(["GET"])
def htmx_notifications(request):
    """
    عرض الإشعارات بشكل جزئي
    
    يستخدم للتحديث الدوري للإشعارات في الـ Navbar
    
    HTMX Usage:
        <div hx-get="{% url 'courses:htmx_notifications' %}"
             hx-trigger="every 30s"
             hx-swap="innerHTML">
        </div>
    """
    from apps.notifications.models import NotificationManager
    
    user = request.user
    notifications = NotificationManager.get_recent_notifications(user, limit=5)
    unread_count = NotificationManager.get_unread_count(user)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    
    return render(request, 'partials/notifications_dropdown.html', context)


# ========== AI Features Partials ==========

@login_required
@require_http_methods(["POST"])
def htmx_generate_summary(request, file_id):
    """
    توليد تلخيص للملف بشكل جزئي
    
    يستخدم مع HTMX لتوليد التلخيص بدون إعادة تحميل الصفحة
    
    HTMX Usage:
        <button hx-post="{% url 'courses:htmx_generate_summary' file.id %}"
                hx-target="#summary-container"
                hx-indicator=".summary-loading">
            توليد تلخيص
        </button>
    """
    from apps.ai_features.services import GeminiService
    
    file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
    
    # التحقق من صلاحية الوصول
    user = request.user
    allowed, error = EnhancedFileService.check_file_access(user, file_obj)
    if not allowed:
        return HttpResponse(f"<div class='alert alert-danger'>{error}</div>")
    
    # توليد التلخيص
    service = GeminiService()
    text = service.extract_text_from_file(file_obj)
    
    if not text:
        return HttpResponse("<div class='alert alert-warning'>لا يمكن استخراج النص من هذا الملف</div>")
    
    summary = service.generate_summary(text)
    
    context = {
        'summary': summary,
        'file': file_obj
    }
    
    return render(request, 'ai_features/partials/summary_result.html', context)


@login_required
@require_http_methods(["POST"])
def htmx_generate_questions(request, file_id):
    """
    توليد أسئلة من الملف بشكل جزئي
    
    HTMX Usage:
        <button hx-post="{% url 'courses:htmx_generate_questions' file.id %}"
                hx-target="#questions-container"
                hx-indicator=".questions-loading">
            توليد أسئلة
        </button>
    """
    from apps.ai_features.services import GeminiService
    
    file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
    
    # التحقق من صلاحية الوصول
    user = request.user
    allowed, error = EnhancedFileService.check_file_access(user, file_obj)
    if not allowed:
        return HttpResponse(f"<div class='alert alert-danger'>{error}</div>")
    
    # الحصول على المعاملات
    question_type = request.POST.get('type', 'mixed')
    num_questions = int(request.POST.get('count', 5))
    
    # توليد الأسئلة
    service = GeminiService()
    text = service.extract_text_from_file(file_obj)
    
    if not text:
        return HttpResponse("<div class='alert alert-warning'>لا يمكن استخراج النص من هذا الملف</div>")
    
    questions = service.generate_questions(text, question_type, num_questions)
    
    context = {
        'questions': questions,
        'file': file_obj
    }
    
    return render(request, 'ai_features/partials/questions_result.html', context)


@login_required
@require_http_methods(["POST"])
def htmx_ask_document(request, file_id):
    """
    طرح سؤال على المستند بشكل جزئي
    
    HTMX Usage:
        <form hx-post="{% url 'courses:htmx_ask_document' file.id %}"
              hx-target="#answer-container"
              hx-indicator=".answer-loading">
            <input type="text" name="question" placeholder="اكتب سؤالك...">
            <button type="submit">اسأل</button>
        </form>
    """
    from apps.ai_features.services import GeminiService
    
    file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
    
    # التحقق من صلاحية الوصول
    user = request.user
    allowed, error = EnhancedFileService.check_file_access(user, file_obj)
    if not allowed:
        return HttpResponse(f"<div class='alert alert-danger'>{error}</div>")
    
    question = request.POST.get('question', '').strip()
    if not question:
        return HttpResponse("<div class='alert alert-warning'>يرجى كتابة سؤال</div>")
    
    # الإجابة على السؤال
    service = GeminiService()
    text = service.extract_text_from_file(file_obj)
    
    if not text:
        return HttpResponse("<div class='alert alert-warning'>لا يمكن استخراج النص من هذا الملف</div>")
    
    answer = service.ask_document(text, question)
    
    context = {
        'question': question,
        'answer': answer,
        'file': file_obj
    }
    
    return render(request, 'ai_features/partials/answer_result.html', context)
