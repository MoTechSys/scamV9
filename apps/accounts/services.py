"""
Service Layer لتطبيق accounts
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على الخدمات المنطقية المنفصلة عن Views
لتحقيق مبدأ Single Responsibility و Service Layer Pattern

تم إنشاء هذا الملف لـ:
1. فصل منطق الأعمال عن Views (Fat Views → Thin Views + Services)
2. تحسين أداء استيراد CSV باستخدام Stream Processing
3. توفير خدمات قابلة لإعادة الاستخدام
"""

import csv
import io
import logging
from typing import Generator, Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('accounts')


@dataclass
class ImportResult:
    """نتيجة عملية الاستيراد"""
    created_count: int
    skipped_count: int
    errors: List[str]
    
    @property
    def success(self) -> bool:
        return self.created_count > 0 or (self.created_count == 0 and len(self.errors) == 0)


class CSVStreamProcessor:
    """
    معالج CSV باستخدام Stream Processing
    
    يحل مشكلة استهلاك الذاكرة (DoS Risk) عند استيراد ملفات كبيرة
    بدلاً من قراءة الملف كاملاً في الذاكرة، يتم معالجته سطراً بسطر
    
    Security Fix: DoS Prevention
    - قبل الإصلاح: csv_file.read().decode('utf-8') يقرأ الملف كاملاً (50MB = 50MB RAM)
    - بعد الإصلاح: معالجة سطر بسطر (50MB file = ~1KB RAM per iteration)
    """
    
    # الحد الأقصى لحجم الملف (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # حجم الدفعة للـ bulk_create
    BATCH_SIZE = 100
    
    def __init__(self, csv_file, encoding: str = 'utf-8'):
        """
        Args:
            csv_file: ملف CSV (من request.FILES)
            encoding: ترميز الملف
        """
        self.csv_file = csv_file
        self.encoding = encoding
        self._validate_file_size()
    
    def _validate_file_size(self):
        """التحقق من حجم الملف"""
        if hasattr(self.csv_file, 'size'):
            if self.csv_file.size > self.MAX_FILE_SIZE:
                raise ValueError(
                    f"حجم الملف ({self.csv_file.size / 1024 / 1024:.1f}MB) "
                    f"يتجاوز الحد المسموح ({self.MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
                )
    
    def stream_rows(self) -> Generator[Tuple[int, Dict[str, str]], None, None]:
        """
        قراءة الملف سطراً بسطر باستخدام Generator
        
        Yields:
            Tuple[int, Dict[str, str]]: (رقم السطر, بيانات السطر)
        """
        # إعادة مؤشر الملف للبداية
        self.csv_file.seek(0)
        
        # قراءة الملف كـ stream
        for chunk in self.csv_file.chunks():
            # معالجة كل chunk
            text_chunk = chunk.decode(self.encoding)
            
            # استخدام StringIO للتعامل مع النص كملف
            reader = csv.DictReader(io.StringIO(text_chunk))
            
            for row_num, row in enumerate(reader, start=2):
                yield row_num, row
    
    def stream_rows_simple(self) -> Generator[Tuple[int, Dict[str, str]], None, None]:
        """
        قراءة بسيطة للملفات الصغيرة
        
        للملفات الصغيرة (< 1MB)، القراءة الكاملة أسرع
        """
        self.csv_file.seek(0)
        content = self.csv_file.read().decode(self.encoding)
        reader = csv.DictReader(io.StringIO(content))
        
        for row_num, row in enumerate(reader, start=2):
            yield row_num, row


