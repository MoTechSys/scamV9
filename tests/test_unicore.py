"""
Comprehensive Tests for S-ACM - Smart Academic Content Management System
UniCore-OS Phase 4: Full Test Suite

Tests cover: Models, Views, Forms, Templates, Security, URLs, Context Processors
Target: 57 tests - All Green
"""

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import json

User = get_user_model()


# ============================================================================
# Helper Mixins
# ============================================================================

class BaseTestMixin:
    """Base mixin with user creation helpers."""

    @classmethod
    def create_role(cls, code='student', display_name='طالب'):
        from apps.accounts.models import Role
        role, _ = Role.objects.get_or_create(
            code=code,
            defaults={
                'display_name': display_name,
                'is_active': True,
                'is_system': True,
            }
        )
        return role

    @classmethod
    def create_user(cls, academic_id='STU001', password='TestPass123!',
                    role_code='student', full_name='طالب تجريبي', **kwargs):
        role = cls.create_role(role_code, role_code)
        user = User.objects.create_user(
            academic_id=academic_id,
            password=password,
            full_name=full_name,
            id_card_number=kwargs.pop('id_card_number', f'ID-{academic_id}'),
            role=role,
            account_status='active',
            **kwargs
        )
        return user

    @classmethod
    def create_instructor(cls, academic_id='INS001', **kwargs):
        return cls.create_user(
            academic_id=academic_id,
            role_code='instructor',
            full_name=kwargs.pop('full_name', 'مدرس تجريبي'),
            **kwargs
        )

    @classmethod
    def create_admin_user(cls, academic_id='ADM001', **kwargs):
        return cls.create_user(
            academic_id=academic_id,
            role_code='admin',
            full_name=kwargs.pop('full_name', 'مدير تجريبي'),
            **kwargs
        )


# ============================================================================
# 1. Accounts Models Tests (8 tests)
# ============================================================================

class RoleModelTest(TestCase, BaseTestMixin):
    """Test Role model."""

    def test_role_creation(self):
        """T01: Role creation with code and display_name."""
        role = self.create_role('instructor', 'مدرس')
        self.assertEqual(role.code, 'instructor')
        self.assertEqual(role.display_name, 'مدرس')

    def test_role_str(self):
        """T02: Role string representation."""
        role = self.create_role('student', 'طالب')
        self.assertEqual(str(role), 'طالب')


class UserModelTest(TestCase, BaseTestMixin):
    """Test User model."""

    def test_user_creation(self):
        """T03: User creation with academic_id."""
        user = self.create_user()
        self.assertEqual(user.academic_id, 'STU001')
        self.assertTrue(user.check_password('TestPass123!'))

    def test_user_is_student(self):
        """T04: User role detection - student."""
        user = self.create_user(role_code='student')
        self.assertTrue(user.is_student())
        self.assertFalse(user.is_instructor())
        self.assertFalse(user.is_admin())

    def test_user_is_instructor(self):
        """T05: User role detection - instructor."""
        user = self.create_instructor()
        self.assertTrue(user.is_instructor())
        self.assertFalse(user.is_student())

    def test_user_is_admin(self):
        """T06: User role detection - admin."""
        user = self.create_admin_user()
        self.assertTrue(user.is_admin())

    def test_user_str(self):
        """T07: User string representation."""
        user = self.create_user(full_name='أحمد محمد')
        self.assertIn('أحمد محمد', str(user))

    def test_superuser_creation(self):
        """T08: Superuser creation."""
        su = User.objects.create_superuser(
            academic_id='SUPER01',
            password='SuperPass123!',
            full_name='سوبر أدمن',
            id_card_number='SU-001'
        )
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.is_staff)


# ============================================================================
# 2. Accounts Forms Tests (7 tests)
# ============================================================================

