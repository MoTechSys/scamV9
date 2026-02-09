"""
اختبارات شاملة لنظام الإشعارات v2
S-ACM - Smart Academic Content Management System

يغطي:
1. Models: إنشاء وقراءة الإشعارات، NotificationRecipient، NotificationPreference
2. Services: NotificationService - إنشاء، استهداف، قراءة، تحديث
3. Targeting Logic: استهداف طلاب المقرر، التخصص، المستوى، الجميع
4. Views: Composer، List، Detail، HTMX endpoints
5. Signals: إشعارات تلقائية عند رفع ملف
"""

from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import User, Role, Major, Level, Semester
from apps.courses.models import Course, CourseMajor, InstructorCourse
from apps.notifications.models import Notification, NotificationRecipient, NotificationPreference
from apps.notifications.services import NotificationService


class NotificationTestBase(TestCase):
    """Base class مع بيانات اختبار مشتركة"""

    @classmethod
    def setUpTestData(cls):
        """إعداد بيانات الاختبار مرة واحدة"""
        # === الأدوار ===
        cls.admin_role = Role.objects.create(
            code='admin', display_name='مدير', is_system=True
        )
        cls.instructor_role = Role.objects.create(
            code='instructor', display_name='مدرس', is_system=True
        )
        cls.student_role = Role.objects.create(
            code='student', display_name='طالب', is_system=True
        )

        # === التخصصات والمستويات ===
        cls.major_cs = Major.objects.create(major_name='علوم حاسب')
        cls.major_is = Major.objects.create(major_name='نظم معلومات')
        cls.level_1 = Level.objects.create(level_name='المستوى الأول', level_number=1)
        cls.level_2 = Level.objects.create(level_name='المستوى الثاني', level_number=2)

        # === الفصل الدراسي ===
        cls.semester = Semester.objects.create(
            name='الفصل الأول 2026',
            academic_year='2025/2026',
            semester_number=1,
            start_date='2025-09-01',
            end_date='2026-01-15',
            is_current=True,
        )

        # === المستخدمون ===
        cls.admin_user = User.objects.create_user(
            academic_id='ADMIN001',
            password='TestPass123!',
            full_name='مدير النظام',
            id_card_number='ID_ADMIN_001',
            role=cls.admin_role,
            account_status='active',
        )
        cls.instructor_user = User.objects.create_user(
            academic_id='INST001',
            password='TestPass123!',
            full_name='دكتور أحمد',
            id_card_number='ID_INST_001',
            role=cls.instructor_role,
            account_status='active',
        )
        cls.student_1 = User.objects.create_user(
            academic_id='STU001',
            password='TestPass123!',
            full_name='طالب واحد',
            id_card_number='ID_STU_001',
            role=cls.student_role,
            major=cls.major_cs,
            level=cls.level_1,
            account_status='active',
        )
        cls.student_2 = User.objects.create_user(
            academic_id='STU002',
            password='TestPass123!',
            full_name='طالب اثنان',
            id_card_number='ID_STU_002',
            role=cls.student_role,
            major=cls.major_cs,
            level=cls.level_1,
            account_status='active',
        )
        cls.student_3 = User.objects.create_user(
            academic_id='STU003',
            password='TestPass123!',
            full_name='طالب ثلاثة',
            id_card_number='ID_STU_003',
            role=cls.student_role,
            major=cls.major_is,
            level=cls.level_1,
            account_status='active',
        )
        cls.student_inactive = User.objects.create_user(
            academic_id='STU_INACTIVE',
            password='TestPass123!',
            full_name='طالب غير نشط',
            id_card_number='ID_STU_INACTIVE',
            role=cls.student_role,
            major=cls.major_cs,
            level=cls.level_1,
            account_status='inactive',
        )

        # === المقرر ===
        cls.course = Course.objects.create(
            course_name='برمجة 1',
            course_code='CS101',
            level=cls.level_1,
            semester=cls.semester,
        )
        CourseMajor.objects.create(course=cls.course, major=cls.major_cs)
        InstructorCourse.objects.create(
            instructor=cls.instructor_user,
            course=cls.course,
        )


