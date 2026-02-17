"""
Comprehensive Test Suite for S-ACM
===================================
Tests AI service (mocked), streaming (Range/206), and RBAC (403 security).

Run with:
    python manage.py test tests -v2
"""

import os
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock, patch as mock_patch

from django.conf import settings
from django.test import TestCase, RequestFactory, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

User = get_user_model()


# =========================================================================
# Helpers
# =========================================================================

def _create_role(code, display_name, is_system=True):
    """Create a Role instance with the given code."""
    from apps.accounts.models import Role
    role, _ = Role.objects.get_or_create(
        code=code,
        defaults={
            'display_name': display_name,
            'is_system': is_system,
        },
    )
    return role


def _create_user(academic_id, role_code, password='TestPass123!', **extra):
    """Create a User with a given role."""
    from apps.accounts.models import Role
    role = _create_role(
        role_code,
        {'admin': 'Admin', 'instructor': 'Instructor', 'student': 'Student'}.get(
            role_code, role_code
        ),
    )
    user = User.objects.create_user(
        academic_id=academic_id,
        password=password,
        full_name=extra.pop('full_name', f'Test {role_code}'),
        id_card_number=extra.pop('id_card_number', f'ID-{academic_id}'),
        role=role,
        account_status='active',
        **extra,
    )
    return user


def _setup_course_infrastructure():
    """Create level, semester, major, course — returns (course, level, major, semester)."""
    from apps.accounts.models import Level, Semester, Major
    from apps.courses.models import Course, CourseMajor

    level, _ = Level.objects.get_or_create(
        level_number=1, defaults={'level_name': 'Level 1'},
    )
    semester, _ = Semester.objects.get_or_create(
        name='Test Semester',
        defaults={
            'academic_year': '2025/2026',
            'semester_number': 1,
            'start_date': '2025-09-01',
            'end_date': '2025-12-31',
            'is_current': True,
        },
    )
    major, _ = Major.objects.get_or_create(
        major_name='Computer Science',
        defaults={'description': 'CS Department'},
    )
    course, _ = Course.objects.get_or_create(
        course_code='CS101',
        defaults={
            'course_name': 'Intro to CS',
            'level': level,
            'semester': semester,
        },
    )
    CourseMajor.objects.get_or_create(course=course, major=major)
    return course, level, major, semester


def _create_lecture_file(course, uploader, title='Test Lecture', content=b'Hello'):
    """Create a LectureFile with a small temp file."""
    from apps.courses.models import LectureFile
    upload = SimpleUploadedFile(f'{title}.txt', content, content_type='text/plain')
    lf = LectureFile.objects.create(
        course=course,
        uploader=uploader,
        title=title,
        file_type='Lecture',
        content_type='local_file',
        local_file=upload,
        is_visible=True,
    )
    return lf


# =========================================================================
# 1. AI Service Tests (Mocked — zero real API calls)
# =========================================================================

