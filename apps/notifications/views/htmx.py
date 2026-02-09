"""
HTMX Endpoints - واجهات ديناميكية بدون تحميل صفحة
S-ACM - Smart Academic Content Management System v3

Endpoints:
- HtmxLevelsForMajor: Cascading dropdown -> المستويات حسب التخصص
- HtmxStudentsCount: عدد المستلمين المستهدفين بناءً على الفلاتر
- HtmxBellUpdate: تحديث أيقونة الجرس في Navbar
- HtmxSearchStudents: بحث عن طالب محدد
- HtmxSearchInstructors: بحث عن دكتور محدد
"""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Q

from ..services import NotificationService


class HtmxLevelsForMajor(LoginRequiredMixin, View):
    """HTMX: جلب المستويات المتاحة لتخصص معين"""

    def get(self, request):
        major_id = request.GET.get('major')
        if not major_id:
            return HttpResponse('<option value="">-- اختر التخصص أولاً --</option>')

        levels = NotificationService.get_levels_for_major(major_id)
        html = '<option value="">-- جميع المستويات --</option>'
        for level in levels:
            html += f'<option value="{level.pk}">{level.level_name}</option>'

        return HttpResponse(html)


class HtmxStudentsCount(LoginRequiredMixin, View):
    """HTMX: عدد المستلمين المستهدفين بناءً على الفلاتر الحالية"""

    def get(self, request):
        major_id = request.GET.get('major')
        level_id = request.GET.get('level')
        course_id = request.GET.get('course')
        target_type = request.GET.get('target_type', 'all_students')
        recipient_type = request.GET.get('recipient_type', 'students')

        count = 0

        if target_type == 'course_students' and course_id:
            count = NotificationService.get_students_count(course_id=course_id)

        elif target_type in ('major_students', 'all_students'):
            count = NotificationService.get_students_count(
                major_id=major_id, level_id=level_id
            )

        elif target_type == 'all_instructors':
            from apps.accounts.models import User, Role
            count = User.objects.filter(
                role__code=Role.INSTRUCTOR,
                account_status='active'
            ).count()

        elif target_type == 'major_instructors' and major_id:
            # عدد الدكاترة حسب التخصص
            from apps.accounts.models import User, Role
            from apps.courses.models import Course
            course_ids = Course.objects.filter(
                course_majors__major_id=major_id,
                is_active=True,
            ).values_list('pk', flat=True)
            instructor_ids = Course.objects.filter(
                pk__in=course_ids,
            ).values_list('instructor_courses__instructor', flat=True).distinct()
            count = User.objects.filter(
                pk__in=instructor_ids,
                role__code=Role.INSTRUCTOR,
                account_status='active',
            ).count()

        elif target_type == 'specific_student' or target_type == 'specific_instructor':
            count = 1 if request.GET.get('specific_user_id') else 0

        elif target_type == 'everyone':
            from apps.accounts.models import User
            count = User.objects.filter(account_status='active').count()

        icon = 'bi-people-fill' if count > 1 else 'bi-person-fill'
        color = 'info' if count > 0 else 'warning'

        html = f'''
        <div class="alert alert-{color} py-2 px-3 mb-0 d-flex align-items-center gap-2">
            <i class="bi {icon}"></i>
            <span>عدد المستلمين المتوقع: <strong>{count}</strong> مستخدم</span>
        </div>
        '''
        return HttpResponse(html)


class HtmxBellUpdate(LoginRequiredMixin, View):
    """HTMX: تحديث أيقونة الجرس + القائمة المنسدلة"""

    def get(self, request):
        unread_count = NotificationService.get_unread_count(request.user)
        recent = NotificationService.get_recent_notifications(request.user, limit=5)

        return render(request, 'notifications/partials/bell_dropdown.html', {
            'unread_count': unread_count,
            'recent_notifications': recent,
        })


class HtmxSearchStudents(LoginRequiredMixin, View):
    """HTMX: بحث عن طالب محدد بالاسم أو الرقم الأكاديمي"""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return HttpResponse('')

        from apps.accounts.models import User, Role
        students = User.objects.filter(
            role__code=Role.STUDENT,
            account_status='active',
        ).filter(
            Q(full_name__icontains=query) | Q(academic_id__icontains=query)
        )[:10]

        html = ''
        for student in students:
            major_name = student.major.major_name if student.major else ''
            level_name = student.level.level_name if student.level else ''
            html += f'''
            <button type="button" class="list-group-item list-group-item-action"
                    onclick="selectUser({student.pk}, '{student.full_name} ({student.academic_id})')">
                <div class="d-flex justify-content-between">
                    <span>{student.full_name}</span>
                    <small class="text-muted">{student.academic_id}</small>
                </div>
                <small class="text-muted">{major_name} - {level_name}</small>
            </button>
            '''

        if not html:
            html = '<div class="text-center text-muted py-2">لا توجد نتائج</div>'

        return HttpResponse(html)


class HtmxSearchInstructors(LoginRequiredMixin, View):
    """HTMX: بحث عن دكتور محدد بالاسم أو الرقم الأكاديمي"""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return HttpResponse('')

        from apps.accounts.models import User, Role
        instructors = User.objects.filter(
            role__code=Role.INSTRUCTOR,
            account_status='active',
        ).filter(
            Q(full_name__icontains=query) | Q(academic_id__icontains=query)
        )[:10]

        html = ''
        for instructor in instructors:
            html += f'''
            <button type="button" class="list-group-item list-group-item-action"
                    onclick="selectUser({instructor.pk}, '{instructor.full_name} ({instructor.academic_id})')">
                <div class="d-flex justify-content-between">
                    <span>{instructor.full_name}</span>
                    <small class="text-muted">{instructor.academic_id}</small>
                </div>
            </button>
            '''

        if not html:
            html = '<div class="text-center text-muted py-2">لا توجد نتائج</div>'

        return HttpResponse(html)