class NotificationModelTests(NotificationTestBase):
    """اختبارات نماذج الإشعارات"""

    def test_create_notification(self):
        """اختبار إنشاء إشعار"""
        notif = Notification.objects.create(
            title='إشعار تجريبي',
            body='محتوى الإشعار',
            notification_type='general',
            priority='normal',
            sender=self.instructor_user,
        )
        self.assertEqual(str(notif), 'إشعار تجريبي')
        self.assertEqual(notif.priority_color, 'info')
        self.assertFalse(notif.is_expired)

    def test_priority_colors(self):
        """اختبار ألوان الأولوية"""
        for priority, expected_color in [
            ('low', 'secondary'), ('normal', 'info'),
            ('high', 'warning'), ('urgent', 'danger'),
        ]:
            notif = Notification(priority=priority)
            self.assertEqual(notif.priority_color, expected_color)

    def test_notification_with_generic_fk(self):
        """اختبار ربط GenericForeignKey بالمقرر"""
        ct = ContentType.objects.get_for_model(Course)
        notif = Notification.objects.create(
            title='إشعار مقرر',
            body='محتوى',
            content_type=ct,
            object_id=self.course.pk,
            course=self.course,
        )
        self.assertEqual(notif.content_type, ct)
        self.assertEqual(notif.object_id, self.course.pk)

    def test_recipient_mark_as_read(self):
        """اختبار تحديد كمقروء"""
        notif = Notification.objects.create(
            title='إشعار', body='محتوى',
        )
        recipient = NotificationRecipient.objects.create(
            notification=notif, user=self.student_1,
        )
        self.assertFalse(recipient.is_read)
        recipient.mark_as_read()
        recipient.refresh_from_db()
        self.assertTrue(recipient.is_read)
        self.assertIsNotNone(recipient.read_at)

    def test_recipient_soft_delete_and_restore(self):
        """اختبار الحذف الناعم والاستعادة"""
        notif = Notification.objects.create(title='إشعار', body='محتوى')
        recipient = NotificationRecipient.objects.create(
            notification=notif, user=self.student_1,
        )
        recipient.soft_delete()
        recipient.refresh_from_db()
        self.assertTrue(recipient.is_deleted)
        self.assertIsNotNone(recipient.deleted_at)

        recipient.restore()
        recipient.refresh_from_db()
        self.assertFalse(recipient.is_deleted)
        self.assertIsNone(recipient.deleted_at)

    def test_notification_preference(self):
        """اختبار تفضيلات الإشعارات"""
        prefs = NotificationPreference.get_or_create_for_user(self.student_1)
        self.assertTrue(prefs.email_enabled)
        self.assertTrue(prefs.email_file_upload)


class TargetingTests(NotificationTestBase):
    """اختبارات منطق الاستهداف - الأهم!"""

    def test_target_course_students(self):
        """اختبار استهداف طلاب مقرر: يجب أن يشمل طلاب التخصص والمستوى فقط"""
        users = NotificationService.get_targeted_users(
            target_type='course_students',
            course=self.course,
        )
        user_ids = set(users.values_list('pk', flat=True))

        # يجب أن يشمل student_1 و student_2 (CS, Level 1)
        self.assertIn(self.student_1.pk, user_ids)
        self.assertIn(self.student_2.pk, user_ids)

        # يجب ألا يشمل student_3 (IS) أو student_inactive
        self.assertNotIn(self.student_3.pk, user_ids)
        self.assertNotIn(self.student_inactive.pk, user_ids)

    def test_target_all_students(self):
        """اختبار استهداف جميع الطلاب النشطين"""
        users = NotificationService.get_targeted_users(target_type='all_students')
        user_ids = set(users.values_list('pk', flat=True))

        self.assertIn(self.student_1.pk, user_ids)
        self.assertIn(self.student_2.pk, user_ids)
        self.assertIn(self.student_3.pk, user_ids)
        self.assertNotIn(self.student_inactive.pk, user_ids)
        self.assertNotIn(self.instructor_user.pk, user_ids)

    def test_target_major_students(self):
        """اختبار استهداف طلاب تخصص محدد"""
        users = NotificationService.get_targeted_users(
            target_type='major_students',
            major=self.major_cs,
        )
        user_ids = set(users.values_list('pk', flat=True))
        self.assertIn(self.student_1.pk, user_ids)
        self.assertIn(self.student_2.pk, user_ids)
        self.assertNotIn(self.student_3.pk, user_ids)

    def test_target_major_and_level(self):
        """اختبار استهداف طلاب تخصص ومستوى"""
        users = NotificationService.get_targeted_users(
            target_type='major_students',
            major=self.major_cs,
            level=self.level_2,  # لا يوجد طلاب في المستوى الثاني
        )
        self.assertEqual(users.count(), 0)

    def test_target_all_instructors(self):
        """اختبار استهداف جميع المدرسين"""
        users = NotificationService.get_targeted_users(target_type='all_instructors')
        user_ids = set(users.values_list('pk', flat=True))
        self.assertIn(self.instructor_user.pk, user_ids)
        self.assertNotIn(self.student_1.pk, user_ids)

    def test_target_everyone(self):
        """اختبار استهداف الجميع"""
        users = NotificationService.get_targeted_users(target_type='everyone')
        user_ids = set(users.values_list('pk', flat=True))
        self.assertIn(self.admin_user.pk, user_ids)
        self.assertIn(self.instructor_user.pk, user_ids)
        self.assertIn(self.student_1.pk, user_ids)
        self.assertNotIn(self.student_inactive.pk, user_ids)

    def test_target_specific_student(self):
        """اختبار استهداف طالب محدد"""
        users = NotificationService.get_targeted_users(
            target_type='specific_student',
            specific_user_id=self.student_1.pk,
        )
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.student_1)

    def test_target_course_without_course_returns_empty(self):
        """اختبار أن استهداف طلاب مقرر بدون تحديد مقرر يُرجع فارغ"""
        users = NotificationService.get_targeted_users(
            target_type='course_students',
            course=None,
        )
        self.assertEqual(users.count(), 0)


