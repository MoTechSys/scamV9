"""
نماذج إدارة المقررات والمحتوى الأكاديمي
S-ACM - Smart Academic Content Management System
"""

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from pathlib import Path
import os


class Course(models.Model):
    """
    جدول المقررات (Courses)
    يرتبط بالمستويات والفصول الدراسية
    """
    course_name = models.CharField(
        max_length=150,
        verbose_name='اسم المقرر'
    )
    course_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رمز المقرر'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف المقرر'
    )
    level = models.ForeignKey(
        'accounts.Level',
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='المستوى'
    )
    semester = models.ForeignKey(
        'accounts.Semester',
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='الفصل الدراسي'
    )
    credit_hours = models.PositiveIntegerField(
        default=3,
        verbose_name='الساعات المعتمدة'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        db_table = 'courses'
        verbose_name = 'مقرر'
        verbose_name_plural = 'المقررات'
        ordering = ['course_code']
        indexes = [
            models.Index(fields=['course_code']),
            models.Index(fields=['level', 'semester']),
        ]
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name}"
    
    def get_majors(self):
        """الحصول على التخصصات المرتبطة بالمقرر"""
        return self.course_majors.all()
    
    def get_instructors(self):
        """الحصول على المدرسين المعينين للمقرر"""
        return self.instructor_courses.all()
    
    def get_files_count(self):
        """الحصول على عدد الملفات في المقرر"""
        return self.files.filter(is_deleted=False, is_visible=True).count()


