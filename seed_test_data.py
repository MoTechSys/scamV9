#!/usr/bin/env python3
"""
سكريبت زراعة بيانات الاختبار لمشروع S-ACM
يقوم بإنشاء بيانات اختبار منطقية للتحقق من الوظائف
"""

import os
import sys
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.accounts.models import Role, Permission, RolePermission, Major, Level, Semester, User
from apps.courses.models import Course, CourseMajor, InstructorCourse, LectureFile
from apps.notifications.models import Notification, NotificationRecipient

def create_roles():
    """إنشاء الأدوار الأساسية"""
    print("📋 إنشاء الأدوار...")
    roles_data = [
        ('admin', 'مدير النظام', 'مدير النظام - صلاحيات كاملة'),
        ('instructor', 'مدرس', 'مدرس - إدارة المقررات والملفات'),
        ('student', 'طالب', 'طالب - عرض المحتوى والتفاعل'),
    ]
    
    created_roles = []
    for code, display_name, description in roles_data:
        role, created = Role.objects.get_or_create(
            code=code,
            defaults={
                'display_name': display_name,
                'description': description,
                'is_system': True
            }
        )
        status = "✅ تم إنشاؤه" if created else "⏭️ موجود مسبقاً"
        print(f"   - {display_name} ({code}): {status}")
        created_roles.append(role)
    
    return created_roles


def create_permissions():
    """إنشاء الصلاحيات الأساسية"""
    print("🔐 إنشاء الصلاحيات...")
    permissions_data = [
        ('manage_users', 'إدارة المستخدمين'),
        ('manage_courses', 'إدارة المقررات'),
        ('manage_files', 'إدارة الملفات'),
        ('view_reports', 'عرض التقارير'),
        ('upload_files', 'رفع الملفات'),
        ('view_files', 'عرض الملفات'),
        ('use_ai_features', 'استخدام ميزات الذكاء الاصطناعي'),
        ('send_notifications', 'إرسال الإشعارات'),
    ]
    
    for code, display_name in permissions_data:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                'display_name': display_name,
                'description': f'صلاحية {display_name}',
                'category': 'system'
            }
        )
    
    # ربط الصلاحيات بالأدوار
    admin_role = Role.objects.get(code='admin')
    instructor_role = Role.objects.get(code='instructor')
    student_role = Role.objects.get(code='student')
    
    # Admin: جميع الصلاحيات
    for perm in Permission.objects.all():
        RolePermission.objects.get_or_create(role=admin_role, permission=perm)
    
    # Instructor: صلاحيات محددة
    instructor_perms = ['upload_files', 'view_files', 'manage_files', 'use_ai_features', 'send_notifications']
    for perm_code in instructor_perms:
        perm = Permission.objects.get(code=perm_code)
        RolePermission.objects.get_or_create(role=instructor_role, permission=perm)
    
    # Student: صلاحيات محدودة
    student_perms = ['view_files', 'use_ai_features']
    for perm_code in student_perms:
        perm = Permission.objects.get(code=perm_code)
        RolePermission.objects.get_or_create(role=student_role, permission=perm)
    
    print("   ✅ تم ربط الصلاحيات بالأدوار")


def create_majors():
    """إنشاء التخصصات"""
    print("🎓 إنشاء التخصصات...")
    majors_data = [
        ('علوم الحاسب', 'تخصص علوم الحاسب والبرمجة'),
        ('نظم المعلومات', 'تخصص نظم المعلومات'),
        ('هندسة البرمجيات', 'تخصص هندسة البرمجيات'),
        ('الذكاء الاصطناعي', 'تخصص الذكاء الاصطناعي'),
    ]
    
    for name, description in majors_data:
        Major.objects.get_or_create(
            major_name=name,
            defaults={'description': description, 'is_active': True}
        )
        print(f"   - {name}")
    
    return Major.objects.all()


def create_levels():
    """إنشاء المستويات الدراسية"""
    print("📊 إنشاء المستويات...")
    for i in range(1, 9):
        Level.objects.get_or_create(
            level_number=i,
            defaults={
                'level_name': f'المستوى {i}',
                'description': f'المستوى الدراسي {i}'
            }
        )
    
    print(f"   ✅ تم إنشاء 8 مستويات")
    return Level.objects.all()


