"""
خدمات إدارة المحتوى والملفات
S-ACM - Smart Academic Content Management System
"""

import os
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import slugify
from datetime import datetime


class FileService:
    """خدمة إدارة الملفات"""
    
    ALLOWED_EXTENSIONS = {
        'document': ['.pdf', '.doc', '.docx', '.txt', '.md'],
        'presentation': ['.ppt', '.pptx'],
        'video': ['.mp4', '.webm', '.avi', '.mov'],
        'image': ['.jpg', '.jpeg', '.png', '.gif'],
        'other': ['.zip', '.rar']
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    @classmethod
    def get_upload_path(cls, instance, filename):
        """
        توليد مسار رفع الملف
        Format: uploads/courses/{course_code}/{semester}/{filename}
        """
        # الحصول على امتداد الملف
        ext = Path(filename).suffix.lower()
        
        # توليد اسم فريد للملف
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = slugify(Path(filename).stem, allow_unicode=True)
        new_filename = f"{safe_name}_{timestamp}{ext}"
        
        # بناء المسار
        course_code = instance.course.course_code if instance.course else 'unknown'
        semester = instance.semester.semester_name if instance.semester else 'general'
        
        return os.path.join('uploads', 'courses', course_code, semester, new_filename)
    
    @classmethod
    def validate_file(cls, file):
        """
        التحقق من صحة الملف
        Returns: (is_valid, error_message)
        """
        if not file:
            return False, "لم يتم اختيار ملف"
        
        # التحقق من الحجم
        if file.size > cls.MAX_FILE_SIZE:
            max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"حجم الملف يتجاوز الحد المسموح ({max_mb} ميجابايت)"
        
        # التحقق من الامتداد
        ext = Path(file.name).suffix.lower()
        all_allowed = []
        for exts in cls.ALLOWED_EXTENSIONS.values():
            all_allowed.extend(exts)
        
        if ext not in all_allowed:
            return False, f"نوع الملف غير مدعوم. الأنواع المدعومة: {', '.join(all_allowed)}"
        
        return True, None
    
    @classmethod
    def get_file_type(cls, filename):
        """تحديد نوع الملف"""
        ext = Path(filename).suffix.lower()
        
        for file_type, extensions in cls.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        
        return 'other'
    
    @classmethod
    def delete_file(cls, file_path):
        """حذف ملف من التخزين"""
        try:
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False
    
    @classmethod
    def get_file_size_display(cls, size_bytes):
        """عرض حجم الملف بشكل مقروء"""
        if size_bytes < 1024:
            return f"{size_bytes} بايت"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} كيلوبايت"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} ميجابايت"


class NotificationService:
    """خدمة الإشعارات"""
    
    @classmethod
    def notify_new_file(cls, file_obj):
        """
        إرسال إشعار عند رفع ملف جديد
        """
        from apps.notifications.models import Notification
        from apps.accounts.models import User
        
        course = file_obj.course
        
        # الحصول على جميع الطلاب المسجلين في التخصصات المرتبطة بالمقرر
        majors = course.course_majors.values_list('major_id', flat=True)
        students = User.objects.filter(
            role__role_name='student',
            major_id__in=majors,
            level=course.level,
            account_status='active'
        )
        
        # إنشاء إشعار لكل طالب
        notifications = []
        for student in students:
            notifications.append(Notification(
                user=student,
                title=f"ملف جديد في {course.course_name}",
                body=f"تم رفع ملف جديد: {file_obj.title}",
                notification_type='new_file',
                related_course=course
            ))
        
        if notifications:
            Notification.objects.bulk_create(notifications)
        
        return len(notifications)
    
    @classmethod
    def notify_announcement(cls, title, body, course=None, target_role=None):
        """
        إرسال إعلان عام
        """
        from apps.notifications.models import Notification
        from apps.accounts.models import User
        
        users = User.objects.filter(account_status='active')
        
        if target_role:
            users = users.filter(role__role_name=target_role)
        
        if course:
            majors = course.course_majors.values_list('major_id', flat=True)
            users = users.filter(major_id__in=majors, level=course.level)
        
        notifications = []
        for user in users:
            notifications.append(Notification(
                user=user,
                title=title,
                body=body,
                notification_type='info',
                related_course=course
            ))
        
        if notifications:
            Notification.objects.bulk_create(notifications)
        
        return len(notifications)