class CourseMajor(models.Model):
    """
    جدول ربط المقررات بالتخصصات (Course_Majors)
    علاقة Many-to-Many بين المقررات والتخصصات
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='course_majors',
        verbose_name='المقرر'
    )
    major = models.ForeignKey(
        'accounts.Major',
        on_delete=models.CASCADE,
        related_name='major_courses',
        verbose_name='التخصص'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        db_table = 'course_majors'
        unique_together = ('course', 'major')
        verbose_name = 'ربط مقرر بتخصص'
        verbose_name_plural = 'ربط المقررات بالتخصصات'
    
    def __str__(self):
        return f"{self.course.course_code} - {self.major.major_name}"


class InstructorCourse(models.Model):
    """
    جدول ربط المدرسين بالمقررات (Instructor_Courses)
    """
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_courses',
        verbose_name='المدرس'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='instructor_courses',
        verbose_name='المقرر'
    )
    assigned_date = models.DateField(
        auto_now_add=True,
        verbose_name='تاريخ التعيين'
    )
    is_primary = models.BooleanField(
        default=True,
        verbose_name='المدرس الرئيسي',
        help_text='يحدد ما إذا كان هذا المدرس هو المدرس الرئيسي للمقرر'
    )
    
    class Meta:
        db_table = 'instructor_courses'
        unique_together = ('instructor', 'course')
        verbose_name = 'تعيين مدرس'
        verbose_name_plural = 'تعيينات المدرسين'
    
    def __str__(self):
        return f"{self.instructor.full_name} - {self.course.course_code}"


def lecture_file_path(instance, filename):
    """
    تحديد مسار حفظ الملفات بشكل منظم
    media/uploads/courses/{course_code}/{file_type}/{filename}
    """
    # استخدام pathlib للتوافق مع جميع أنظمة التشغيل
    course_code = instance.course.course_code
    file_type = instance.file_type
    return str(Path('uploads') / 'courses' / course_code / file_type / filename)


class LectureFile(models.Model):
    """
    جدول ملفات المحاضرات (Lectures_Files)
    يدعم التخزين الهجين: ملفات محلية وروابط خارجية
    """
    CONTENT_TYPE_CHOICES = [
        ('local_file', 'ملف محلي'),
        ('external_link', 'رابط خارجي'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('Lecture', 'محاضرة'),
        ('Summary', 'ملخص'),
        ('Exam', 'اختبار'),
        ('Assignment', 'واجب'),
        ('Reference', 'مرجع'),
        ('Other', 'أخرى'),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='المقرر'
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
        verbose_name='رافع الملف'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان الملف'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف الملف'
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='local_file',
        verbose_name='نوع المحتوى'
    )
    # للملفات المحلية
    local_file = models.FileField(
        upload_to=lecture_file_path,
        blank=True,
        null=True,
        verbose_name='الملف المحلي'
    )
    # للروابط الخارجية (YouTube, Google Drive, etc.)
    external_link = models.URLField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='الرابط الخارجي'
    )
    file_type = models.CharField(
        max_length=50,
        choices=FILE_TYPE_CHOICES,
        default='Lecture',
        verbose_name='تصنيف الملف'
    )
    file_size = models.BigIntegerField(
        blank=True,
        null=True,
        verbose_name='حجم الملف (بايت)'
    )
    file_extension = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='امتداد الملف'
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='نوع MIME'
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الرفع'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name='مرئي للطلاب',
        help_text='للتحكم في ظهور الملف للطلاب'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='محذوف',
        help_text='Soft delete - الملف لا يظهر لكنه موجود في قاعدة البيانات'
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاريخ الحذف'
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد التحميلات'
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد المشاهدات'
    )
    
    class Meta:
        db_table = 'lectures_files'
        verbose_name = 'ملف محاضرة'
        verbose_name_plural = 'ملفات المحاضرات'
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['course', 'file_type']),
            models.Index(fields=['upload_date']),
            models.Index(fields=['is_visible', 'is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.course.course_code}"
    
    def save(self, *args, **kwargs):
        # تحديث معلومات الملف عند الحفظ
        if self.local_file:
            self.content_type = 'local_file'
            if hasattr(self.local_file, 'size'):
                self.file_size = self.local_file.size
            if hasattr(self.local_file, 'name'):
                self.file_extension = Path(self.local_file.name).suffix.lower()
        elif self.external_link:
            self.content_type = 'external_link'
        super().save(*args, **kwargs)
    
    def get_content_url(self):
        """الحصول على رابط المحتوى (محلي أو خارجي)"""
        if self.content_type == 'local_file' and self.local_file:
            return self.local_file.url
        elif self.content_type == 'external_link' and self.external_link:
            return self.external_link
        return None
    
    def increment_download(self):
        """زيادة عداد التحميلات"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def increment_view(self):
        """زيادة عداد المشاهدات"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def soft_delete(self):
        """حذف ناعم للملف"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def restore(self):
        """استعادة ملف محذوف"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def is_video(self):
        """التحقق مما إذا كان الملف فيديو"""
        video_extensions = ['.mp4', '.webm', '.avi', '.mov', '.mkv']
        if self.file_extension:
            return self.file_extension.lower() in video_extensions
        if self.external_link:
            return 'youtube.com' in self.external_link or 'youtu.be' in self.external_link
        return False
    
    def is_pdf(self):
        """التحقق مما إذا كان الملف PDF"""
        return self.file_extension and self.file_extension.lower() == '.pdf'
    
    def is_image(self):
        """التحقق مما إذا كان الملف صورة"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        return self.file_extension and self.file_extension.lower() in image_extensions


class CourseManager(models.Manager):
    """
    مدير مخصص للمقررات مع استعلامات شائعة
    """
    
    def get_current_courses_for_student(self, student):
        """
        الحصول على المقررات الحالية للطالب
        استعلام المواد الحالية (التبويب الرئيسي)
        """
        if not student.level or not student.major:
            return self.none()
        
        return self.filter(
            semester__is_current=True,
            level=student.level,
            course_majors__major=student.major,
            is_active=True
        ).distinct()
    
    def get_archived_courses_for_student(self, student):
        """
        الحصول على المقررات المؤرشفة للطالب
        استعلام مواد الأرشيف (تبويب الأرشيف)
        """
        if not student.level or not student.major:
            return self.none()
        
        return self.filter(
            semester__is_current=False,
            level__level_number__lt=student.level.level_number,
            course_majors__major=student.major,
            is_active=True
        ).distinct()
    
    def get_courses_for_instructor(self, instructor):
        """
        الحصول على المقررات المعينة للمدرس
        """
        return self.filter(
            instructor_courses__instructor=instructor,
            is_active=True
        ).distinct()


# إضافة المدير المخصص للنموذج
Course.objects = CourseManager()
Course.objects.model = Course
