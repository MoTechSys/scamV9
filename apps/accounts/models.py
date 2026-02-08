"""
نماذج إدارة المستخدمين والأدوار والصلاحيات
S-ACM - Smart Academic Content Management System
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MinLengthValidator
import secrets
import string


class Role(models.Model):
    """
    جدول الأدوار (Roles)
    نظام أدوار ديناميكي - يمكن إنشاء أي عدد من الأدوار
    
    الأدوار الافتراضية (is_system=True): Admin, Instructor, Student
    يمكن للأدمن إنشاء أدوار مخصصة (is_system=False)
    """
    # الأدوار الافتراضية - للاستخدام في الكود فقط
    ADMIN = 'admin'
    INSTRUCTOR = 'instructor'
    STUDENT = 'student'
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='كود الدور',
        help_text='معرف فريد للدور (بالإنجليزية، مثل: admin, instructor)'
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name='اسم العرض',
        help_text='الاسم الذي يظهر للمستخدم'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف الدور'
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name='دور نظام',
        help_text='الأدوار الافتراضية التي لا يمكن حذفها'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'دور'
        verbose_name_plural = 'الأدوار'
        ordering = ['-is_system', 'display_name']
    
    def __str__(self):
        return self.display_name
    
    def get_permissions(self):
        """الحصول على جميع صلاحيات هذا الدور"""
        return Permission.objects.filter(
            role_permissions__role=self,
            is_active=True
        ).values_list('code', flat=True)
    
    @classmethod
    def get_default_roles(cls):
        """إرجاع الأدوار الافتراضية"""
        return cls.objects.filter(is_system=True, is_active=True)


class Permission(models.Model):
    """
    جدول الصلاحيات (Permissions)
    نظام صلاحيات ديناميكي - يتحكم في كل وظيفة في النظام
    
    Categories:
        - courses: صلاحيات المقررات
        - files: صلاحيات الملفات
        - users: صلاحيات المستخدمين
        - notifications: صلاحيات الإشعارات
        - ai: صلاحيات الذكاء الاصطناعي
        - system: صلاحيات النظام
    """
    CATEGORY_CHOICES = [
        ('courses', 'المقررات'),
        ('files', 'الملفات'),
        ('users', 'المستخدمين'),
        ('notifications', 'الإشعارات'),
        ('ai', 'الذكاء الاصطناعي'),
        ('system', 'النظام'),
    ]
    
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='كود الصلاحية',
        help_text='معرف فريد (مثل: manage_files, view_courses)'
    )
    display_name = models.CharField(
        max_length=150,
        verbose_name='اسم العرض',
        help_text='الاسم الذي يظهر في لوحة التحكم'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف الصلاحية'
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='system',
        verbose_name='التصنيف'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشطة'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        db_table = 'permissions'
        verbose_name = 'صلاحية'
        verbose_name_plural = 'الصلاحيات'
        ordering = ['category', 'display_name']
    
    def __str__(self):
        return f"{self.display_name} ({self.code})"


class RolePermission(models.Model):
    """
    جدول ربط الأدوار بالصلاحيات (Role_Permissions)
    علاقة Many-to-Many بين الأدوار والصلاحيات
    """
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name='الدور'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='permission_roles',
        verbose_name='الصلاحية'
    )
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')
        verbose_name = 'صلاحية الدور'
        verbose_name_plural = 'صلاحيات الأدوار'
    
    def __str__(self):
        return f"{self.role} - {self.permission}"


class Major(models.Model):
    """
    جدول التخصصات (Majors)
    """
    major_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='اسم التخصص'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف التخصص'
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        db_table = 'majors'
        verbose_name = 'تخصص'
        verbose_name_plural = 'التخصصات'
        ordering = ['major_name']
    
    def __str__(self):
        return self.major_name


class Level(models.Model):
    """
    جدول المستويات (Levels)
    يحتوي على level_number لدعم محرك الترقية الجماعية
    """
    level_name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='اسم المستوى'
    )
    level_number = models.PositiveIntegerField(
        unique=True,
        verbose_name='رقم المستوى',
        help_text='رقم ترتيبي للمستوى (1, 2, 3, 4) يستخدم في الترقية الجماعية'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف المستوى'
    )
    
    class Meta:
        db_table = 'levels'
        verbose_name = 'مستوى'
        verbose_name_plural = 'المستويات'
        ordering = ['level_number']
    
    def __str__(self):
        return self.level_name


class Semester(models.Model):
    """
    جدول الفصول الدراسية (Semesters)
    يحتوي على is_current لدعم منطق الأرشفة الذكي
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='اسم الفصل الدراسي'
    )
    academic_year = models.CharField(
        max_length=20,
        verbose_name='العام الدراسي',
        help_text='مثال: 2025/2026'
    )
    semester_number = models.PositiveIntegerField(
        verbose_name='رقم الفصل',
        help_text='1 للفصل الأول، 2 للفصل الثاني'
    )
    start_date = models.DateField(verbose_name='تاريخ البداية')
    end_date = models.DateField(verbose_name='تاريخ النهاية')
    is_current = models.BooleanField(
        default=False,
        verbose_name='الفصل الحالي',
        help_text='يحدد ما إذا كان هذا هو الفصل الدراسي النشط حالياً'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        db_table = 'semesters'
        verbose_name = 'فصل دراسي'
        verbose_name_plural = 'الفصول الدراسية'
        ordering = ['-academic_year', '-semester_number']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # إذا تم تعيين هذا الفصل كحالي، قم بإلغاء تعيين الفصول الأخرى
        if self.is_current:
            Semester.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class UserManager(BaseUserManager):
    """
    مدير مخصص للمستخدمين
    """
    def create_user(self, academic_id, password=None, **extra_fields):
        if not academic_id:
            raise ValueError('يجب تحديد الرقم الأكاديمي')
        user = self.model(academic_id=academic_id, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, academic_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('account_status', 'active')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(academic_id, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    نموذج المستخدم المخصص (Users)
    يدعم نظام الإضافة المسبقة مع التفعيل الذاتي
    """
    ACCOUNT_STATUS_CHOICES = [
        ('inactive', 'غير مفعّل'),
        ('active', 'مفعّل'),
        ('suspended', 'موقوف'),
    ]
    
    academic_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='الرقم الأكاديمي/الوظيفي',
        help_text='الرقم الأكاديمي للطالب أو الرقم الوظيفي للموظف'
    )
    id_card_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم البطاقة الشخصية',
        help_text='يستخدم للتحقق من الهوية عند التفعيل'
    )
    full_name = models.CharField(
        max_length=150,
        verbose_name='الاسم الكامل'
    )
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
        verbose_name='البريد الإلكتروني',
        help_text='يتم تعيينه عند التفعيل'
    )
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='inactive',
        verbose_name='حالة الحساب'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='users',
        verbose_name='الدور',
        null=True,
        blank=True
    )
    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        related_name='students',
        verbose_name='التخصص',
        null=True,
        blank=True,
        help_text='للطلاب فقط'
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        related_name='students',
        verbose_name='المستوى',
        null=True,
        blank=True,
        help_text='للطلاب فقط'
    )
    
    # Django required fields
    is_staff = models.BooleanField(default=False, verbose_name='موظف')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='تاريخ الانضمام')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='آخر تسجيل دخول')
    
    # Profile fields
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name='صورة الملف الشخصي'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'academic_id'
    REQUIRED_FIELDS = ['full_name', 'id_card_number']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        indexes = [
            models.Index(fields=['academic_id']),
            models.Index(fields=['email']),
            models.Index(fields=['account_status']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.academic_id})"
    
    def is_admin(self):
        """التحقق من أن المستخدم أدمن (للتوافق الخلفي)"""
        return self.role and self.role.code == Role.ADMIN
    
    def is_instructor(self):
        """التحقق من أن المستخدم مدرس (للتوافق الخلفي)"""
        return self.role and self.role.code == Role.INSTRUCTOR
    
    def is_student(self):
        """التحقق من أن المستخدم طالب (للتوافق الخلفي)"""
        return self.role and self.role.code == Role.STUDENT
    
    def has_perm(self, perm_code):
        """
        التحقق من وجود صلاحية معينة للمستخدم (النظام الجديد)
        
        Args:
            perm_code: كود الصلاحية (مثل: 'manage_files', 'view_courses')
            
        Returns:
            bool: True إذا كان المستخدم يمتلك الصلاحية
        """
        # الأدمن له كل الصلاحيات
        if self.is_superuser or self.is_admin():
            return True
        
        if not self.role:
            return False
        
        return perm_code in self.get_permissions()
    
    def has_permission(self, permission_name):
        """للتوافق الخلفي مع الكود القديم"""
        return self.has_perm(permission_name)
    
    def get_permissions(self):
        """
        الحصول على جميع صلاحيات المستخدم (مع Caching)
        
        Returns:
            set: مجموعة أكواد الصلاحيات
        """
        # تحقق من الكاش أولاً
        cache_attr = '_permissions_cache'
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)
        
        if not self.role:
            permissions = set()
        else:
            permissions = set(
                RolePermission.objects.filter(
                    role=self.role,
                    permission__is_active=True
                ).values_list('permission__code', flat=True)
            )
        
        # حفظ في الكاش
        setattr(self, cache_attr, permissions)
        return permissions
    
    def clear_permissions_cache(self):
        """مسح كاش الصلاحيات (يُستدعى عند تغيير الدور)"""
        if hasattr(self, '_permissions_cache'):
            delattr(self, '_permissions_cache')
    
    def get_role_display(self):
        """الحصول على اسم الدور للعرض"""
        return self.role.display_name if self.role else 'بدون دور'


class VerificationCode(models.Model):
    """
    جدول رموز التحقق (Verification_Codes)
    يستخدم لتفعيل الحسابات عبر OTP
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_codes',
        verbose_name='المستخدم'
    )
    code = models.CharField(
        max_length=10,
        verbose_name='رمز التحقق'
    )
    email = models.EmailField(
        verbose_name='البريد الإلكتروني المستهدف'
    )
    expires_at = models.DateTimeField(verbose_name='تاريخ الانتهاء')
    is_used = models.BooleanField(default=False, verbose_name='مستخدم')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    attempts = models.PositiveIntegerField(default=0, verbose_name='عدد المحاولات')
    
    class Meta:
        db_table = 'verification_codes'
        verbose_name = 'رمز تحقق'
        verbose_name_plural = 'رموز التحقق'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.academic_id}"
    
    def is_valid(self):
        """التحقق من صلاحية الرمز"""
        return not self.is_used and self.expires_at > timezone.now() and self.attempts < 5
    
    @staticmethod
    def generate_code(length=6):
        """توليد رمز تحقق عشوائي"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))


class PasswordResetToken(models.Model):
    """
    جدول رموز إعادة تعيين كلمة المرور (Password_Reset_Tokens)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name='المستخدم'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='التوكن'
    )
    expires_at = models.DateTimeField(verbose_name='تاريخ الانتهاء')
    is_used = models.BooleanField(default=False, verbose_name='مستخدم')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'توكن إعادة تعيين'
        verbose_name_plural = 'توكنات إعادة التعيين'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.academic_id}"
    
    def is_valid(self):
        """التحقق من صلاحية التوكن"""
        return not self.is_used and self.expires_at > timezone.now()
    
    @staticmethod
    def generate_token():
        """توليد توكن عشوائي آمن"""
        return secrets.token_urlsafe(32)


class UserActivity(models.Model):
    """
    جدول نشاط المستخدمين (User_Activity)
    لتتبع وتسجيل أنشطة المستخدمين في النظام
    """
    ACTIVITY_TYPES = [
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('upload', 'رفع ملف'),
        ('download', 'تحميل ملف'),
        ('view', 'عرض محتوى'),
        ('ai_summary', 'طلب تلخيص AI'),
        ('ai_questions', 'طلب أسئلة AI'),
        ('profile_update', 'تحديث الملف الشخصي'),
        ('password_change', 'تغيير كلمة المرور'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='المستخدم'
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES,
        verbose_name='نوع النشاط'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف النشاط'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='عنوان IP'
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name='معلومات المتصفح'
    )
    activity_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='وقت النشاط'
    )
    
    # Optional reference to related file
    file_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='معرف الملف'
    )
    
    class Meta:
        db_table = 'user_activity'
        verbose_name = 'نشاط مستخدم'
        verbose_name_plural = 'أنشطة المستخدمين'
        ordering = ['-activity_time']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['activity_time']),
        ]
    
    def __str__(self):
        return f"{self.user.academic_id} - {self.get_activity_type_display()}"
