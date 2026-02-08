"""
Management Command لإنشاء البيانات الأولية للنظام
S-ACM - Smart Academic Content Management System
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import Role, Permission, RolePermission, Level, Semester, Major, User
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'إنشاء البيانات الأولية للنظام (الأدوار، الصلاحيات، المستويات، الفصول)'

    def handle(self, *args, **options):
        self.stdout.write('جاري إنشاء البيانات الأولية...\n')
        
        with transaction.atomic():
            self.create_roles()
            self.create_permissions()
            self.create_role_permissions()
            self.create_levels()
            self.create_semesters()
            self.create_sample_majors()
            self.create_admin_user()
        
        self.stdout.write(self.style.SUCCESS('\n✓ تم إنشاء البيانات الأولية بنجاح!'))

    def create_roles(self):
        """إنشاء الأدوار الأساسية"""
        roles = [
            {'role_name': 'admin', 'description': 'مسؤول النظام - صلاحيات كاملة'},
            {'role_name': 'instructor', 'description': 'مدرس - إدارة المقررات والملفات'},
            {'role_name': 'student', 'description': 'طالب - الوصول للمحتوى الأكاديمي'},
        ]
        
        for role_data in roles:
            role, created = Role.objects.get_or_create(
                role_name=role_data['role_name'],
                defaults={'description': role_data['description']}
            )
            status = 'تم إنشاؤه' if created else 'موجود مسبقاً'
            self.stdout.write(f'  - الدور: {role.role_name} ({status})')

    def create_permissions(self):
        """إنشاء الصلاحيات"""
        permissions = [
            # صلاحيات المستخدمين
            {'permission_name': 'manage_users', 'description': 'إدارة المستخدمين'},
            {'permission_name': 'view_users', 'description': 'عرض المستخدمين'},
            {'permission_name': 'promote_students', 'description': 'ترقية الطلاب'},
            
            # صلاحيات المقررات
            {'permission_name': 'manage_courses', 'description': 'إدارة المقررات'},
            {'permission_name': 'view_courses', 'description': 'عرض المقررات'},
            {'permission_name': 'assign_instructors', 'description': 'تعيين المدرسين للمقررات'},
            
            # صلاحيات الملفات
            {'permission_name': 'upload_files', 'description': 'رفع الملفات'},
            {'permission_name': 'delete_files', 'description': 'حذف الملفات'},
            {'permission_name': 'view_files', 'description': 'عرض الملفات'},
            {'permission_name': 'download_files', 'description': 'تحميل الملفات'},
            
            # صلاحيات الذكاء الاصطناعي
            {'permission_name': 'use_ai_features', 'description': 'استخدام ميزات الذكاء الاصطناعي'},
            
            # صلاحيات الإشعارات
            {'permission_name': 'send_notifications', 'description': 'إرسال الإشعارات'},
            
            # صلاحيات النظام
            {'permission_name': 'manage_semesters', 'description': 'إدارة الفصول الدراسية'},
            {'permission_name': 'manage_majors', 'description': 'إدارة التخصصات'},
            {'permission_name': 'view_statistics', 'description': 'عرض الإحصائيات'},
        ]
        
        for perm_data in permissions:
            perm, created = Permission.objects.get_or_create(
                permission_name=perm_data['permission_name'],
                defaults={'description': perm_data['description']}
            )
        
        self.stdout.write(f'  - تم إنشاء {len(permissions)} صلاحية')

    def create_role_permissions(self):
        """ربط الصلاحيات بالأدوار"""
        # صلاحيات الأدمن (جميع الصلاحيات)
        admin_role = Role.objects.get(role_name='admin')
        all_permissions = Permission.objects.all()
        for perm in all_permissions:
            RolePermission.objects.get_or_create(role=admin_role, permission=perm)
        
        # صلاحيات المدرس
        instructor_role = Role.objects.get(role_name='instructor')
        instructor_permissions = [
            'view_courses', 'upload_files', 'delete_files', 'view_files',
            'download_files', 'send_notifications', 'view_statistics'
        ]
        for perm_name in instructor_permissions:
            perm = Permission.objects.get(permission_name=perm_name)
            RolePermission.objects.get_or_create(role=instructor_role, permission=perm)
        
        # صلاحيات الطالب
        student_role = Role.objects.get(role_name='student')
        student_permissions = [
            'view_courses', 'view_files', 'download_files', 'use_ai_features'
        ]
        for perm_name in student_permissions:
            perm = Permission.objects.get(permission_name=perm_name)
            RolePermission.objects.get_or_create(role=student_role, permission=perm)
        
        self.stdout.write('  - تم ربط الصلاحيات بالأدوار')

    def create_levels(self):
        """إنشاء المستويات الدراسية"""
        levels = [
            {'level_number': 1, 'level_name': 'المستوى الأول'},
            {'level_number': 2, 'level_name': 'المستوى الثاني'},
            {'level_number': 3, 'level_name': 'المستوى الثالث'},
            {'level_number': 4, 'level_name': 'المستوى الرابع'},
            {'level_number': 5, 'level_name': 'المستوى الخامس'},
            {'level_number': 6, 'level_name': 'المستوى السادس'},
            {'level_number': 7, 'level_name': 'المستوى السابع'},
            {'level_number': 8, 'level_name': 'المستوى الثامن'},
        ]
        
        for level_data in levels:
            Level.objects.get_or_create(
                level_number=level_data['level_number'],
                defaults={'level_name': level_data['level_name']}
            )
        
        self.stdout.write(f'  - تم إنشاء {len(levels)} مستوى دراسي')

    def create_semesters(self):
        """إنشاء الفصول الدراسية"""
        today = date.today()
        year = today.year
        
        semesters = [
            {
                'name': f'الفصل الأول {year}/{year+1}',
                'academic_year': f'{year}/{year+1}',
                'semester_number': 1,
                'start_date': date(year, 9, 1),
                'end_date': date(year, 12, 31),
                'is_current': True
            },
            {
                'name': f'الفصل الثاني {year}/{year+1}',
                'academic_year': f'{year}/{year+1}',
                'semester_number': 2,
                'start_date': date(year+1, 1, 15),
                'end_date': date(year+1, 5, 31),
                'is_current': False
            },
        ]
        
        for sem_data in semesters:
            Semester.objects.get_or_create(
                name=sem_data['name'],
                defaults={
                    'academic_year': sem_data['academic_year'],
                    'semester_number': sem_data['semester_number'],
                    'start_date': sem_data['start_date'],
                    'end_date': sem_data['end_date'],
                    'is_current': sem_data['is_current']
                }
            )
        
        self.stdout.write(f'  - تم إنشاء {len(semesters)} فصل دراسي')

    def create_sample_majors(self):
        """إنشاء تخصصات نموذجية"""
        majors = [
            {'major_name': 'علوم الحاسب', 'description': 'قسم علوم الحاسب الآلي'},
            {'major_name': 'نظم المعلومات', 'description': 'قسم نظم المعلومات'},
            {'major_name': 'هندسة البرمجيات', 'description': 'قسم هندسة البرمجيات'},
            {'major_name': 'الذكاء الاصطناعي', 'description': 'قسم الذكاء الاصطناعي'},
        ]
        
        for major_data in majors:
            Major.objects.get_or_create(
                major_name=major_data['major_name'],
                defaults={'description': major_data['description']}
            )
        
        self.stdout.write(f'  - تم إنشاء {len(majors)} تخصص')

    def create_admin_user(self):
        """إنشاء حساب الأدمن الافتراضي"""
        admin_role = Role.objects.get(role_name='admin')
        
        admin_user, created = User.objects.get_or_create(
            academic_id='admin',
            defaults={
                'email': 'admin@s-acm.com',
                'full_name': 'مسؤول النظام',
                'role': admin_role,
                'account_status': 'active',
                'id_card_number': '0000000000',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('  - تم إنشاء حساب الأدمن (academic_id: admin, password: admin123)')
        else:
            self.stdout.write('  - حساب الأدمن موجود مسبقاً')
