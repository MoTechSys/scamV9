"""
Mixins متقدمة للتحقق من الصلاحيات
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Mixins للتحقق من صلاحيات الوصول للملفات والمقررات
لحل ثغرة IDOR (Insecure Direct Object Reference)
"""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from functools import wraps


class CourseEnrollmentMixin:
    """
    Mixin للتحقق من تسجيل الطالب في المقرر
    
    يتحقق من:
    1. أن الطالب في نفس المستوى المطلوب للمقرر
    2. أن الطالب في نفس التخصص المرتبط بالمقرر
    3. أو أن الطالب في مستوى أعلى (للأرشيف)
    """
    
    def check_course_access(self, user, course):
        """
        التحقق من صلاحية الوصول للمقرر
        
        Args:
            user: المستخدم الحالي
            course: المقرر المطلوب الوصول إليه
            
        Returns:
            bool: True إذا كان الوصول مسموحاً
            
        Raises:
            PermissionDenied: إذا لم يكن الوصول مسموحاً
        """
        # الأدمن والمدرسين لديهم وصول كامل
        if user.is_admin():
            return True
            
        if user.is_instructor():
            # التحقق من أن المدرس معين لهذا المقرر
            from apps.courses.models import InstructorCourse
            if InstructorCourse.objects.filter(
                instructor=user,
                course=course
            ).exists():
                return True
            # المدرسين يمكنهم رؤية المقررات الأخرى للقراءة فقط
            return True
        
        if user.is_student():
            return self._check_student_course_access(user, course)
        
        raise PermissionDenied("ليس لديك صلاحية الوصول لهذا المقرر.")
    
    def _check_student_course_access(self, student, course):
        """
        التحقق من صلاحية الطالب للوصول للمقرر
        
        القواعد:
        1. المقررات الحالية: نفس المستوى + نفس التخصص + الفصل الحالي
        2. المقررات المؤرشفة: مستوى أقل + نفس التخصص + فصل سابق
        """
        if not student.level or not student.major:
            raise PermissionDenied("يجب تحديد المستوى والتخصص للوصول للمقررات.")
        
        # التحقق من التخصص
        course_majors = course.course_majors.values_list('major_id', flat=True)
        if student.major_id not in course_majors:
            raise PermissionDenied("هذا المقرر ليس ضمن تخصصك.")
        
        # التحقق من المستوى
        if course.semester.is_current:
            # المقررات الحالية: يجب أن يكون الطالب في نفس المستوى
            if student.level_id != course.level_id:
                raise PermissionDenied("هذا المقرر ليس ضمن مستواك الدراسي الحالي.")
        else:
            # المقررات المؤرشفة: يجب أن يكون الطالب في مستوى أعلى أو نفس المستوى
            if student.level.level_number < course.level.level_number:
                raise PermissionDenied("لا يمكنك الوصول لمقررات مستويات أعلى.")
        
        return True


class FileAccessMixin(CourseEnrollmentMixin):
    """
    Mixin للتحقق من صلاحية الوصول للملفات
    
    يتحقق من:
    1. صلاحية الوصول للمقرر (عبر CourseEnrollmentMixin)
    2. أن الملف مرئي (للطلاب)
    3. أن الملف غير محذوف
    """
    
    def check_file_access(self, user, file_obj, require_visible=True):
        """
        التحقق من صلاحية الوصول للملف
        
        Args:
            user: المستخدم الحالي
            file_obj: الملف المطلوب الوصول إليه
            require_visible: هل يجب أن يكون الملف مرئياً (للطلاب)
            
        Returns:
            bool: True إذا كان الوصول مسموحاً
            
        Raises:
            PermissionDenied: إذا لم يكن الوصول مسموحاً
        """
        # التحقق من أن الملف غير محذوف
        if file_obj.is_deleted:
            raise PermissionDenied("هذا الملف غير متاح.")
        
        # التحقق من صلاحية الوصول للمقرر
        self.check_course_access(user, file_obj.course)
        
        # للطلاب: التحقق من أن الملف مرئي
        if user.is_student() and require_visible:
            if not file_obj.is_visible:
                raise PermissionDenied("هذا الملف غير متاح حالياً.")
        
        return True


def require_course_enrollment(view_func):
    """
    Decorator للتحقق من تسجيل الطالب في المقرر
    
    يستخدم مع function-based views
    
    Usage:
        @require_course_enrollment
        def my_view(request, course_id):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from apps.courses.models import Course
        
        # البحث عن course_id في الـ kwargs
        course_id = kwargs.get('pk') or kwargs.get('course_id') or kwargs.get('course_pk')
        
        if course_id:
            course = get_object_or_404(Course, pk=course_id)
            mixin = CourseEnrollmentMixin()
            mixin.check_course_access(request.user, course)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_file_access(require_visible=True):
    """
    Decorator للتحقق من صلاحية الوصول للملف
    
    يستخدم مع function-based views
    
    Usage:
        @require_file_access(require_visible=True)
        def download_file(request, file_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from apps.courses.models import LectureFile
            
            # البحث عن file_id في الـ kwargs
            file_id = kwargs.get('pk') or kwargs.get('file_id') or kwargs.get('file_pk')
            
            if file_id:
                file_obj = get_object_or_404(LectureFile, pk=file_id)
                mixin = FileAccessMixin()
                mixin.check_file_access(request.user, file_obj, require_visible)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class SecureFileDownloadMixin(LoginRequiredMixin, FileAccessMixin):
    """
    Mixin جاهز للاستخدام مع Class-based Views لتحميل الملفات بشكل آمن
    
    Usage:
        class MyFileDownloadView(SecureFileDownloadMixin, View):
            def get(self, request, pk):
                file_obj = self.get_secure_file(pk)
                # ... باقي المنطق
    """
    
    def get_secure_file(self, file_id, require_visible=True):
        """
        الحصول على الملف بعد التحقق من الصلاحيات
        
        Args:
            file_id: معرف الملف
            require_visible: هل يجب أن يكون الملف مرئياً
            
        Returns:
            LectureFile: الملف إذا كان الوصول مسموحاً
            
        Raises:
            PermissionDenied: إذا لم يكن الوصول مسموحاً
            Http404: إذا لم يكن الملف موجوداً
        """
        from apps.courses.models import LectureFile
        
        file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
        self.check_file_access(self.request.user, file_obj, require_visible)
        
        return file_obj
