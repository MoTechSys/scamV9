"""
Access Control Mixins - أدوات التحقق من الصلاحيات
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Mixins للتحقق من صلاحيات المستخدمين.

ملاحظة مهمة:
    هذا الملف لا يستورد أي ملفات داخلية لتجنب مشاكل الاستيراد الدائري.
    يعتمد فقط على Django's built-in mixins.
"""

from django.contrib.auth.mixins import UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin للتحقق من صلاحيات الأدمن.
    
    يُستخدم مع Class-Based Views لحماية الصفحات التي تتطلب صلاحيات أدمن.
    
    المتطلبات:
        - المستخدم مسجل دخول (authenticated)
        - المستخدم له دور Admin
    
    مثال الاستخدام:
        class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
            template_name = 'admin_panel/dashboard.html'
    """
    
    def test_func(self):
        """التحقق من أن المستخدم أدمن."""
        return self.request.user.is_authenticated and self.request.user.is_admin()


class InstructorRequiredMixin(UserPassesTestMixin):
    """
    Mixin للتحقق من صلاحيات المدرس.
    
    يُستخدم مع Class-Based Views لحماية الصفحات التي تتطلب صلاحيات مدرس.
    
    المتطلبات:
        - المستخدم مسجل دخول (authenticated)
        - المستخدم له دور Instructor أو Admin
    
    ملاحظة:
        الأدمن يمكنه الوصول لصفحات المدرسين أيضاً.
    
    مثال الاستخدام:
        class InstructorDashboardView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
            template_name = 'instructor_panel/dashboard.html'
    """
    
    def test_func(self):
        """التحقق من أن المستخدم مدرس أو أدمن."""
        return self.request.user.is_authenticated and (
            self.request.user.is_instructor() or self.request.user.is_admin()
        )


class StudentRequiredMixin(UserPassesTestMixin):
    """
    Mixin للتحقق من صلاحيات الطالب.
    
    يُستخدم مع Class-Based Views لحماية الصفحات الخاصة بالطلاب فقط.
    
    المتطلبات:
        - المستخدم مسجل دخول (authenticated)
        - المستخدم له دور Student
    
    مثال الاستخدام:
        class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
            template_name = 'student_panel/dashboard.html'
    """
    
    def test_func(self):
        """التحقق من أن المستخدم طالب."""
        return self.request.user.is_authenticated and self.request.user.is_student()