class ArchiveService:
    """خدمة الأرشفة الذكية"""
    
    @classmethod
    def is_archived_for_student(cls, course, student):
        """
        التحقق مما إذا كان المقرر مؤرشفاً بالنسبة للطالب
        
        المنطق:
        - إذا كان الفصل الدراسي غير حالي (is_current = False)
        - و مستوى الطالب أعلى من مستوى المقرر
        - فإن المقرر يعتبر مؤرشفاً
        """
        from apps.accounts.models import Semester
        
        # الحصول على الفصل الحالي
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            return False
        
        # التحقق من مستوى الطالب مقارنة بمستوى المقرر
        if student.level and course.level:
            student_level_number = student.level.level_number
            course_level_number = course.level.level_number
            
            if student_level_number > course_level_number:
                return True
        
        return False
    
    @classmethod
    def get_student_courses(cls, student, archived=False):
        """
        الحصول على مقررات الطالب (الحالية أو المؤرشفة)
        """
        from apps.courses.models import Course
        
        # الحصول على المقررات المرتبطة بتخصص الطالب
        courses = Course.objects.filter(
            course_majors__major=student.major,
            is_active=True
        ).distinct()
        
        result = []
        for course in courses:
            is_archived = cls.is_archived_for_student(course, student)
            
            if archived and is_archived:
                result.append(course)
            elif not archived and not is_archived:
                # فقط المقررات التي تطابق مستوى الطالب
                if course.level == student.level:
                    result.append(course)
        
        return result


class PromotionService:
    """خدمة ترقية الطلاب"""
    
    @classmethod
    def promote_students(cls, from_level):
        """
        ترقية جميع طلاب مستوى معين إلى المستوى التالي
        """
        from apps.accounts.models import User, Level
        
        # الحصول على المستوى التالي
        try:
            next_level = Level.objects.get(level_number=from_level.level_number + 1)
        except Level.DoesNotExist:
            return 0, "لا يوجد مستوى تالي"
        
        # ترقية الطلاب
        students = User.objects.filter(
            role__role_name='student',
            level=from_level,
            account_status='active'
        )
        
        count = students.update(level=next_level)
        
        return count, None
    
    @classmethod
    def get_promotion_stats(cls):
        """
        الحصول على إحصائيات الترقية
        """
        from apps.accounts.models import User, Level
        
        levels = Level.objects.all().order_by('level_number')
        stats = []
        
        for level in levels:
            student_count = User.objects.filter(
                role__role_name='student',
                level=level,
                account_status='active'
            ).count()
            
            try:
                next_level = Level.objects.get(level_number=level.level_number + 1)
            except Level.DoesNotExist:
                next_level = None
            
            stats.append({
                'level': level,
                'student_count': student_count,
                'next_level': next_level
            })
        
        return stats


# ========== خدمات محسّنة (Service Layer Pattern) ==========
# تم إضافة هذه الخدمات لتحسين المعمارية وفصل منطق الأعمال عن Views

import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from django.db import transaction
from django.db.models import QuerySet, Count, Sum
from django.utils import timezone

logger = logging.getLogger('courses')


@dataclass
class FileUploadResult:
    """نتيجة عملية رفع الملف"""
    success: bool
    file_id: Optional[int] = None
    error: Optional[str] = None


@dataclass
class CourseStatistics:
    """إحصائيات المقرر"""
    total_files: int
    visible_files: int
    hidden_files: int
    total_downloads: int
    total_views: int
    students_count: int


