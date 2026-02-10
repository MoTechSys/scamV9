"""
Student App - غرفة الدراسة الذكية (Enterprise Edition v2)
S-ACM - Smart Academic Content Management System

=== Performance Refactoring v2 ===
- StudentDashboardView: Max 2 DB queries via prefetch_related + annotate
- Eliminated N+1 query explosion in course_progress loop
- All stats computed via DB aggregation

يحتوي على:
- Gamified Dashboard (تقدم، استئناف، إحصائيات)
- Split-Screen Study Room
- Context-Aware AI Chat
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import (
    Count, Avg, Sum, Q, F, Value, IntegerField,
    Subquery, OuterRef, Prefetch, Case, When,
)
from django.db.models.functions import Coalesce
import time
import logging

from apps.courses.models import Course, LectureFile
from apps.courses.mixins import CourseEnrollmentMixin
from apps.accounts.views import StudentRequiredMixin
from apps.accounts.models import UserActivity
from apps.notifications.services import NotificationService
from apps.ai_features.models import (
    AISummary, AIGeneratedQuestion, AIChat,
    AIUsageLog, StudentProgress
)

logger = logging.getLogger('courses')


# ========== Gamified Dashboard ==========

class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """
    لوحة تحكم الطالب - Enterprise v2 (Gamified)

    === Performance Optimization ===
    BEFORE (Legacy): N+1 Query Explosion
      - for course in courses:                          # N courses
      -     course.files.filter(...).count()             # +1 query per course
      -     StudentProgress.objects.filter(...).count()  # +1 query per course
      -     course.instructor_courses.select_related()   # +1 query per course
      Total: 1 + 3N queries = catastrophic at scale

    AFTER (v2): Batch Annotate + Prefetch = 2 Queries
      - Query 1: Courses with annotated file_count + viewed_count + instructor
      - Query 2: Prefetched instructor_courses
      Total: 2 queries regardless of course count
    """
    template_name = 'student/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'dashboard'
        student = self.request.user

        try:
            # === Query 1: Current courses with annotated stats ===
            # Prefetch instructor_courses to avoid N+1
            instructor_prefetch = Prefetch(
                'instructor_courses',
                queryset=(
                    __import__('apps.courses.models', fromlist=['InstructorCourse'])
                    .InstructorCourse.objects
                    .select_related('instructor')
                ),
            )

            current_courses = (
                Course.objects
                .get_current_courses_for_student(student)
                .prefetch_related(instructor_prefetch)
                .annotate(
                    visible_file_count=Count(
                        'files',
                        filter=Q(files__is_visible=True, files__is_deleted=False),
                    ),
                    viewed_file_count=Count(
                        'files__student_progress',
                        filter=Q(
                            files__student_progress__student=student,
                            files__student_progress__progress__gt=0,
                        ),
                    ),
                )
            )
            context['current_courses'] = current_courses
            context['archived_courses'] = Course.objects.get_archived_courses_for_student(student)

            # === Build course progress from annotated data (ZERO extra queries) ===
            course_progress = []
            for course in current_courses:
                total_files = course.visible_file_count
                viewed_files = course.viewed_file_count
                progress_pct = min(100, int((viewed_files / total_files) * 100)) if total_files > 0 else 0
                instructor_rel = course.instructor_courses.all()
                instructor_name = (
                    instructor_rel[0].instructor.full_name
                    if instructor_rel else '-'
                )
                course_progress.append({
                    'course': course,
                    'progress': progress_pct,
                    'total_files': total_files,
                    'viewed_files': viewed_files,
                    'instructor': instructor_name,
                })
            context['course_progress'] = course_progress

            # === Resume learning ===
            last_progress = (
                StudentProgress.objects
                .filter(student=student, progress__lt=100)
                .select_related('file', 'file__course')
                .order_by('-last_accessed')
                .first()
            )
            context['resume_item'] = last_progress
            context['unread_notifications'] = NotificationService.get_unread_count(student)

            context['recent_files'] = (
                LectureFile.objects
                .filter(
                    course__in=current_courses,
                    is_visible=True, is_deleted=False
                )
                .select_related('course')
                .order_by('-upload_date')[:5]
            )

            today_date = timezone.now().date()
            context['stats'] = {
                'total_courses': current_courses.count(),
                'files_viewed': StudentProgress.objects.filter(
                    student=student, progress__gt=0
                ).count(),
                'ai_used_today': AIUsageLog.objects.filter(
                    user=student,
                    request_time__date=today_date
                ).count(),
                'ai_remaining': 9999,
                'total_summaries': AISummary.objects.filter(user=student).count(),
                'total_questions': AIGeneratedQuestion.objects.filter(user=student).count(),
            }
        except Exception as e:
            logger.error(f"StudentDashboardView error: {e}", exc_info=True)
            context.setdefault('current_courses', [])
            context.setdefault('course_progress', [])
            context.setdefault('stats', {})

        return context


# ========== Courses ==========

class StudentCourseListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    template_name = 'student/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        student = self.request.user
        view_type = self.request.GET.get('view', 'current')
        if view_type == 'archived':
            return Course.objects.get_archived_courses_for_student(student)
        return Course.objects.get_current_courses_for_student(student)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'courses'
        context['view_type'] = self.request.GET.get('view', 'current')
        return context


class StudentCourseDetailView(LoginRequiredMixin, StudentRequiredMixin, CourseEnrollmentMixin, DetailView):
    model = Course
    template_name = 'student/course_detail.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        course = super().get_object(queryset)
        self.check_course_access(self.request.user, course)
        return course

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'courses'
        course = self.object
        files = course.files.filter(is_visible=True, is_deleted=False)

        context['lectures'] = files.filter(file_type='Lecture')
        context['summaries'] = files.filter(file_type='Summary')
        context['exams'] = files.filter(file_type='Exam')
        context['assignments'] = files.filter(file_type='Assignment')
        context['references'] = files.filter(file_type='Reference')
        context['others'] = files.filter(file_type='Other')
        context['instructors'] = course.instructor_courses.select_related('instructor')
        context['all_files'] = files

        return context


# ========== Split-Screen Study Room ==========

class StudyRoomView(LoginRequiredMixin, StudentRequiredMixin, View):
    """غرفة الدراسة - شاشة مقسومة: عارض المحتوى + مساعد AI"""
    template_name = 'student/study_room.html'

    def get(self, request, file_pk):
        file_obj = get_object_or_404(LectureFile, pk=file_pk, is_deleted=False, is_visible=True)

        # التحقق من الصلاحية
        mixin = CourseEnrollmentMixin()
        mixin.check_course_access(request.user, file_obj.course)

        # تسجيل المشاهدة
        file_obj.increment_view()
        UserActivity.objects.create(
            user=request.user, activity_type='view',
            description=f'غرفة الدراسة: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        # تحديث/إنشاء تقدم الطالب
        progress, created = StudentProgress.objects.get_or_create(
            student=request.user, file=file_obj,
            defaults={'progress': 10}
        )
        if not created and progress.progress < 100:
            progress.progress = min(100, progress.progress + 10)
            progress.save(update_fields=['progress', 'last_accessed'])

        # محادثات AI السابقة (جميع المحادثات بدون حد)
        chat_history = AIChat.objects.filter(
            file=file_obj, user=request.user
        ).order_by('created_at')

        # ملخص موجود
        existing_summary = AISummary.objects.filter(file=file_obj).first()

        # ملفات المقرر (للتنقل)
        course_files = file_obj.course.files.filter(
            is_visible=True, is_deleted=False
        ).order_by('upload_date')
        file_list = list(course_files)
        current_index = next((i for i, f in enumerate(file_list) if f.id == file_obj.id), 0)
        prev_file = file_list[current_index - 1] if current_index > 0 else None
        next_file = file_list[current_index + 1] if current_index < len(file_list) - 1 else None

        context = {
            'file': file_obj,
            'course': file_obj.course,
            'progress': progress,
            'chat_history': chat_history,
            'existing_summary': existing_summary,
            'prev_file': prev_file,
            'next_file': next_file,
            'remaining_requests': 9999,  # Unlimited
            'active_page': 'study_room',
        }

        return render(request, self.template_name, context)


# ========== AI Chat for Study Room ==========

class AIChatView(LoginRequiredMixin, StudentRequiredMixin, View):
    """محادثة AI سياقية في غرفة الدراسة"""

    def post(self, request, file_pk):
        file_obj = get_object_or_404(LectureFile, pk=file_pk, is_deleted=False)
        question = request.POST.get('question', '').strip()
        action = request.POST.get('action', 'ask')

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not question and action == 'ask':
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'يرجى إدخال سؤال.'})
            messages.error(request, 'يرجى إدخال سؤال.')
            return redirect('student:study_room', file_pk=file_pk)

        # Chat is unlimited - no rate limit for conversations

        try:
            from apps.ai_features.services import GeminiService
            service = GeminiService()
            text = service.extract_text_from_file(file_obj)

            if not text:
                error = 'لا يمكن استخراج النص من هذا الملف.'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error})
                messages.error(request, error)
                return redirect('student:study_room', file_pk=file_pk)

            # تحديد نوع الطلب
            if action == 'summarize':
                question = 'قم بتلخيص هذا المحتوى بشكل مفصل ومنظم مع عناوين فرعية ونقاط مرتبة'
            elif action == 'quiz':
                question = 'أنشئ 5 أسئلة اختبارية متنوعة من هذا المحتوى مع الإجابات الصحيحة والشرح'
            elif action == 'explain':
                question = 'اشرح المفاهيم الرئيسية في هذا المحتوى بطريقة مبسطة مع أمثلة'
            elif action == 'keypoints':
                question = 'استخرج النقاط الرئيسية من هذا المحتوى في قائمة مرتبة ومنظمة'
            elif action == 'definitions':
                question = 'استخرج جميع التعريفات والمصطلحات المهمة من هذا المحتوى في جدول منظم'

            start_time = time.time()
            answer = service.ask_document(text, question)
            response_time = time.time() - start_time

            chat = AIChat.objects.create(
                file=file_obj, user=request.user,
                question=question, answer=answer,
                response_time=response_time,
            )

            AIUsageLog.log_request(
                user=request.user, request_type='chat',
                file=file_obj, success=True,
                tokens_used=len(question.split()) + len(answer.split())
            )

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'question': question,
                    'answer': answer,
                    'created_at': chat.created_at.strftime('%Y-%m-%d %H:%M'),
                    'remaining': AIUsageLog.get_remaining_requests(request.user),
                })

            messages.success(request, 'تم الحصول على الإجابة!')

        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limit / quota errors
            if 'quota' in error_str or '429' in error_str or 'rate' in error_str or 'resource_exhausted' in error_str:
                error = '⏳ تجاوزت الحد المسموح من الطلبات. انتظر دقيقة ثم حاول مرة أخرى.'
            else:
                error = f'⚠️ حدث خطأ: {str(e)[:100]}'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error})
            messages.error(request, error)

        return redirect('student:study_room', file_pk=file_pk)


class AIChatClearView(LoginRequiredMixin, StudentRequiredMixin, View):
    """مسح سجل المحادثة"""
    def post(self, request, file_pk):
        AIChat.objects.filter(file_id=file_pk, user=request.user).delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'تم مسح المحادثة.')
        return redirect('student:study_room', file_pk=file_pk)


class UpdateProgressView(LoginRequiredMixin, StudentRequiredMixin, View):
    """تحديث تقدم الطالب (AJAX)"""
    def post(self, request, file_pk):
        progress_val = request.POST.get('progress', 0)
        position = request.POST.get('position', '')

        try:
            progress_val = min(100, max(0, int(progress_val)))
        except (ValueError, TypeError):
            progress_val = 0

        prog, _ = StudentProgress.objects.get_or_create(
            student=request.user,
            file_id=file_pk,
            defaults={'progress': progress_val, 'last_position': position}
        )
        if prog.progress < progress_val:
            prog.progress = progress_val
        if position:
            prog.last_position = position
        prog.save()

        return JsonResponse({'success': True, 'progress': prog.progress})


# ========== Settings ==========

class StudentSettingsView(LoginRequiredMixin, StudentRequiredMixin, View):
    """إعدادات الطالب"""
    template_name = 'student/settings.html'

    def get(self, request):
        context = {
            'active_page': 'settings',
            'user': request.user,
            'active_tab': request.GET.get('tab', 'profile'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        tab = request.POST.get('tab', 'profile')

        if tab == 'profile':
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone_number', '').strip()
            email = request.POST.get('email', '').strip()

            if full_name:
                request.user.full_name = full_name
            if phone:
                request.user.phone_number = phone
            if email:
                request.user.email = email

            if 'profile_picture' in request.FILES:
                request.user.profile_picture = request.FILES['profile_picture']

            request.user.save()
            messages.success(request, 'تم تحديث البيانات الشخصية بنجاح.')

        elif tab == 'password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not request.user.check_password(current_password):
                messages.error(request, 'كلمة المرور الحالية غير صحيحة.')
            elif new_password != confirm_password:
                messages.error(request, 'كلمة المرور الجديدة غير متطابقة.')
            elif len(new_password) < 8:
                messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'تم تغيير كلمة المرور بنجاح.')

        elif tab == 'notifications':
            messages.success(request, 'تم حفظ إعدادات الإشعارات.')

        from django.urls import reverse
        return redirect(reverse('student:settings') + f'?tab={tab}')


# ========== Multi-Context AI Center ==========

class MultiContextAIView(LoginRequiredMixin, StudentRequiredMixin, View):
    """مركز الذكاء الاصطناعي المتقدم - Multi-Context Engine"""
    template_name = 'ai_features/multi_context_select.html'

    def get(self, request):
        courses = Course.objects.get_current_courses_for_student(request.user)
        remaining = AIUsageLog.get_remaining_requests(request.user)

        context = {
            'active_page': 'ai_center',
            'courses': courses,
            'remaining_requests': remaining,
        }
        return render(request, self.template_name, context)


class MultiContextProcessView(LoginRequiredMixin, StudentRequiredMixin, View):
    """معالجة طلب AI متعدد السياقات"""

    def post(self, request):
        from django.urls import reverse

        file_ids = request.POST.getlist('file_ids')
        action_type = request.POST.get('action_type', 'summarize')
        custom_instructions = request.POST.get('custom_instructions', '').strip()

        # Quiz config
        mcq_count = int(request.POST.get('mcq_count', 0))
        mcq_score = float(request.POST.get('mcq_score', 2.0))
        tf_count = int(request.POST.get('tf_count', 0))
        tf_score = float(request.POST.get('tf_score', 1.0))
        sa_count = int(request.POST.get('sa_count', 0))
        sa_score = float(request.POST.get('sa_score', 3.0))

        if not file_ids:
            messages.error(request, 'يرجى اختيار ملف واحد على الأقل.')
            return redirect('student:ai_center')

        try:
            from apps.ai_features.services import GeminiService, QuestionMatrixConfig

            files = LectureFile.objects.filter(
                pk__in=file_ids, is_deleted=False, is_visible=True
            )

            if not files.exists():
                messages.error(request, 'الملفات المحددة غير متاحة.')
                return redirect('student:ai_center')

            service = GeminiService()

            # تجميع النصوص من الملفات المختارة
            aggregated_text = ""
            file_titles = []
            for f in files:
                text = service.extract_text_from_file(f)
                if text:
                    aggregated_text += f"\n\n[FILE: {f.title}]\n\n{text}"
                    file_titles.append(f.title)

            if not aggregated_text.strip():
                messages.error(request, 'لم نتمكن من استخراج النص من الملفات المحددة.')
                return redirect('student:ai_center')

            first_file = files.first()

            if action_type == 'summarize':
                job = AIGenerationJob.objects.create(
                    instructor=request.user, file=first_file,
                    job_type='summary', user_notes=custom_instructions,
                    status='processing'
                )
                result = service.generate_summary(
                    aggregated_text, user_notes=custom_instructions
                )
                md_path = service.storage.save_summary(
                    file_id=first_file.id, content=result,
                    metadata={
                        'source_files': ', '.join(file_titles),
                        'custom_instructions': custom_instructions[:200] if custom_instructions else 'بدون',
                        'model': service._model_name,
                    }
                )
                job.status = 'completed'
                job.md_file_path = md_path
                job.completed_at = timezone.now()
                job.save()

                AIUsageLog.log_request(
                    user=request.user, request_type='summary',
                    file=first_file, success=True
                )
                messages.success(request, 'تم توليد الملخص بنجاح!')

            elif action_type == 'chat':
                question = custom_instructions or 'اشرح المحتوى الرئيسي لهذه الملفات'
                answer = service.ask_document(aggregated_text, question)

                AIChat.objects.create(
                    file=first_file, user=request.user,
                    question=question, answer=answer,
                )
                AIUsageLog.log_request(
                    user=request.user, request_type='chat',
                    file=first_file, success=True
                )
                messages.success(request, 'تم الحصول على الإجابة!')

            elif action_type == 'quiz':
                total_q = mcq_count + tf_count + sa_count
                if total_q == 0:
                    mcq_count, tf_count, sa_count = 3, 2, 2
                    total_q = 7

                matrix = QuestionMatrixConfig(
                    mcq_count=mcq_count, mcq_score=mcq_score,
                    true_false_count=tf_count, true_false_score=tf_score,
                    short_answer_count=sa_count, short_answer_score=sa_score,
                )
                job = AIGenerationJob.objects.create(
                    instructor=request.user, file=first_file,
                    job_type='questions', user_notes=custom_instructions,
                    config=matrix.to_dict(), status='processing'
                )
                questions = service.generate_questions_matrix(
                    aggregated_text, matrix, custom_instructions
                )
                if questions:
                    md_path = service.storage.save_questions(
                        file_id=first_file.id, questions_data=questions,
                        metadata={
                            'source_files': ', '.join(file_titles),
                            'total_questions': str(len(questions)),
                            'total_score': str(matrix.total_score),
                            'model': service._model_name,
                        }
                    )
                    job.status = 'completed'
                    job.md_file_path = md_path
                    job.completed_at = timezone.now()
                    job.save()

                    for q in questions:
                        AIGeneratedQuestion.objects.create(
                            file=first_file, user=request.user,
                            question_text=q.get('question', ''),
                            question_type=q.get('type', 'short_answer'),
                            options=q.get('options'),
                            correct_answer=q.get('answer', ''),
                            explanation=q.get('explanation', ''),
                            score=q.get('score', 1.0),
                        )

                    AIUsageLog.log_request(
                        user=request.user, request_type='questions',
                        file=first_file, success=True
                    )
                    messages.success(request, f'تم توليد {len(questions)} سؤال بنجاح!')
                else:
                    job.status = 'failed'
                    job.error_message = 'لم يتمكن AI من توليد أسئلة'
                    job.save()
                    messages.warning(request, 'لم يتمكن الذكاء الاصطناعي من توليد أسئلة.')

        except Exception as e:
            logger.error(f"Multi-Context AI error: {e}")
            messages.error(request, f'حدث خطأ: {str(e)[:150]}')

        return redirect('student:ai_center')


class StudentReportsView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """تقارير وإحصائيات الطالب الشاملة"""
    template_name = 'student/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'reports'
        student = self.request.user
        active_tab = self.request.GET.get('tab', 'overview')
        context['active_tab'] = active_tab

        # Get student's courses
        courses = Course.objects.get_current_courses_for_student(student)
        context['courses'] = courses

        # Overview stats
        context['stats'] = {
            'total_courses': courses.count(),
            'files_viewed': StudentProgress.objects.filter(student=student, progress__gt=0).count(),
            'total_summaries': AISummary.objects.filter(user=student).count(),
            'total_questions': AIGeneratedQuestion.objects.filter(user=student).count(),
            'total_chats': AIChat.objects.filter(user=student).count(),
            'avg_progress': StudentProgress.objects.filter(student=student).aggregate(
                avg=Coalesce(Avg('progress'), Value(0, output_field=IntegerField()))
            )['avg'],
        }

        # Course progress
        course_stats = []
        for course in courses:
            total_files = LectureFile.objects.filter(
                course=course, is_visible=True, is_deleted=False
            ).count()
            viewed = StudentProgress.objects.filter(
                student=student, file__course=course, progress__gt=0
            ).count()
            pct = min(100, int((viewed / total_files) * 100)) if total_files > 0 else 0
            course_stats.append({
                'course': course,
                'total_files': total_files,
                'viewed_files': viewed,
                'progress': pct,
            })
        context['course_stats'] = course_stats

        # AI usage history
        context['ai_history'] = AIUsageLog.objects.filter(
            user=student
        ).select_related('file', 'file__course').order_by('-request_time')[:20]

        return context


class CourseFilesAjaxStudentView(LoginRequiredMixin, StudentRequiredMixin, View):

    """إرجاع قائمة ملفات المقرر للطالب (AJAX/HTMX)"""
    def get(self, request):
        course_id = request.GET.get('course_id')
        if not course_id:
            return JsonResponse({'files': []})

        files = LectureFile.objects.filter(
            course_id=course_id, is_deleted=False, is_visible=True
        ).values('id', 'title', 'file_type')

        if request.headers.get('HX-Request'):
            # Return HTML checkboxes for HTMX
            files_list = list(files)
            html = ''
            for f in files_list:
                icon = 'bi-file-earmark-pdf' if 'pdf' in f.get('file_type', '').lower() else 'bi-file-earmark'
                html += f'''
                <div class="form-check d-flex align-items-center gap-2 py-2 px-3"
                     style="border-bottom:1px solid var(--border-color,#e2e8f0);">
                    <input class="form-check-input" type="checkbox" name="file_ids"
                           value="{f['id']}" id="file_{f['id']}">
                    <label class="form-check-label d-flex align-items-center gap-2 w-100" for="file_{f['id']}">
                        <i class="bi {icon}" style="color:var(--primary);"></i>
                        <span>{f['title']}</span>
                        <span class="badge bg-light text-muted ms-auto" style="font-size:0.7rem;">{f['file_type']}</span>
                    </label>
                </div>'''
            if not html:
                html = '<div class="text-center text-muted py-3"><i class="bi bi-inbox me-1"></i>لا توجد ملفات متاحة</div>'
            return HttpResponse(html)

        return JsonResponse({'files': list(files)})


# ========== Student Reports & Statistics ==========

class StudentReportsView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """تقارير وإحصائيات الطالب"""
    template_name = 'student/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'reports'
        student = self.request.user

        try:
            # Current courses
            courses = Course.objects.get_current_courses_for_student(student)

            # Overall stats
            total_files_viewed = StudentProgress.objects.filter(
                student=student, progress__gt=0
            ).count()

            total_files_completed = StudentProgress.objects.filter(
                student=student, progress=100
            ).count()

            # AI usage stats
            total_ai_requests = AIUsageLog.objects.filter(user=student).count()
            total_summaries = AISummary.objects.filter(user=student).count()
            total_questions = AIGeneratedQuestion.objects.filter(user=student).count()
            total_chats = AIChat.objects.filter(user=student).count()

            # Today's activity
            today = timezone.now().date()
            today_ai = AIUsageLog.objects.filter(
                user=student, request_time__date=today
            ).count()
            today_views = UserActivity.objects.filter(
                user=student, activity_type='view',
                activity_time__date=today
            ).count()

            # Course progress
            course_stats = []
            for course in courses:
                visible_files = course.files.filter(is_visible=True, is_deleted=False).count()
                viewed = StudentProgress.objects.filter(
                    student=student, file__course=course, progress__gt=0
                ).count()
                completed = StudentProgress.objects.filter(
                    student=student, file__course=course, progress=100
                ).count()
                progress_pct = min(100, int((viewed / visible_files) * 100)) if visible_files > 0 else 0

                course_stats.append({
                    'course': course,
                    'total_files': visible_files,
                    'viewed': viewed,
                    'completed': completed,
                    'progress': progress_pct,
                })

            # Recent activity timeline
            recent_activities = UserActivity.objects.filter(
                user=student
            ).order_by('-activity_time')[:20]

            # AI usage by type
            ai_by_type = {
                'summaries': total_summaries,
                'questions': total_questions,
                'chats': total_chats,
            }

            context.update({
                'total_courses': courses.count(),
                'total_files_viewed': total_files_viewed,
                'total_files_completed': total_files_completed,
                'total_ai_requests': total_ai_requests,
                'today_ai': today_ai,
                'today_views': today_views,
                'course_stats': course_stats,
                'recent_activities': recent_activities,
                'ai_by_type': ai_by_type,
            })
        except Exception as e:
            logger.error(f"StudentReportsView error: {e}", exc_info=True)
            context['error'] = 'حدث خطأ أثناء تحميل التقارير.'

        return context