class ProfileUpdateFormTest(TestCase, BaseTestMixin):
    """Test ProfileUpdateForm."""

    def test_valid_form(self):
        """T09: Valid profile update form."""
        from apps.accounts.forms import ProfileUpdateForm
        user = self.create_user(email='test@test.com')
        form = ProfileUpdateForm(
            data={'full_name': 'اسم جديد', 'email': 'new@test.com'},
            instance=user
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_email(self):
        """T10: Duplicate email validation."""
        from apps.accounts.forms import ProfileUpdateForm
        user1 = self.create_user(academic_id='U1', email='taken@test.com', id_card_number='ID-U1')
        user2 = self.create_user(academic_id='U2', email='other@test.com', id_card_number='ID-U2')
        form = ProfileUpdateForm(
            data={'full_name': 'test', 'email': 'taken@test.com'},
            instance=user2
        )
        self.assertFalse(form.is_valid())


class ChangePasswordFormTest(TestCase, BaseTestMixin):
    """Test ChangePasswordForm."""

    def test_valid_form(self):
        """T11: Valid password change form."""
        from apps.accounts.forms import ChangePasswordForm
        user = self.create_user()
        form = ChangePasswordForm(user, data={
            'current_password': 'TestPass123!',
            'new_password1': 'NewSecure456!',
            'new_password2': 'NewSecure456!',
        })
        self.assertTrue(form.is_valid())

    def test_wrong_current_password(self):
        """T12: Wrong current password validation."""
        from apps.accounts.forms import ChangePasswordForm
        user = self.create_user()
        form = ChangePasswordForm(user, data={
            'current_password': 'WrongPassword',
            'new_password1': 'NewSecure456!',
            'new_password2': 'NewSecure456!',
        })
        self.assertFalse(form.is_valid())

    def test_password_mismatch(self):
        """T13: Password mismatch validation."""
        from apps.accounts.forms import ChangePasswordForm
        user = self.create_user()
        form = ChangePasswordForm(user, data={
            'current_password': 'TestPass123!',
            'new_password1': 'NewSecure456!',
            'new_password2': 'DifferentPass!',
        })
        self.assertFalse(form.is_valid())


class LoginFormTest(TestCase, BaseTestMixin):
    """Test LoginForm."""

    def test_login_form_fields(self):
        """T14: Login form has required fields."""
        from apps.accounts.forms import LoginForm
        form = LoginForm()
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)

    def test_login_form_placeholder(self):
        """T15: Login form has Arabic placeholder."""
        from apps.accounts.forms import LoginForm
        form = LoginForm()
        self.assertIn('الرقم الأكاديمي', form.fields['username'].widget.attrs.get('placeholder', ''))


# ============================================================================
# 3. Accounts Views Tests (8 tests)
# ============================================================================