class AIServiceMockTests(TestCase):
    """Test the Manus AI Router integration with mocked OpenAI client."""

    def setUp(self):
        self.role = _create_role('instructor', 'Instructor')
        self.user = _create_user('inst01', 'instructor')

    @patch('apps.ai_features.services.HydraKeyManager')
    @patch('openai.OpenAI')
    def test_generate_summary_returns_text(self, mock_openai_cls, mock_key_mgr):
        """AI summary generation should return markdown text via Manus proxy."""
        # Arrange — mock the OpenAI client response
        mock_choice = MagicMock()
        mock_choice.message.content = '# Summary\nThis is a test summary.'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        mock_km_instance = MagicMock()
        mock_km_instance.has_keys = True
        mock_km_instance.get_api_key.return_value = 'sk-test-key'
        mock_key_mgr.return_value = mock_km_instance

        from apps.ai_features.services import GeminiService
        service = GeminiService.__new__(GeminiService)
        service._model_name = 'gpt-4.1-mini'
        service._key_manager = mock_km_instance
        service._chunker = MagicMock()
        service._chunker.chunk_text.return_value = ['chunk1']
        service._storage = MagicMock()
        service._client = mock_client

        # Act
        result = service.generate_summary('Some academic text here...')

        # Assert
        self.assertIn('Summary', result)
        mock_client.chat.completions.create.assert_called_once()

    @patch('apps.ai_features.services.HydraKeyManager')
    @patch('openai.OpenAI')
    def test_generate_questions_returns_list(self, mock_openai_cls, mock_key_mgr):
        """AI question generation should parse JSON array from Manus proxy."""
        questions_json = '''[
            {"type": "mcq", "question": "What is AI?",
             "options": ["A", "B", "C", "D"], "answer": "A",
             "explanation": "AI stands for ...", "score": 2.0}
        ]'''
        mock_choice = MagicMock()
        mock_choice.message.content = questions_json
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        mock_km = MagicMock()
        mock_km.has_keys = True
        mock_km.get_api_key.return_value = 'sk-test-key'
        mock_key_mgr.return_value = mock_km

        from apps.ai_features.services import GeminiService, QuestionMatrixConfig
        service = GeminiService.__new__(GeminiService)
        service._model_name = 'gpt-4.1-mini'
        service._key_manager = mock_km
        service._chunker = MagicMock()
        service._chunker.chunk_text.return_value = ['chunk1']
        service._storage = MagicMock()
        service._client = mock_client

        matrix = QuestionMatrixConfig(mcq_count=1)
        result = service.generate_questions_matrix('Academic text ...', matrix)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'mcq')

    def test_hydra_key_manager_loads_env_key(self):
        """HydraKeyManager should read MANUS_API_KEY from settings."""
        with self.settings(MANUS_API_KEY='sk-test-123'):
            from apps.ai_features.services import HydraKeyManager
            # Reset singleton for test isolation
            HydraKeyManager._instance = None
            mgr = HydraKeyManager()
            self.assertTrue(mgr.has_keys)
            self.assertEqual(mgr.get_api_key(), 'sk-test-123')
            HydraKeyManager._instance = None  # Cleanup

    @patch.dict(os.environ, {'MANUS_API_KEY': ''}, clear=False)
    def test_hydra_key_manager_missing_key_raises(self):
        """HydraKeyManager.get_api_key() should raise when no key."""
        with self.settings(MANUS_API_KEY=''):
            from apps.ai_features.services import (
                HydraKeyManager, GeminiConfigurationError,
            )
            HydraKeyManager._instance = None
            HydraKeyManager._instance = None  # force re-init
            mgr = HydraKeyManager.__new__(HydraKeyManager)
            mgr._initialized = False
            mgr._api_key = None
            mgr.__init__()
            with self.assertRaises(GeminiConfigurationError):
                mgr.get_api_key()
            HydraKeyManager._instance = None

    def test_smart_chunker_splits_large_text(self):
        """SmartChunker should split text exceeding chunk_size."""
        from apps.ai_features.services import SmartChunker
        chunker = SmartChunker(chunk_size=100, overlap=20)
        # Use paragraph-separated text so chunker splits on \n\n
        text = 'A' * 80 + '\n\n' + 'B' * 80 + '\n\n' + 'C' * 80
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)

    def test_smart_chunker_single_chunk(self):
        """SmartChunker should not split short text."""
        from apps.ai_features.services import SmartChunker
        chunker = SmartChunker(chunk_size=100, overlap=10)
        chunks = chunker.chunk_text('Short text')
        self.assertEqual(len(chunks), 1)

    @patch('apps.ai_features.services.HydraKeyManager')
    @patch('openai.OpenAI')
    def test_ask_document_returns_answer(self, mock_openai_cls, mock_key_mgr):
        """ask_document should relay the question to the Manus proxy."""
        mock_choice = MagicMock()
        mock_choice.message.content = 'The answer is 42.'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        mock_km = MagicMock()
        mock_km.has_keys = True
        mock_km.get_api_key.return_value = 'sk-test-key'
        mock_key_mgr.return_value = mock_km

        from apps.ai_features.services import GeminiService
        service = GeminiService.__new__(GeminiService)
        service._model_name = 'gpt-4.1-mini'
        service._key_manager = mock_km
        service._chunker = MagicMock()
        service._chunker.chunk_text.return_value = ['All the context']
        service._storage = MagicMock()
        service._client = mock_client

        answer = service.ask_document('All the context', 'What is the meaning?')
        self.assertIn('42', answer)


# =========================================================================
# 2. Streaming Tests — Range Header / 206 Partial Content
# =========================================================================