def create_semesters():
    """إنشاء الفصول الدراسية"""
    print("📅 إنشاء الفصول الدراسية...")
    
    # الفصل الحالي
    current_semester, _ = Semester.objects.get_or_create(
        name='الفصل الأول 1446',
        defaults={
            'academic_year': '1445/1446',
            'semester_number': 1,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timezone.timedelta(days=120),
            'is_current': True
        }
    )
    
    # الفصل الثاني (القادم) لتوضيح الأرشفة
    next_semester, _ = Semester.objects.get_or_create(
        name='الفصل الثاني 1446',
        defaults={
            'academic_year': '1445/1446',
            'semester_number': 2,
            'start_date': timezone.now().date() + timezone.timedelta(days=121),
            'end_date': timezone.now().date() + timezone.timedelta(days=240),
            'is_current': False
        }
    )
    
    # فصل سابق (مؤرشف)
    archived_semester, _ = Semester.objects.get_or_create(
        name='الفصل الثاني 1445',
        defaults={
            'academic_year': '1444/1445',
            'semester_number': 2,
            'start_date': timezone.now().date() - timezone.timedelta(days=240),
            'end_date': timezone.now().date() - timezone.timedelta(days=120),
            'is_current': False
        }
    )
    
    print(f"   - الفصل الحالي: {current_semester.name}")
    print(f"   - الفصل المؤرشف: {archived_semester.name}")
    
    return current_semester, archived_semester