class EnhancedCourseService:
    """
    خدمة إدارة المقررات المحسّنة
    
    تتعامل مع جميع العمليات المتعلقة بالمقررات مع فصل كامل لمنطق الأعمال
    """
    
    @staticmethod
    def get_student_courses(student, view_type: str = 'current') -> QuerySet:
        """
        الحصول على مقررات الطالب
        
        Args:
            student: كائن المستخدم (الطالب)
            view_type: نوع العرض ('current' أو 'archived')
            
        Returns:
            QuerySet: مقررات الطالب
        """
        from .models import Course
        
        if view_type == 'archived':
            return Course.objects.get_archived_courses_for_student(student)
        return Course.objects.get_current_courses_for_student(student)
    
    @staticmethod
    def get_instructor_courses(instructor) -> QuerySet:
        """
        الحصول على مقررات المدرس
        
        Args:
            instructor: كائن المستخدم (المدرس)
            
        Returns:
            QuerySet: مقررات المدرس
        """
        from .models import Course
        return Course.objects.get_courses_for_instructor(instructor)
    
    @staticmethod
    def get_course_statistics(course) -> CourseStatistics:
        """
        الحصول على إحصائيات المقرر
        
        Args:
            course: كائن المقرر
            
        Returns:
            CourseStatistics: إحصائيات المقرر
        """
        from .models import LectureFile
        from apps.accounts.models import User
        
        files = course.files.filter(is_deleted=False)
        
        # إحصائيات الملفات
        total_files = files.count()
        visible_files = files.filter(is_visible=True).count()
        hidden_files = files.filter(is_visible=False).count()
        
        # إحصائيات التحميل والمشاهدة
        stats = files.aggregate(
            total_downloads=Sum('download_count'),
            total_views=Sum('view_count')
        )
        
        # عدد الطلاب
        students_count = User.objects.filter(
            role__role_name='Student',
            major__in=course.course_majors.values_list('major', flat=True),
            level=course.level,
            account_status='active'
        ).count()
        
        return CourseStatistics(
            total_files=total_files,
            visible_files=visible_files,
            hidden_files=hidden_files,
            total_downloads=stats['total_downloads'] or 0,
            total_views=stats['total_views'] or 0,
            students_count=students_count
        )
    
    @staticmethod
    def check_student_enrollment(student, course) -> bool:
        """
        التحقق من تسجيل الطالب في المقرر
        
        Args:
            student: كائن المستخدم (الطالب)
            course: كائن المقرر
            
        Returns:
            bool: True إذا كان الطالب مسجلاً
        """
        if not student.level or not student.major:
            return False
        
        # التحقق من التخصص
        course_majors = course.course_majors.values_list('major_id', flat=True)
        if student.major_id not in course_majors:
            return False
        
        # التحقق من المستوى
        if course.semester.is_current:
            return student.level_id == course.level_id
        else:
            return student.level.level_number >= course.level.level_number
    
    @staticmethod
    @transaction.atomic
    def assign_instructors(course, instructor_ids: List[int], assigned_by) -> Dict[str, Any]:
        """
        تعيين مدرسين للمقرر
        """
        from .models import InstructorCourse
        from apps.core.models import AuditLog
        
        InstructorCourse.objects.filter(course=course).delete()
        
        created = []
        for idx, instructor_id in enumerate(instructor_ids):
            ic = InstructorCourse.objects.create(
                course=course,
                instructor_id=instructor_id,
                is_primary=(idx == 0)
            )
            created.append(ic.id)
        
        AuditLog.log(
            user=assigned_by,
            action='update',
            model_name='InstructorCourse',
            object_id=course.id,
            object_repr=f'تعيين مدرسين لـ {course}',
            changes={'instructors': instructor_ids}
        )
        
        logger.info(f"Assigned {len(instructor_ids)} instructors to course {course.course_code}")
        
        return {
            'success': True,
            'assigned_count': len(created),
            'instructor_course_ids': created
        }


