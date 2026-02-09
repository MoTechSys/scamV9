"""
HTMX Endpoints - واجهات ديناميكية بدون تحميل صفحة
S-ACM - Smart Academic Content Management System

Endpoints:
- HtmxLevelsForMajor: Cascading dropdown -> المستويات حسب التخصص
- HtmxStudentsCount: عدد الطلاب المستهدفين بناءً على الفلاتر
- HtmxBellUpdate: تحديث أيقونة الجرس في Navbar
- HtmxSearchStudents: بحث عن طالب محدد
"""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from ..services import NotificationService


class HtmxLevelsForMajor(LoginRequiredMixin, View):
    """
    HTMX: جلب المستويات المتاحة لتخصص معين
    يُستخدم في Cascading Dropdown

    Usage:
        <select hx-get="{% url 'notifications:htmx_levels' %}"
                hx-target="#level-select"
                hx-trigger="change"
                name="major">
    """

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
    """
    HTMX: عدد الطلاب المستهدفين بناءً على الفلاتر الحالية
    يُحدّث العدد ديناميكياً عند تغيير الفلاتر

    Usage:
        <div hx-get="{% url 'notifications:htmx_students_count' %}"
             hx-trigger="change from:#target-filters"
             hx-include="#target-filters">
    """

    def get(self, request):
        major_id = request.GET.get('major')
        level_id = request.GET.get('level')
        course_id = request.GET.get('course')
        target_type = request.GET.get('target_type', 'all_students')

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
        elif target_type == 'everyone':
            from apps.accounts.models import User
            count = User.objects.filter(account_status='active').count()
        else:
            count = 0

        html = f'''
        <div class="alert alert-info py-2 px-3 mb-0 d-flex align-items-center gap-2">
            <i class="bi bi-people-fill"></i>
            <span>عدد المستلمين المتوقع: <strong>{count}</strong> مستخدم</span>
        </div>
        '''
        return HttpResponse(html)


class HtmxBellUpdate(LoginRequiredMixin, View):
    """
    HTMX: تحديث أيقونة الجرس + القائمة المنسدلة
    يعمل عبر HTMX polling كل 30 ثانية

    Usage:
        <div hx-get="{% url 'notifications:htmx_bell' %}"
             hx-trigger="every 30s"
             hx-swap="innerHTML">
    """

    def get(self, request):
        unread_count = NotificationService.get_unread_count(request.user)
        recent = NotificationService.get_recent_notifications(request.user, limit=5)

        return render(request, 'notifications/partials/bell_dropdown.html', {
            'unread_count': unread_count,
            'recent_notifications': recent,
        })


class HtmxSearchStudents(LoginRequiredMixin, View):
    """
    HTMX: بحث عن طالب محدد بالاسم أو الرقم الأكاديمي
    """

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return HttpResponse('')

        from apps.accounts.models import User, Role
        students = User.objects.filter(
            role__code=Role.STUDENT,
            account_status='active',
        ).filter(
            models_Q_full_name_icontains=query,
        )[:10]

        # بحث بالاسم أو الرقم الأكاديمي
        from django.db.models import Q
        students = User.objects.filter(
            role__code=Role.STUDENT,
            account_status='active',
        ).filter(
            Q(full_name__icontains=query) | Q(academic_id__icontains=query)
        )[:10]

        html = ''
        for student in students:
            html += f'''
            <button type="button" class="list-group-item list-group-item-action"
                    onclick="selectStudent({student.pk}, '{student.full_name} ({student.academic_id})')">
                <div class="d-flex justify-content-between">
                    <span>{student.full_name}</span>
                    <small class="text-muted">{student.academic_id}</small>
                </div>
                <small class="text-muted">{student.major or ''} - {student.level or ''}</small>
            </button>
            '''

        if not html:
            html = '<div class="text-center text-muted py-2">لا توجد نتائج</div>'

        return HttpResponse(html)