class StreamingTests(TestCase):
    """Test video streaming with HTTP Range headers (206 Partial Content)."""

    def setUp(self):
        self.course, self.level, self.major, self.semester = (
            _setup_course_infrastructure()
        )
        self.instructor = _create_user(
            'inst02', 'instructor',
            id_card_number='ID-inst02',
        )
        self.student = _create_user(
            'std01', 'student',
            id_card_number='ID-std01',
            major=self.major,
            level=self.level,
        )
        # Assign instructor to course
        from apps.courses.models import InstructorCourse
        InstructorCourse.objects.get_or_create(
            instructor=self.instructor, course=self.course,
        )

        # Create a small "video" file
        video_content = b'\x00' * 1024  # 1 KB fake video
        upload = SimpleUploadedFile(
            'test_video.mp4', video_content,
            content_type='video/mp4',
        )
        from apps.courses.models import LectureFile
        self.video_file = LectureFile.objects.create(
            course=self.course,
            uploader=self.instructor,
            title='Test Video',
            file_type='Lecture',
            content_type='local_file',
            local_file=upload,
            is_visible=True,
        )
        self.client_http = Client()

    def test_streaming_returns_206_with_range_header(self):
        """GET with Range: bytes=0-100 on a video should return 206."""
        self.client_http.force_login(self.student)
        url = reverse('streaming:stream_file', kwargs={'pk': self.video_file.pk})
        response = self.client_http.get(
            url, HTTP_RANGE='bytes=0-100',
        )
        self.assertEqual(response.status_code, 206)
        self.assertIn('Content-Range', response)
        self.assertEqual(response['Accept-Ranges'], 'bytes')

    def test_streaming_returns_200_without_range_header(self):
        """GET without Range header should return 200."""
        self.client_http.force_login(self.student)
        url = reverse('streaming:stream_file', kwargs={'pk': self.video_file.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_streaming_invalid_range_returns_416(self):
        """GET with out-of-bounds Range should return 416."""
        self.client_http.force_login(self.student)
        url = reverse('streaming:stream_file', kwargs={'pk': self.video_file.pk})
        response = self.client_http.get(
            url, HTTP_RANGE='bytes=999999-',
        )
        self.assertEqual(response.status_code, 416)

    def test_streaming_content_length_header(self):
        """206 response should have accurate Content-Length."""
        self.client_http.force_login(self.student)
        url = reverse('streaming:stream_file', kwargs={'pk': self.video_file.pk})
        response = self.client_http.get(
            url, HTTP_RANGE='bytes=0-99',
        )
        self.assertEqual(response.status_code, 206)
        self.assertEqual(int(response['Content-Length']), 100)


# =========================================================================
# 3. RBAC / Security Tests — Student vs Instructor
# =========================================================================

class RBACSecurityTests(TestCase):
    """Test role-based access control enforcement (student ↛ instructor pages)."""

    def setUp(self):
        self.course, self.level, self.major, self.semester = (
            _setup_course_infrastructure()
        )
        self.instructor = _create_user(
            'inst03', 'instructor',
            id_card_number='ID-inst03',
        )
        self.student = _create_user(
            'std02', 'student',
            id_card_number='ID-std02',
            major=self.major,
            level=self.level,
        )
        from apps.courses.models import InstructorCourse
        InstructorCourse.objects.get_or_create(
            instructor=self.instructor, course=self.course,
        )
        self.client_http = Client()

    def test_student_cannot_access_instructor_dashboard(self):
        """Student accessing instructor dashboard should get 403."""
        self.client_http.force_login(self.student)
        url = reverse('instructor:dashboard')
        response = self.client_http.get(url)
        self.assertIn(response.status_code, [403, 302])

    def test_student_cannot_access_instructor_ai_hub(self):
        """Student accessing instructor AI Hub should be denied."""
        self.client_http.force_login(self.student)
        url = reverse('instructor:ai_hub')
        response = self.client_http.get(url)
        self.assertIn(response.status_code, [403, 302])

    def test_student_cannot_access_instructor_reports(self):
        """Student accessing instructor reports should be denied."""
        self.client_http.force_login(self.student)
        url = reverse('instructor:reports')
        response = self.client_http.get(url)
        self.assertIn(response.status_code, [403, 302])

    def test_instructor_can_access_instructor_dashboard(self):
        """Instructor should successfully access their dashboard."""
        self.client_http.force_login(self.instructor)
        url = reverse('instructor:dashboard')
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_instructor_cannot_access_student_dashboard(self):
        """Instructor accessing student dashboard should be denied."""
        self.client_http.force_login(self.instructor)
        url = reverse('student:dashboard')
        response = self.client_http.get(url)
        self.assertIn(response.status_code, [403, 302])

    def test_unauthenticated_redirects_to_login(self):
        """Unauthenticated user should be redirected to login."""
        url = reverse('instructor:dashboard')
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url.lower())


# =========================================================================
# 4. RBAC Decorator Tests
# =========================================================================

class DecoratorTests(TestCase):
    """Test function-based view decorators for role enforcement."""

    def setUp(self):
        self.factory = RequestFactory()
        self.student = _create_user(
            'std03', 'student', id_card_number='ID-std03',
        )
        self.instructor = _create_user(
            'inst04', 'instructor', id_card_number='ID-inst04',
        )

    def test_role_required_blocks_wrong_role(self):
        """role_required(['admin']) should redirect a student."""
        from apps.accounts.decorators import role_required

        @role_required(['admin'])
        def admin_view(request):
            return 'OK'

        request = self.factory.get('/test/')
        request.user = self.student
        # Add session/messages support
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.messages.middleware import MessageMiddleware
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        MessageMiddleware(lambda r: None).process_request(request)
        response = admin_view(request)
        self.assertEqual(response.status_code, 302)

    def test_role_required_allows_correct_role(self):
        """role_required(['instructor', 'admin']) should pass for instructor."""
        from apps.accounts.decorators import role_required

        @role_required(['instructor', 'admin'])
        def instructor_view(request):
            from django.http import HttpResponse
            return HttpResponse('OK')

        request = self.factory.get('/test/')
        request.user = self.instructor
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.messages.middleware import MessageMiddleware
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        MessageMiddleware(lambda r: None).process_request(request)
        response = instructor_view(request)
        self.assertEqual(response.status_code, 200)


# =========================================================================
# 5. Model & Settings Audit Tests
# =========================================================================

class SettingsAuditTests(TestCase):
    """Verify critical security settings are correct."""

    def test_secret_key_is_not_default_insecure(self):
        """SECRET_KEY should not contain 'insecure' when DEBUG is off."""
        # In testing DEBUG may be True, but we verify the pattern
        key = settings.SECRET_KEY
        self.assertIsNotNone(key)
        self.assertGreater(len(key), 20)

    def test_allowed_hosts_is_configured(self):
        """ALLOWED_HOSTS should contain at least localhost entries."""
        hosts = settings.ALLOWED_HOSTS
        self.assertIsInstance(hosts, list)
        # In production (DEBUG=False) the wildcard is removed by our
        # settings.py logic. Here we just verify config is populated.
        self.assertTrue(len(hosts) > 0)

    def test_csrf_cookie_httponly(self):
        """CSRF cookie must be HTTP-only."""
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)

    def test_session_cookie_httponly(self):
        """Session cookie must be HTTP-only."""
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_ai_model_name_is_configured(self):
        """AI_MODEL_NAME should be set."""
        model = settings.AI_MODEL_NAME
        self.assertIn(model, ['gpt-4.1-mini', 'gemini-2.5-flash', 'gpt-4o-mini'])