class NotificationServiceTests(NotificationTestBase):
    """اختبارات خدمة الإشعارات"""

    def test_create_notification_with_recipients(self):
        """اختبار إنشاء إشعار مع مستلمين"""
        recipients = User.objects.filter(pk__in=[self.student_1.pk, self.student_2.pk])
        notif = NotificationService.create_notification(
            title='إشعار اختبار',
            body='محتوى الإشعار',
            recipients=recipients,
            sender=self.instructor_user,
        )
        self.assertEqual(notif.recipients.count(), 2)

    def test_notify_file_upload(self):
        """اختبار إشعار رفع ملف - يصل لطلاب المقرر فقط"""
        from apps.courses.models import LectureFile
        file_obj = LectureFile.objects.create(
            course=self.course,
            uploader=self.instructor_user,
            title='محاضرة 1',
            is_visible=True,
        )
        notif = NotificationService.notify_file_upload(file_obj, self.course)
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, 'file_upload')
        # يجب أن يصل لطلاب CS Level 1 فقط (student_1 و student_2)
        self.assertEqual(notif.recipients.count(), 2)

    def test_notify_system(self):
        """اختبار إشعار نظام لجميع المستخدمين"""
        notif = NotificationService.notify_system(
            title='صيانة النظام',
            body='سيتم إيقاف النظام مؤقتاً',
        )
        # يجب أن يصل لجميع المستخدمين النشطين
        active_count = User.objects.filter(account_status='active').count()
        self.assertEqual(notif.recipients.count(), active_count)

    def test_unread_count(self):
        """اختبار عدد الإشعارات غير المقروءة"""
        notif = Notification.objects.create(title='إشعار', body='محتوى')
        NotificationRecipient.objects.create(
            notification=notif, user=self.student_1,
        )
        count = NotificationService.get_unread_count(self.student_1)
        self.assertEqual(count, 1)

    def test_mark_as_read(self):
        """اختبار تحديد كمقروء"""
        notif = Notification.objects.create(title='إشعار', body='محتوى')
        NotificationRecipient.objects.create(
            notification=notif, user=self.student_1,
        )
        result = NotificationService.mark_as_read(notif.pk, self.student_1)
        self.assertTrue(result)
        self.assertEqual(NotificationService.get_unread_count(self.student_1), 0)

    def test_mark_all_as_read(self):
        """اختبار تحديد الكل كمقروء"""
        for i in range(5):
            notif = Notification.objects.create(title=f'إشعار {i}', body='محتوى')
            NotificationRecipient.objects.create(
                notification=notif, user=self.student_1,
            )
        self.assertEqual(NotificationService.get_unread_count(self.student_1), 5)
        NotificationService.mark_all_as_read(self.student_1)
        self.assertEqual(NotificationService.get_unread_count(self.student_1), 0)

    def test_soft_delete_and_restore(self):
        """اختبار الحذف والاستعادة عبر الخدمة"""
        notif = Notification.objects.create(title='إشعار', body='محتوى')
        NotificationRecipient.objects.create(
            notification=notif, user=self.student_1,
        )
        NotificationService.soft_delete(notif.pk, self.student_1)
        # يجب ألا يظهر في القائمة العادية
        normal_list = NotificationService.get_user_notifications(
            self.student_1, filter_type='all'
        )
        self.assertEqual(normal_list.count(), 0)
        # يجب أن يظهر في سلة المهملات
        trash_list = NotificationService.get_user_notifications(
            self.student_1, filter_type='trash'
        )
        self.assertEqual(trash_list.count(), 1)
        # الاستعادة
        NotificationService.restore_from_trash(notif.pk, self.student_1)
        normal_list = NotificationService.get_user_notifications(
            self.student_1, filter_type='all'
        )
        self.assertEqual(normal_list.count(), 1)

    def test_empty_trash(self):
        """اختبار إفراغ سلة المهملات"""
        for i in range(3):
            notif = Notification.objects.create(title=f'إشعار {i}', body='محتوى')
            nr = NotificationRecipient.objects.create(
                notification=notif, user=self.student_1,
            )
            nr.soft_delete()
        NotificationService.empty_trash(self.student_1)
        trash = NotificationService.get_user_notifications(
            self.student_1, filter_type='trash'
        )
        self.assertEqual(trash.count(), 0)

    def test_get_sent_notifications(self):
        """اختبار جلب الإشعارات المرسلة"""
        NotificationService.create_notification(
            title='إشعار مرسل',
            body='محتوى',
            sender=self.instructor_user,
            recipients=[self.student_1],
        )
        sent = NotificationService.get_sent_notifications(self.instructor_user)
        self.assertEqual(sent.count(), 1)
        self.assertEqual(sent.first().recipients_count, 1)