def create_users():
    """إنشاء المستخدمين للاختبار"""
    print("👥 إنشاء المستخدمين...")
    
    admin_role = Role.objects.get(code='admin')
    instructor_role = Role.objects.get(code='instructor')
    student_role = Role.objects.get(code='student')
    
    cs_major = Major.objects.get(major_name='علوم الحاسب')
    level_7 = Level.objects.get(level_number=7)
    level_8 = Level.objects.get(level_number=8)
    
    users_created = []
    
    # 1. مسؤول النظام
    admin, created = User.objects.get_or_create(
        academic_id='admin',
        defaults={
            'id_card_number': '1000000001',
            'full_name': 'مسؤول النظام',
            'email': 'admin@sacm.edu',
            'role': admin_role,
            'account_status': 'active',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password('Admin@123')
        admin.save()
    users_created.append(('Admin', admin, created))
    
    # 2. مدرس
    instructor, created = User.objects.get_or_create(
        academic_id='inst001',
        defaults={
            'id_card_number': '1000000002',
            'full_name': 'د. أحمد محمد',
            'email': 'ahmed@sacm.edu',
            'role': instructor_role,
            'account_status': 'active'
        }
    )
    if created:
        instructor.set_password('Inst@123')
        instructor.save()
    users_created.append(('Instructor', instructor, created))
    
    # 3. طالب مستوى 7
    student_7, created = User.objects.get_or_create(
        academic_id='202101',
        defaults={
            'id_card_number': '1000000003',
            'full_name': 'عبدالله سعد',
            'email': 'abdullah@sacm.edu',
            'role': student_role,
            'major': cs_major,
            'level': level_7,
            'account_status': 'active'
        }
    )
    if created:
        student_7.set_password('Student@123')
        student_7.save()
    users_created.append(('Student Level 7', student_7, created))
    
    # 4. طالب مستوى 8 (للاختبار الخريجين)
    student_8, created = User.objects.get_or_create(
        academic_id='202001',
        defaults={
            'id_card_number': '1000000004',
            'full_name': 'محمد خالد',
            'email': 'mohammed@sacm.edu',
            'role': student_role,
            'major': cs_major,
            'level': level_8,
            'account_status': 'active'
        }
    )
    if created:
        student_8.set_password('Student@123')
        student_8.save()
    users_created.append(('Student Level 8', student_8, created))
    
    for label, user, created in users_created:
        status = "✅ تم إنشاؤه" if created else "⏭️ موجود مسبقاً"
        print(f"   - {label}: {user.full_name} ({user.academic_id}) - {status}")
    
    return admin, instructor, student_7, student_8


def create_courses(current_semester, instructor):
    """إنشاء المقررات"""
    print("📚 إنشاء المقررات...")
    
    cs_major = Major.objects.get(major_name='علوم الحاسب')
    level_7 = Level.objects.get(level_number=7)
    level_8 = Level.objects.get(level_number=8)
    
    # مقرر للمستوى 7
    course_7, created = Course.objects.get_or_create(
        course_code='CS401',
        defaults={
            'course_name': 'هندسة البرمجيات',
            'description': 'مقرر متقدم في هندسة البرمجيات ومراحل تطوير النظم',
            'level': level_7,
            'semester': current_semester,
            'credit_hours': 3
        }
    )
    
    # مقرر للمستوى 8
    course_8, created = Course.objects.get_or_create(
        course_code='CS402',
        defaults={
            'course_name': 'مشروع التخرج',
            'description': 'مشروع التخرج للمستوى الثامن وتطبيق المعارف',
            'level': level_8,
            'semester': current_semester,
            'credit_hours': 6
        }
    )
    
    # ربط المقررات بالتخصص
    CourseMajor.objects.get_or_create(course=course_7, major=cs_major)
    CourseMajor.objects.get_or_create(course=course_8, major=cs_major)
    
    # تعيين المدرس للمقررات
    InstructorCourse.objects.get_or_create(
        instructor=instructor,
        course=course_7,
        defaults={'is_primary': True}
    )
    InstructorCourse.objects.get_or_create(
        instructor=instructor,
        course=course_8,
        defaults={'is_primary': True}
    )
    
    print(f"   - {course_7.course_code}: {course_7.course_name}")
    print(f"   - {course_8.course_code}: {course_8.course_name}")
    
    return course_7, course_8


def create_lecture_file(course, instructor):
    """إنشاء ملف محاضرة للاختبار"""
    print("📄 إنشاء ملف محاضرة...")
    
    # استخدام Lecture كنوع ملف (متوافق مع الاختيارات)
    lecture, created = LectureFile.objects.get_or_create(
        course=course,
        title='المحاضرة الأولى - مقدمة',
        defaults={
            'description': 'مقدمة في هندسة البرمجيات ومفاهيمها الأساسية',
            'file_type': 'Lecture',
            'content_type': 'external_link',
            'external_link': 'https://example.com/lecture1.pdf',
            'uploader': instructor,
            'is_visible': True
        }
    )
    
    status = "✅ تم إنشاؤه" if created else "⏭️ موجود مسبقاً"
    print(f"   - {lecture.title}: {status}")
    
    return lecture


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🌱 بدء زراعة بيانات الاختبار لمشروع S-ACM")
    print("=" * 60)
    print()
    
    # إنشاء البيانات الأساسية
    create_roles()
    create_permissions()
    majors = create_majors()
    levels = create_levels()
    current_semester, archived_semester = create_semesters()
    
    print()
    
    # إنشاء المستخدمين
    admin, instructor, student_7, student_8 = create_users()
    
    print()
    
    # إنشاء المقررات
    course_7, course_8 = create_courses(current_semester, instructor)
    
    print()
    
    # إنشاء ملف محاضرة
    lecture = create_lecture_file(course_7, instructor)
    
    print()
    print("=" * 60)
    print("✅ تم زراعة بيانات الاختبار بنجاح!")
    print("=" * 60)
    print()
    print("📋 ملخص البيانات المنشأة:")
    print(f"   - الأدوار: {Role.objects.count()}")
    print(f"   - الصلاحيات: {Permission.objects.count()}")
    print(f"   - التخصصات: {Major.objects.count()}")
    print(f"   - المستويات: {Level.objects.count()}")
    print(f"   - الفصول: {Semester.objects.count()}")
    print(f"   - المستخدمون: {User.objects.count()}")
    print(f"   - المقررات: {Course.objects.count()}")
    print(f"   - الملفات: {LectureFile.objects.count()}")
    print()
    print("🔑 بيانات تسجيل الدخول:")
    print("   - Admin: admin / Admin@123")
    print("   - Instructor: inst001 / Inst@123")
    print("   - Student L7: 202101 / Student@123")
    print("   - Student L8: 202001 / Student@123")
    print()


if __name__ == '__main__':
    main()