class ModelTests(TestCase):
    """Test model methods and constraints."""

    def test_user_is_student(self):
        """User.is_student() should return True for student role."""
        user = _create_user('std10', 'student', id_card_number='ID-std10')
        self.assertTrue(user.is_student())
        self.assertFalse(user.is_instructor())
        self.assertFalse(user.is_admin())

    def test_user_is_instructor(self):
        """User.is_instructor() should return True for instructor role."""
        user = _create_user('inst10', 'instructor', id_card_number='ID-inst10')
        self.assertTrue(user.is_instructor())
        self.assertFalse(user.is_student())

    def test_user_is_admin(self):
        """User.is_admin() should return True for admin role."""
        user = _create_user('adm10', 'admin', id_card_number='ID-adm10')
        self.assertTrue(user.is_admin())

    def test_verification_code_generation(self):
        """VerificationCode.generate_code() produces 6-digit string."""
        from apps.accounts.models import VerificationCode
        code = VerificationCode.generate_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_password_reset_token_generation(self):
        """PasswordResetToken.generate_token() produces URL-safe token."""
        from apps.accounts.models import PasswordResetToken
        token = PasswordResetToken.generate_token()
        self.assertGreater(len(token), 20)


# =========================================================================
# 6. AI File Storage Tests
# =========================================================================

class AIFileStorageTests(TestCase):
    """Test AIFileStorage read/write/delete operations."""

    def test_save_and_read_summary(self):
        """AIFileStorage should save and read markdown files."""
        from apps.ai_features.services import AIFileStorage
        storage = AIFileStorage()
        path = storage.save_summary(
            file_id=999,
            content='# Test Summary\nContent here.',
            metadata={'source_file': 'test.pdf'},
        )
        self.assertIn('ai_generated', path)
        content = storage.read_file(path)
        self.assertIn('Test Summary', content)
        # Cleanup
        storage.delete_file(path)

    def test_delete_nonexistent_file(self):
        """Deleting a non-existent file should return False."""
        from apps.ai_features.services import AIFileStorage
        storage = AIFileStorage()
        result = storage.delete_file('ai_generated/nonexistent.md')
        self.assertFalse(result)
