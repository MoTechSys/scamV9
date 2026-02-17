"""
Management Command - Initial System Data Setup.

Creates default roles, permissions, role-permission bindings,
academic levels, semesters, sample majors, and an admin user.

S-ACM - Smart Academic Content Management System
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import (
    Role, Permission, RolePermission, Level, Semester, Major, User,
)
from datetime import date


class Command(BaseCommand):
    """Bootstrap command that populates the database with seed data."""

    help = 'Create initial system data (roles, permissions, levels, semesters)'

    def handle(self, *args, **options):
        self.stdout.write('Creating initial data ...\n')

        with transaction.atomic():
            self.create_roles()
            self.create_permissions()
            self.create_role_permissions()
            self.create_levels()
            self.create_semesters()
            self.create_sample_majors()
            self.create_admin_user()

        self.stdout.write(
            self.style.SUCCESS('\n✓ Initial data created successfully!')
        )

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------
    def create_roles(self):
        """Create the three system roles: admin, instructor, student."""
        roles = [
            {
                'code': 'admin',
                'display_name': 'مسؤول النظام',
                'description': 'مسؤول النظام - صلاحيات كاملة',
                'is_system': True,
            },
            {
                'code': 'instructor',
                'display_name': 'مدرس',
                'description': 'مدرس - إدارة المقررات والملفات',
                'is_system': True,
            },
            {
                'code': 'student',
                'display_name': 'طالب',
                'description': 'طالب - الوصول للمحتوى الأكاديمي',
                'is_system': True,
            },
        ]

        for data in roles:
            role, created = Role.objects.get_or_create(
                code=data['code'],
                defaults={
                    'display_name': data['display_name'],
                    'description': data['description'],
                    'is_system': data['is_system'],
                },
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  - Role: {role.code} ({status})')

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------
    def create_permissions(self):
        """Create all granular permissions grouped by category."""
        permissions = [
            # Users
            {'code': 'manage_users', 'display_name': 'إدارة المستخدمين',
             'category': 'users', 'description': 'إدارة المستخدمين'},
            {'code': 'view_users', 'display_name': 'عرض المستخدمين',
             'category': 'users', 'description': 'عرض المستخدمين'},
            {'code': 'promote_students', 'display_name': 'ترقية الطلاب',
             'category': 'users', 'description': 'ترقية الطلاب'},
            # Courses
            {'code': 'manage_courses', 'display_name': 'إدارة المقررات',
             'category': 'courses', 'description': 'إدارة المقررات'},
            {'code': 'view_courses', 'display_name': 'عرض المقررات',
             'category': 'courses', 'description': 'عرض المقررات'},
            {'code': 'assign_instructors', 'display_name': 'تعيين المدرسين',
             'category': 'courses', 'description': 'تعيين المدرسين للمقررات'},
            # Files
            {'code': 'upload_files', 'display_name': 'رفع الملفات',
             'category': 'files', 'description': 'رفع الملفات'},
            {'code': 'delete_files', 'display_name': 'حذف الملفات',
             'category': 'files', 'description': 'حذف الملفات'},
            {'code': 'view_files', 'display_name': 'عرض الملفات',
             'category': 'files', 'description': 'عرض الملفات'},
            {'code': 'download_files', 'display_name': 'تحميل الملفات',
             'category': 'files', 'description': 'تحميل الملفات'},
            # AI
            {'code': 'use_ai_features', 'display_name': 'استخدام ميزات AI',
             'category': 'ai', 'description': 'استخدام ميزات الذكاء الاصطناعي'},
            # Notifications
            {'code': 'send_notifications', 'display_name': 'إرسال الإشعارات',
             'category': 'notifications', 'description': 'إرسال الإشعارات'},
            # System
            {'code': 'manage_semesters', 'display_name': 'إدارة الفصول',
             'category': 'system', 'description': 'إدارة الفصول الدراسية'},
            {'code': 'manage_majors', 'display_name': 'إدارة التخصصات',
             'category': 'system', 'description': 'إدارة التخصصات'},
            {'code': 'view_statistics', 'display_name': 'عرض الإحصائيات',
             'category': 'system', 'description': 'عرض الإحصائيات'},
        ]

        for data in permissions:
            Permission.objects.get_or_create(
                code=data['code'],
                defaults={
                    'display_name': data['display_name'],
                    'description': data['description'],
                    'category': data['category'],
                },
            )

        self.stdout.write(f'  - Created {len(permissions)} permissions')

    # ------------------------------------------------------------------
    # Role ↔ Permission bindings
    # ------------------------------------------------------------------
    def create_role_permissions(self):
        """Bind permissions to each role."""
        # Admin gets everything
        admin_role = Role.objects.get(code='admin')
        for perm in Permission.objects.all():
            RolePermission.objects.get_or_create(
                role=admin_role, permission=perm,
            )

        # Instructor permissions
        instructor_role = Role.objects.get(code='instructor')
        for code in [
            'view_courses', 'upload_files', 'delete_files',
            'view_files', 'download_files', 'send_notifications',
            'view_statistics',
        ]:
            perm = Permission.objects.get(code=code)
            RolePermission.objects.get_or_create(
                role=instructor_role, permission=perm,
            )

        # Student permissions
        student_role = Role.objects.get(code='student')
        for code in [
            'view_courses', 'view_files', 'download_files',
            'use_ai_features',
        ]:
            perm = Permission.objects.get(code=code)
            RolePermission.objects.get_or_create(
                role=student_role, permission=perm,
            )

        self.stdout.write('  - Role-permission bindings created')

    # ------------------------------------------------------------------
    # Levels
    # ------------------------------------------------------------------
    def create_levels(self):
        """Create eight academic levels."""
        names = [
            'المستوى الأول', 'المستوى الثاني', 'المستوى الثالث',
            'المستوى الرابع', 'المستوى الخامس', 'المستوى السادس',
            'المستوى السابع', 'المستوى الثامن',
        ]
        for i, name in enumerate(names, start=1):
            Level.objects.get_or_create(
                level_number=i, defaults={'level_name': name},
            )
        self.stdout.write(f'  - Created {len(names)} academic levels')

    # ------------------------------------------------------------------
    # Semesters
    # ------------------------------------------------------------------
    def create_semesters(self):
        """Create two semesters for the current academic year."""
        year = date.today().year
        semesters = [
            {
                'name': f'الفصل الأول {year}/{year + 1}',
                'academic_year': f'{year}/{year + 1}',
                'semester_number': 1,
                'start_date': date(year, 9, 1),
                'end_date': date(year, 12, 31),
                'is_current': True,
            },
            {
                'name': f'الفصل الثاني {year}/{year + 1}',
                'academic_year': f'{year}/{year + 1}',
                'semester_number': 2,
                'start_date': date(year + 1, 1, 15),
                'end_date': date(year + 1, 5, 31),
                'is_current': False,
            },
        ]
        for data in semesters:
            Semester.objects.get_or_create(
                name=data['name'],
                defaults={
                    'academic_year': data['academic_year'],
                    'semester_number': data['semester_number'],
                    'start_date': data['start_date'],
                    'end_date': data['end_date'],
                    'is_current': data['is_current'],
                },
            )
        self.stdout.write(f'  - Created {len(semesters)} semesters')

    # ------------------------------------------------------------------
    # Sample Majors
    # ------------------------------------------------------------------
    def create_sample_majors(self):
        """Create four sample academic majors."""
        majors = [
            ('علوم الحاسب', 'قسم علوم الحاسب الآلي'),
            ('نظم المعلومات', 'قسم نظم المعلومات'),
            ('هندسة البرمجيات', 'قسم هندسة البرمجيات'),
            ('الذكاء الاصطناعي', 'قسم الذكاء الاصطناعي'),
        ]
        for name, desc in majors:
            Major.objects.get_or_create(
                major_name=name, defaults={'description': desc},
            )
        self.stdout.write(f'  - Created {len(majors)} majors')

    # ------------------------------------------------------------------
    # Admin User
    # ------------------------------------------------------------------
    def create_admin_user(self):
        """Create the default admin super-user."""
        admin_role = Role.objects.get(code='admin')
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
            },
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(
                '  - Admin created (academic_id: admin, password: admin123)'
            )
        else:
            self.stdout.write('  - Admin already exists')