class ViewTests(NotificationTestBase):
    """اختبارات Views"""

    def setUp(self):
        self.client = Client()

    def test_list_view_requires_login(self):
        """اختبار أن قائمة الإشعارات تتطلب تسجيل دخول"""
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 302)

    def test_list_view_logged_in(self):
        """اختبار عرض قائمة الإشعارات"""
        self.client.login(academic_id='STU001', password='TestPass123!')
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        """اختبار عرض تفاصيل إشعار"""
        notif = Notification.objects.create(title='إشعار', body='محتوى')
        NotificationRecipient.objects.create(
            notification=notif, user=self.student_1,
        )
        self.client.login(academic_id='STU001', password='TestPass123!')
        response = self.client.get(reverse('notifications:detail', args=[notif.pk]))
        self.assertEqual(response.status_code, 200)

    def test_mark_as_read_view(self):
        """اختبار تحديد كمقروء عبر View"""
        notif = Notification.objects.create(title='إشعار', body='محتوى')
        NotificationRecipient.objects.create(
            notification=notif, user=self.student_1,
        )
        self.client.login(academic_id='STU001', password='TestPass123!')
        response = self.client.post(
            reverse('notifications:mark_read', args=[notif.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_unread_count_api(self):
        """اختبار API عدد غير المقروءة"""
        self.client.login(academic_id='STU001', password='TestPass123!')
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)

    def test_composer_view_instructor(self):
        """اختبار صفحة إنشاء إشعار للمدرس"""
        self.client.login(academic_id='INST001', password='TestPass123!')
        response = self.client.get(reverse('notifications:compose'))
        self.assertEqual(response.status_code, 200)

    def test_composer_view_student_denied(self):
        """اختبار أن الطالب لا يستطيع الوصول لصفحة الإنشاء"""
        self.client.login(academic_id='STU001', password='TestPass123!')
        response = self.client.get(reverse('notifications:compose'))
        self.assertEqual(response.status_code, 302)

    def test_trash_view(self):
        """اختبار صفحة سلة المهملات"""
        self.client.login(academic_id='STU001', password='TestPass123!')
        response = self.client.get(reverse('notifications:trash'))
        self.assertEqual(response.status_code, 200)

    def test_preferences_view(self):
        """اختبار صفحة التفضيلات"""
        self.client.login(academic_id='STU001', password='TestPass123!')
        response = self.client.get(reverse('notifications:preferences'))
        self.assertEqual(response.status_code, 200)


class HTMXEndpointTests(NotificationTestBase):
    """اختبارات HTMX Endpoints"""

    def setUp(self):
        self.client = Client()
        self.client.login(academic_id='INST001', password='TestPass123!')

    def test_htmx_levels_for_major(self):
        """اختبار Cascading Dropdown: المستويات حسب التخصص"""
        response = self.client.get(
            reverse('notifications:htmx_levels'),
            {'major': self.major_cs.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.level_1.level_name, response.content.decode())

    def test_htmx_students_count(self):
        """اختبار عدد المستلمين المتوقع"""
        response = self.client.get(
            reverse('notifications:htmx_students_count'),
            {'target_type': 'course_students', 'course': self.course.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('2', response.content.decode())  # 2 طلاب في المقرر

    def test_htmx_bell_update(self):
        """اختبار تحديث أيقونة الجرس"""
        response = self.client.get(reverse('notifications:htmx_bell'))
        self.assertEqual(response.status_code, 200)