class EnhancedFileService:
    """
    خدمة إدارة الملفات المحسّنة
    
    تتعامل مع جميع العمليات المتعلقة بالملفات مع فصل كامل لمنطق الأعمال
    """
    
    @staticmethod
    def get_course_files(course, include_hidden: bool = False) -> QuerySet:
        """
        الحصول على ملفات المقرر
        """
        from .models import LectureFile
        
        files = course.files.filter(is_deleted=False)
        if not include_hidden:
            files = files.filter(is_visible=True)
        return files.order_by('-upload_date')
    
    @staticmethod
    def get_files_by_type(course, include_hidden: bool = False) -> Dict[str, QuerySet]:
        """
        الحصول على ملفات المقرر مصنفة حسب النوع
        """
        files = EnhancedFileService.get_course_files(course, include_hidden)
        
        return {
            'lectures': files.filter(file_type='Lecture'),
            'summaries': files.filter(file_type='Summary'),
            'exams': files.filter(file_type='Exam'),
            'assignments': files.filter(file_type='Assignment'),
            'references': files.filter(file_type='Reference'),
            'others': files.filter(file_type='Other'),
        }
    
    @staticmethod
    def check_file_access(user, file_obj, require_visible: bool = True) -> Tuple[bool, str]:
        """
        التحقق من صلاحية الوصول للملف
        
        Returns:
            Tuple[bool, str]: (مسموح, رسالة الخطأ)
        """
        if file_obj.is_deleted:
            return False, "هذا الملف غير متاح."
        
        if user.is_admin():
            return True, ""
        
        if user.is_instructor():
            return True, ""
        
        if user.is_student():
            if not EnhancedCourseService.check_student_enrollment(user, file_obj.course):
                return False, "ليس لديك صلاحية الوصول لهذا الملف."
            
            if require_visible and not file_obj.is_visible:
                return False, "هذا الملف غير متاح حالياً."
            
            return True, ""
        
        return False, "ليس لديك صلاحية الوصول لهذا الملف."
    
    @staticmethod
    @transaction.atomic
    def upload_file(course, uploader, file_data: Dict[str, Any], 
                   local_file=None) -> FileUploadResult:
        """
        رفع ملف جديد
        """
        from .models import LectureFile
        from apps.accounts.models import UserActivity
        from apps.notifications.models import NotificationManager
        
        try:
            file_obj = LectureFile.objects.create(
                course=course,
                uploader=uploader,
                title=file_data.get('title'),
                description=file_data.get('description'),
                file_type=file_data.get('file_type', 'Lecture'),
                content_type=file_data.get('content_type', 'local_file'),
                local_file=local_file,
                external_link=file_data.get('external_link'),
                is_visible=file_data.get('is_visible', True)
            )
            
            UserActivity.objects.create(
                user=uploader,
                activity_type='upload',
                description=f'رفع ملف: {file_obj.title}',
                file_id=file_obj.id
            )
            
            if file_obj.is_visible:
                NotificationManager.create_file_upload_notification(file_obj, course)
            
            logger.info(f"File uploaded: {file_obj.title} by {uploader.academic_id}")
            
            return FileUploadResult(success=True, file_id=file_obj.id)
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return FileUploadResult(success=False, error=str(e))
    
    @staticmethod
    @transaction.atomic
    def delete_file(file_obj, deleted_by, hard_delete: bool = False) -> bool:
        """
        حذف ملف
        """
        from apps.core.models import AuditLog
        
        try:
            if hard_delete:
                if file_obj.local_file:
                    file_obj.local_file.delete()
                file_obj.delete()
            else:
                file_obj.is_deleted = True
                file_obj.deleted_at = timezone.now()
                file_obj.save()
            
            AuditLog.log(
                user=deleted_by,
                action='delete',
                model_name='LectureFile',
                object_id=file_obj.id,
                object_repr=str(file_obj)
            )
            
            logger.info(f"File deleted: {file_obj.title} by {deleted_by.academic_id}")
            return True
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    @staticmethod
    def toggle_visibility(file_obj, toggled_by) -> bool:
        """
        تبديل ظهور الملف
        """
        from apps.notifications.models import NotificationManager
        
        file_obj.is_visible = not file_obj.is_visible
        file_obj.save()
        
        if file_obj.is_visible:
            NotificationManager.create_file_upload_notification(file_obj, file_obj.course)
        
        logger.info(
            f"File visibility toggled: {file_obj.title} -> "
            f"{'visible' if file_obj.is_visible else 'hidden'} by {toggled_by.academic_id}"
        )
        
        return file_obj.is_visible
    
    @staticmethod
    def record_download(file_obj, user, ip_address: str = None):
        """
        تسجيل تحميل الملف
        """
        from apps.accounts.models import UserActivity
        
        file_obj.increment_download()
        
        UserActivity.objects.create(
            user=user,
            activity_type='download',
            description=f'تحميل ملف: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=ip_address
        )
    
    @staticmethod
    def record_view(file_obj, user, ip_address: str = None):
        """
        تسجيل مشاهدة الملف
        """
        from apps.accounts.models import UserActivity
        
        file_obj.increment_view()
        
        UserActivity.objects.create(
            user=user,
            activity_type='view',
            description=f'عرض ملف: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=ip_address
        )