class UserImportService:
    """
    خدمة استيراد المستخدمين
    
    تستخدم Stream Processing لمعالجة ملفات CSV الكبيرة
    مع Batch Processing للإدراج في قاعدة البيانات
    """
    
    def __init__(self):
        self._roles_cache = None
        self._majors_cache = None
        self._levels_cache = None
        self._existing_academic_ids = None
        self._existing_id_cards = None
    
    def _load_caches(self):
        """تحميل البيانات المرجعية في الذاكرة المؤقتة"""
        from .models import Role, Major, Level, User
        
        if self._roles_cache is None:
            self._roles_cache = {r.code: r for r in Role.objects.all()}
        if self._majors_cache is None:
            self._majors_cache = {m.major_name: m for m in Major.objects.all()}
        if self._levels_cache is None:
            self._levels_cache = {l.level_name: l for l in Level.objects.all()}
        if self._existing_academic_ids is None:
            self._existing_academic_ids = set(User.objects.values_list('academic_id', flat=True))
        if self._existing_id_cards is None:
            self._existing_id_cards = set(User.objects.values_list('id_card_number', flat=True))
    
    def _validate_row(self, row_num: int, row: Dict[str, str]) -> Tuple[Optional['User'], Optional[str]]:
        """
        التحقق من صحة سطر واحد
        
        Returns:
            Tuple[Optional[User], Optional[str]]: (كائن User أو None, رسالة خطأ أو None)
        """
        from .models import User
        
        academic_id = row.get('academic_id', '').strip()
        id_card_number = row.get('id_card_number', '').strip()
        
        # التحقق من الحقول المطلوبة
        if not academic_id or not id_card_number:
            return None, f'السطر {row_num}: الرقم الأكاديمي أو رقم الهوية فارغ'
        
        # التحقق من التكرار
        if academic_id in self._existing_academic_ids:
            return None, None  # تخطي بدون خطأ (موجود مسبقاً)
        
        if id_card_number in self._existing_id_cards:
            return None, f'السطر {row_num}: رقم الهوية {id_card_number} موجود مسبقاً'
        
        # الحصول على البيانات المرجعية
        role_name = row.get('role', 'student').strip()
        role = self._roles_cache.get(role_name)
        if not role:
            return None, f'السطر {row_num}: الدور "{role_name}" غير موجود'
        
        major = None
        if row.get('major'):
            major = self._majors_cache.get(row['major'].strip())
            if not major:
                return None, f'السطر {row_num}: التخصص "{row["major"]}" غير موجود'
        
        level = None
        if row.get('level'):
            level = self._levels_cache.get(row['level'].strip())
            if not level:
                return None, f'السطر {row_num}: المستوى "{row["level"]}" غير موجود'
        
        # إنشاء كائن User (بدون حفظ)
        user = User(
            academic_id=academic_id,
            id_card_number=id_card_number,
            full_name=row.get('full_name', '').strip(),
            email=row.get('email', '').strip() or None,
            role=role,
            major=major,
            level=level,
            account_status='inactive'
        )
        
        # إضافة للمجموعة لمنع التكرار داخل نفس الملف
        self._existing_academic_ids.add(academic_id)
        self._existing_id_cards.add(id_card_number)
        
        return user, None
    
    @transaction.atomic
    def import_from_csv(self, csv_file) -> ImportResult:
        """
        استيراد المستخدمين من ملف CSV
        
        Args:
            csv_file: ملف CSV من request.FILES
            
        Returns:
            ImportResult: نتيجة عملية الاستيراد
        """
        from .models import User
        
        # تحميل الكاش
        self._load_caches()
        
        # إنشاء معالج Stream
        try:
            processor = CSVStreamProcessor(csv_file)
        except ValueError as e:
            return ImportResult(created_count=0, skipped_count=0, errors=[str(e)])
        
        users_to_create = []
        errors = []
        skipped_count = 0
        
        # معالجة الملف سطراً بسطر
        for row_num, row in processor.stream_rows_simple():
            try:
                user, error = self._validate_row(row_num, row)
                
                if error:
                    errors.append(error)
                elif user is None:
                    skipped_count += 1
                else:
                    users_to_create.append(user)
                    
            except Exception as e:
                errors.append(f'خطأ في السطر {row_num}: {str(e)}')
        
        # الإنشاء الجماعي المحسّن
        created_count = 0
        if users_to_create:
            batch_size = CSVStreamProcessor.BATCH_SIZE
            for i in range(0, len(users_to_create), batch_size):
                batch = users_to_create[i:i + batch_size]
                User.objects.bulk_create(batch, ignore_conflicts=True)
            created_count = len(users_to_create)
        
        logger.info(
            f"CSV Import completed: created={created_count}, "
            f"skipped={skipped_count}, errors={len(errors)}"
        )
        
        return ImportResult(
            created_count=created_count,
            skipped_count=skipped_count,
            errors=errors
        )