class ProfileViewTest(TestCase, BaseTestMixin):
    """Test Profile views."""

    def setUp(self):
        self.client = Client()
        self.user = self.create_user(email='profile@test.com')
        self.client.login(username='STU001', password='TestPass123!')

    def test_profile_get(self):
        """T16: Profile page returns 200 with form context."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_profile_uses_dashboard_base(self):
        """T17: Profile page uses dashboard_base.html."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertTemplateUsed(response, 'layouts/dashboard_base.html')

    def test_profile_update_post(self):
        """T18: Profile update POST saves data."""
        response = self.client.post(reverse('accounts:profile'), {
            'full_name': 'اسم محدث',
            'email': 'updated@test.com',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@test.com')

    def test_profile_login_required(self):
        """T19: Profile requires login."""
        self.client.logout()
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class ChangePasswordViewTest(TestCase, BaseTestMixin):
    """Test Change Password view."""

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()
        self.client.login(username='STU001', password='TestPass123!')

    def test_change_password_get(self):
        """T20: Change password page returns 200."""
        response = self.client.get(reverse('accounts:change_password'))
        self.assertEqual(response.status_code, 200)

    def test_change_password_uses_dashboard_base(self):
        """T21: Change password uses dashboard_base.html."""
        response = self.client.get(reverse('accounts:change_password'))
        self.assertTemplateUsed(response, 'layouts/dashboard_base.html')

    def test_change_password_post(self):
        """T22: Successful password change."""
        response = self.client.post(reverse('accounts:change_password'), {
            'current_password': 'TestPass123!',
            'new_password1': 'NewSecure456!',
            'new_password2': 'NewSecure456!',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecure456!'))

    def test_change_password_login_required(self):
        """T23: Change password requires login."""
        self.client.logout()
        response = self.client.get(reverse('accounts:change_password'))
        self.assertEqual(response.status_code, 302)


# ============================================================================
# 4. Notification Models Tests (6 tests)
# ============================================================================

class NotificationModelTest(TestCase, BaseTestMixin):
    """Test Notification models."""

    def setUp(self):
        self.user = self.create_user()
        self.instructor = self.create_instructor()

    def test_notification_creation(self):
        """T24: Notification creation."""
        from apps.notifications.models import Notification
        n = Notification.objects.create(
            sender=self.instructor,
            title='إشعار تجريبي',
            body='محتوى الإشعار',
            notification_type='general',
        )
        self.assertEqual(n.title, 'إشعار تجريبي')
        self.assertTrue(n.is_active)

    def test_notification_recipient_creation(self):
        """T25: NotificationRecipient creation."""
        from apps.notifications.models import Notification, NotificationRecipient
        n = Notification.objects.create(
            sender=self.instructor,
            title='اختبار',
            body='محتوى',
        )
        nr = NotificationRecipient.objects.create(
            notification=n,
            user=self.user,
        )
        self.assertFalse(nr.is_read)
        self.assertFalse(nr.is_deleted)

    def test_mark_as_read(self):
        """T26: Mark notification as read."""
        from apps.notifications.models import Notification, NotificationRecipient
        n = Notification.objects.create(sender=self.instructor, title='T', body='B')
        nr = NotificationRecipient.objects.create(notification=n, user=self.user)
        nr.mark_as_read()
        nr.refresh_from_db()
        self.assertTrue(nr.is_read)
        self.assertIsNotNone(nr.read_at)

    def test_get_unread_count(self):
        """T27: Get unread notification count."""
        from apps.notifications.models import Notification, NotificationRecipient, NotificationManager
        n1 = Notification.objects.create(sender=self.instructor, title='T1', body='B')
        n2 = Notification.objects.create(sender=self.instructor, title='T2', body='B')
        NotificationRecipient.objects.create(notification=n1, user=self.user)
        NotificationRecipient.objects.create(notification=n2, user=self.user)
        self.assertEqual(NotificationManager.get_unread_count(self.user), 2)

    def test_get_user_notifications(self):
        """T28: Get user notifications queryset."""
        from apps.notifications.models import Notification, NotificationRecipient, NotificationManager
        n = Notification.objects.create(sender=self.instructor, title='T', body='B')
        NotificationRecipient.objects.create(notification=n, user=self.user)
        qs = NotificationManager.get_user_notifications(self.user)
        self.assertEqual(qs.count(), 1)

    def test_soft_delete_hides_notification(self):
        """T29: Soft deleted notification is hidden from queryset."""
        from apps.notifications.models import Notification, NotificationRecipient, NotificationManager
        n = Notification.objects.create(sender=self.instructor, title='T', body='B')
        nr = NotificationRecipient.objects.create(notification=n, user=self.user)
        nr.is_deleted = True
        nr.save()
        qs = NotificationManager.get_user_notifications(self.user)
        self.assertEqual(qs.count(), 0)


# ============================================================================
# 5. Notification Views Tests (6 tests)
# ============================================================================

class NotificationViewTest(TestCase, BaseTestMixin):
    """Test Notification views."""

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()
        self.instructor = self.create_instructor()
        self.client.login(username='STU001', password='TestPass123!')
        from apps.notifications.models import Notification, NotificationRecipient
        self.notif = Notification.objects.create(
            sender=self.instructor, title='إشعار اختبار', body='محتوى اختبار'
        )
        self.nr = NotificationRecipient.objects.create(
            notification=self.notif, user=self.user
        )

    def test_notification_list_get(self):
        """T30: Notification list returns 200."""
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)

    def test_notification_detail_get(self):
        """T31: Notification detail returns 200 and marks as read."""
        response = self.client.get(reverse('notifications:detail', args=[self.notif.pk]))
        self.assertEqual(response.status_code, 200)
        self.nr.refresh_from_db()
        self.assertTrue(self.nr.is_read)

    def test_mark_as_read_post(self):
        """T32: Mark notification as read via POST."""
        response = self.client.post(reverse('notifications:mark_read', args=[self.notif.pk]))
        self.assertEqual(response.status_code, 302)
        self.nr.refresh_from_db()
        self.assertTrue(self.nr.is_read)

    def test_mark_all_read_post(self):
        """T33: Mark all notifications as read."""
        response = self.client.post(reverse('notifications:mark_all_read'))
        self.assertEqual(response.status_code, 302)
        self.nr.refresh_from_db()
        self.assertTrue(self.nr.is_read)

    def test_delete_notification_post(self):
        """T34: Soft delete notification."""
        response = self.client.post(reverse('notifications:delete', args=[self.notif.pk]))
        self.assertEqual(response.status_code, 302)
        self.nr.refresh_from_db()
        self.assertTrue(self.nr.is_deleted)

    def test_unread_count_api(self):
        """T35: Unread count API returns JSON."""
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)


# ============================================================================
# 6. AI Features Models Tests (5 tests)
# ============================================================================

class AIConfigurationTest(TestCase, BaseTestMixin):
    """Test AIConfiguration model."""

    def test_singleton_creation(self):
        """T36: AIConfiguration is singleton (pk=1)."""
        from apps.ai_features.models import AIConfiguration
        config = AIConfiguration.get_config()
        self.assertEqual(config.pk, 1)

    def test_singleton_uniqueness(self):
        """T37: Only one AIConfiguration exists."""
        from apps.ai_features.models import AIConfiguration
        AIConfiguration.get_config()
        AIConfiguration(active_model='gemini-2.0-flash').save()
        self.assertEqual(AIConfiguration.objects.count(), 1)

    def test_default_values(self):
        """T38: AIConfiguration has correct defaults."""
        from apps.ai_features.models import AIConfiguration
        config = AIConfiguration.get_config()
        self.assertEqual(config.active_model, 'gemini-2.5-flash')
        self.assertEqual(config.chunk_size, 30000)
        self.assertTrue(config.is_service_enabled)

    def test_cache_invalidation(self):
        """T39: Cache invalidation on save."""
        from apps.ai_features.models import AIConfiguration
        config = AIConfiguration.get_config()
        cache.set('ai_configuration', config)
        config.active_model = 'gemini-2.0-flash'
        config.save()
        self.assertIsNone(cache.get('ai_configuration'))


class APIKeyModelTest(TestCase, BaseTestMixin):
    """Test APIKey model."""

    def test_key_encryption_decryption(self):
        """T40: API key encrypt/decrypt roundtrip."""
        from apps.ai_features.models import APIKey
        key = APIKey(label='Test Key', provider='gemini')
        raw = 'AIzaSyTestKeyValue123'
        key.set_key(raw)
        key.save()
        self.assertEqual(key.get_key(), raw)
        self.assertEqual(key.key_hint, 'e123')


# ============================================================================
# 7. URL Resolution Tests (7 tests)
# ============================================================================

class URLResolutionTest(TestCase):
    """Test URL patterns resolve correctly."""

    def test_login_url(self):
        """T41: Login URL resolves."""
        url = reverse('accounts:login')
        self.assertEqual(url, '/accounts/login/')

    def test_profile_url(self):
        """T42: Profile URL resolves."""
        url = reverse('accounts:profile')
        self.assertEqual(url, '/accounts/profile/')

    def test_change_password_url(self):
        """T43: Change password URL resolves."""
        url = reverse('accounts:change_password')
        self.assertEqual(url, '/accounts/profile/change-password/')

    def test_notification_list_url(self):
        """T44: Notification list URL resolves."""
        url = reverse('notifications:list')
        self.assertEqual(url, '/notifications/')

    def test_notification_detail_url(self):
        """T45: Notification detail URL resolves."""
        url = reverse('notifications:detail', args=[1])
        self.assertEqual(url, '/notifications/1/')

    def test_ai_usage_stats_url(self):
        """T46: AI usage stats URL resolves."""
        url = reverse('ai_features:usage_stats')
        self.assertEqual(url, '/ai/usage/')

    def test_instructor_dashboard_url(self):
        """T47: Instructor dashboard URL resolves."""
        url = reverse('instructor:dashboard')
        self.assertEqual(url, '/instructor/dashboard/')


# ============================================================================
# 8. Context Processors Tests (4 tests)
# ============================================================================

class ContextProcessorTest(TestCase, BaseTestMixin):
    """Test context processors."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.create_user()

    def test_site_settings(self):
        """T48: site_settings returns SITE_NAME."""
        from apps.core.context_processors import site_settings
        request = self.factory.get('/')
        ctx = site_settings(request)
        self.assertEqual(ctx['SITE_NAME'], 'S-ACM')

    def test_user_notifications_authenticated(self):
        """T49: user_notifications returns unread_count for authenticated user."""
        from apps.core.context_processors import user_notifications
        request = self.factory.get('/')
        request.user = self.user
        ctx = user_notifications(request)
        self.assertIn('unread_count', ctx)
        self.assertEqual(ctx['unread_count'], 0)

    def test_user_role_info_student(self):
        """T50: user_role_info returns is_student for student user."""
        from apps.core.context_processors import user_role_info
        request = self.factory.get('/')
        request.user = self.user
        request.menu_items = []
        request.user_permissions = set()
        ctx = user_role_info(request)
        self.assertTrue(ctx['is_student'])
        self.assertFalse(ctx['is_instructor'])

    def test_user_role_info_anonymous(self):
        """T51: user_role_info returns defaults for anonymous user."""
        from django.contrib.auth.models import AnonymousUser
        from apps.core.context_processors import user_role_info
        request = self.factory.get('/')
        request.user = AnonymousUser()
        ctx = user_role_info(request)
        self.assertFalse(ctx['is_student'])
        self.assertFalse(ctx['is_instructor'])
        self.assertFalse(ctx['is_admin'])


# ============================================================================
# 9. Security Settings Tests (3 tests)
# ============================================================================

class SecuritySettingsTest(TestCase):
    """Test security configurations."""

    def test_csrf_cookie_httponly(self):
        """T52: CSRF_COOKIE_HTTPONLY is True."""
        from django.conf import settings
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)

    def test_session_cookie_httponly(self):
        """T53: SESSION_COOKIE_HTTPONLY is True."""
        from django.conf import settings
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_secure_referrer_policy(self):
        """T54: SECURE_REFERRER_POLICY is set."""
        from django.conf import settings
        self.assertEqual(settings.SECURE_REFERRER_POLICY, 'strict-origin-when-cross-origin')


# ============================================================================
# 10. Template Tests (3 tests)
# ============================================================================

class TemplateExistenceTest(TestCase, BaseTestMixin):
    """Test that all required templates exist."""

    def setUp(self):
        self.client = Client()
        self.user = self.create_user(email='tmpl@test.com')
        self.client.login(username='STU001', password='TestPass123!')

    def test_profile_template_extends_dashboard(self):
        """T55: Profile template extends dashboard_base."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertContains(response, 'الملف الشخصي')
        self.assertContains(response, 'S-ACM')

    def test_change_password_template(self):
        """T56: Change password template renders correctly."""
        response = self.client.get(reverse('accounts:change_password'))
        self.assertContains(response, 'تغيير كلمة المرور')

    def test_notification_list_template(self):
        """T57: Notification list template renders correctly."""
        response = self.client.get(reverse('notifications:list'))
        self.assertContains(response, 'الإشعارات')