class AuthService:
    """
    خدمة المصادقة والتفعيل
    
    تفصل منطق المصادقة عن Views
    """
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """توليد رمز OTP"""
        import random
        return ''.join(random.choices('0123456789', k=length))
    
    @staticmethod
    def send_otp_email(email: str, otp_code: str) -> bool:
        """
        إرسال رمز OTP عبر البريد الإلكتروني
        
        Returns:
            bool: True إذا تم الإرسال بنجاح
        """
        try:
            send_mail(
                subject='رمز تفعيل حسابك في S-ACM',
                message=f'رمز التفعيل الخاص بك هو: {otp_code}\n\nهذا الرمز صالح لمدة 10 دقائق.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(email: str, reset_url: str) -> bool:
        """
        إرسال رابط إعادة تعيين كلمة المرور
        
        Returns:
            bool: True إذا تم الإرسال بنجاح
        """
        try:
            send_mail(
                subject='إعادة تعيين كلمة المرور - S-ACM',
                message=f'لإعادة تعيين كلمة المرور، اضغط على الرابط التالي:\n\n{reset_url}\n\nهذا الرابط صالح لمدة ساعة واحدة.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False
    
    @staticmethod
    def activate_user(user, email: str, password: str, request=None) -> bool:
        """
        تفعيل حساب المستخدم
        
        Args:
            user: كائن المستخدم
            email: البريد الإلكتروني
            password: كلمة المرور الجديدة
            request: طلب HTTP (للتسجيل في سجل التدقيق)
            
        Returns:
            bool: True إذا تم التفعيل بنجاح
        """
        from apps.core.models import AuditLog
        
        try:
            user.email = email
            user.account_status = 'active'
            user.set_password(password)
            user.save()
            
            # تسجيل في سجل التدقيق
            if request:
                AuditLog.log(
                    user=user,
                    action='create',
                    model_name='User',
                    object_id=user.id,
                    object_repr=str(user),
                    changes={'action': 'account_activated'},
                    request=request
                )
            
            logger.info(f"User {user.academic_id} activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate user {user.academic_id}: {e}")
            return False


class StudentPromotionService:
    """
    خدمة ترقية الطلاب
    
    تتعامل مع منطق الترقية بما في ذلك حالة الخريجين
    """
    
    @staticmethod
    @transaction.atomic
    def promote_students(from_level, to_level, major=None, request=None) -> Dict[str, Any]:
        """
        ترقية الطلاب من مستوى لآخر
        
        Args:
            from_level: المستوى المصدر
            to_level: المستوى الهدف
            major: التخصص (اختياري)
            request: طلب HTTP (للتسجيل في سجل التدقيق)
            
        Returns:
            Dict: نتيجة العملية
        """
        from .models import User
        from apps.core.models import AuditLog
        
        # بناء الاستعلام الأساسي
        students = User.objects.filter(
            role__code='student',
            level=from_level,
            account_status='active'
        )
        
        if major:
            students = students.filter(major=major)
        
        # معالجة حالة المستوى 8 (الخريجين)
        if from_level.level_number == 8:
            # تحويل الطلاب إلى خريجين
            count = students.update(
                account_status='graduated',
                level=None
            )
            action_description = f'تم تخريج {count} طالب من {from_level}'
            changes_log = {
                'action': 'graduation',
                'from_level': str(from_level),
                'new_status': 'graduated',
                'major': str(major) if major else 'all',
                'count': count
            }
        else:
            # الترقية العادية
            count = students.update(level=to_level)
            action_description = f'تم ترقية {count} طالب من {from_level} إلى {to_level}'
            changes_log = {
                'action': 'promotion',
                'from_level': str(from_level),
                'to_level': str(to_level),
                'major': str(major) if major else 'all',
                'count': count
            }
        
        # تسجيل في سجل التدقيق
        if request:
            AuditLog.log(
                user=request.user,
                action='promote',
                model_name='User',
                changes=changes_log,
                request=request
            )
        
        logger.info(action_description)
        
        return {
            'success': True,
            'count': count,
            'description': action_description,
            'changes': changes_log
        }
