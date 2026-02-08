"""
Views لتطبيق ai_features
S-ACM - Smart Academic Content Management System
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

# تصحيح الاستيراد: AIGeneratedQuestion بدلاً من AIQuestion
from .models import AISummary, AIGeneratedQuestion, AIChat, AIUsageLog
from .services import GeminiService
from apps.courses.models import LectureFile
from apps.accounts.views import StudentRequiredMixin


class AIRateLimitMixin:
    """Mixin للتحقق من حد الاستخدام"""
    
    def check_rate_limit(self, user):
        """التحقق من عدم تجاوز حد الاستخدام"""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        usage_count = AIUsageLog.objects.filter(
            user=user,
            request_time__gte=one_hour_ago
        ).count()
        
        limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return usage_count < limit
    
    def get_remaining_requests(self, user):
        """الحصول على عدد الطلبات المتبقية"""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        usage_count = AIUsageLog.objects.filter(
            user=user,
            request_time__gte=one_hour_ago
        ).count()
        
        limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return max(0, limit - usage_count)


class SummarizeView(LoginRequiredMixin, AIRateLimitMixin, View):
    """تلخيص ملف باستخدام الذكاء الاصطناعي"""
    template_name = 'ai_features/summarize.html'
    
    def get(self, request, file_id):
        file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
        
        # التحقق من وجود تلخيص سابق
        existing_summary = AISummary.objects.filter(
            file=file_obj,
            # user=request.user # اختياري: إذا أردت عرض أي ملخص للملف بغض النظر عن المستخدم
        ).first()
        
        remaining = self.get_remaining_requests(request.user)
        
        return render(request, self.template_name, {
            'file': file_obj,
            'existing_summary': existing_summary,
            'remaining_requests': remaining
        })
    
    def post(self, request, file_id):
        file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
        
        # التحقق من حد الاستخدام
        if not self.check_rate_limit(request.user):
            messages.error(request, 'لقد تجاوزت الحد المسموح من الطلبات. حاول بعد ساعة.')
            return redirect('ai_features:summarize', file_id=file_id)
        
        # استخراج النص من الملف
        try:
            gemini = GeminiService()
            text_content = gemini.extract_text_from_file(file_obj)
            
            if not text_content:
                messages.error(request, 'لم نتمكن من استخراج النص من هذا الملف.')
                return redirect('ai_features:summarize', file_id=file_id)
            
            # توليد التلخيص
            summary_text = gemini.generate_summary(text_content)
            
            # حفظ التلخيص
            summary, created = AISummary.objects.update_or_create(
                file=file_obj,
                defaults={
                    'user': request.user,
                    'summary_text': summary_text,
                    'word_count': len(summary_text.split()),
                    'language': 'ar',
                    'model_used': 'gemini-2.0-flash',
                    'is_cached': True
                }
            )
            
            # تسجيل الاستخدام
            AIUsageLog.objects.create(
                user=request.user,
                request_type='summary',
                file=file_obj,
                tokens_used=len(text_content.split()) + len(summary_text.split()),
                success=True
            )
            
            messages.success(request, 'تم إنشاء التلخيص بنجاح!')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء التلخيص: {str(e)}')
        
        return redirect('ai_features:summarize', file_id=file_id)


class GenerateQuestionsView(LoginRequiredMixin, AIRateLimitMixin, View):
    """توليد أسئلة من ملف باستخدام الذكاء الاصطناعي"""
    template_name = 'ai_features/questions.html'
    
    def get(self, request, file_id):
        file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
        
        # الأسئلة السابقة - تم تحديث الاستعلام للمودل الجديد
        existing_questions = AIGeneratedQuestion.objects.filter(
            file=file_obj,
            # user=request.user # يمكن إزالة هذا الشرط لعرض الأسئلة العامة للمقرر
        ).order_by('-generated_at')
        
        remaining = self.get_remaining_requests(request.user)
        
        return render(request, self.template_name, {
            'file': file_obj,
            'questions': existing_questions,
            'remaining_requests': remaining
        })
    
    def post(self, request, file_id):
        file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
        
        if not self.check_rate_limit(request.user):
            messages.error(request, 'لقد تجاوزت الحد المسموح من الطلبات. حاول بعد ساعة.')
            return redirect('ai_features:questions', file_id=file_id)
        
        question_type_req = request.POST.get('question_type', 'mixed')
        num_questions = int(request.POST.get('num_questions', 5))
        
        try:
            gemini = GeminiService()
            text_content = gemini.extract_text_from_file(file_obj)
            
            if not text_content:
                messages.error(request, 'لم نتمكن من استخراج النص من هذا الملف.')
                return redirect('ai_features:questions', file_id=file_id)
            
            # توليد الأسئلة (تعود كقائمة من القواميس)
            # يجب تحويل question_type_req إلى Enum داخل Service أو تمريره كنص كما هو مدعوم
            from .services import QuestionType
            q_type_enum = QuestionType.MIXED
            try:
                q_type_enum = QuestionType(question_type_req)
            except ValueError:
                pass

            questions_data = gemini.generate_questions(
                text_content,
                question_type=q_type_enum,
                num_questions=num_questions
            )
            
            # حفظ الأسئلة - تم التحديث للحفظ كسجلات متعددة
            if questions_data:
                for q in questions_data:
                    AIGeneratedQuestion.objects.create(
                        file=file_obj,
                        user=request.user,
                        question_text=q.get('question', 'سؤال بدون نص'),
                        question_type=q.get('type', 'short_answer'),
                        options=q.get('options'), # سيتم حفظه كـ JSON تلقائياً
                        correct_answer=q.get('answer', ''),
                        explanation=q.get('explanation', ''),
                        difficulty_level='medium',
                        is_cached=True
                    )
                
                AIUsageLog.objects.create(
                    user=request.user,
                    request_type='questions',
                    file=file_obj,
                    tokens_used=len(text_content.split()),
                    success=True
                )
                
                messages.success(request, f'تم توليد {len(questions_data)} سؤال بنجاح!')
            else:
                messages.warning(request, 'لم يتمكن الذكاء الاصطناعي من توليد أسئلة مفيدة من هذا النص.')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء توليد الأسئلة: {str(e)}')
        
        return redirect('ai_features:questions', file_id=file_id)


class AskDocumentView(LoginRequiredMixin, AIRateLimitMixin, View):
    """اسأل المستند - طرح أسئلة على محتوى الملف"""
    template_name = 'ai_features/ask_document.html'
    
    def get(self, request, file_id):
        file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
        
        chat_history = AIChat.objects.filter(
            file=file_obj,
            user=request.user
        ).order_by('created_at')
        
        remaining = self.get_remaining_requests(request.user)
        
        return render(request, self.template_name, {
            'file': file_obj,
            'chat_history': chat_history,
            'remaining_requests': remaining
        })
    
    def post(self, request, file_id):
        file_obj = get_object_or_404(LectureFile, pk=file_id, is_deleted=False)
        
        if not self.check_rate_limit(request.user):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'لقد تجاوزت الحد المسموح من الطلبات. حاول بعد ساعة.'
                })
            messages.error(request, 'لقد تجاوزت الحد المسموح من الطلبات. حاول بعد ساعة.')
            return redirect('ai_features:ask_document', file_id=file_id)
        
        question = request.POST.get('question', '').strip()
        
        if not question:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'يرجى إدخال سؤال.'})
            messages.error(request, 'يرجى إدخال سؤال.')
            return redirect('ai_features:ask_document', file_id=file_id)
        
        try:
            gemini = GeminiService()
            text_content = gemini.extract_text_from_file(file_obj)
            
            if not text_content:
                error_msg = 'لم نتمكن من استخراج النص من هذا الملف.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('ai_features:ask_document', file_id=file_id)
            
            answer = gemini.ask_document(text_content, question)
            
            chat = AIChat.objects.create(
                file=file_obj,
                user=request.user,
                question=question,
                answer=answer
            )
            
            AIUsageLog.objects.create(
                user=request.user,
                request_type='chat',
                file=file_obj,
                tokens_used=len(question.split()) + len(answer.split()),
                success=True
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'question': question,
                    'answer': answer,
                    'created_at': chat.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            messages.success(request, 'تم الحصول على الإجابة!')
            
        except Exception as e:
            error_msg = f'حدث خطأ: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
        
        return redirect('ai_features:ask_document', file_id=file_id)


class AIUsageStatsView(LoginRequiredMixin, View):
    """إحصائيات استخدام الذكاء الاصطناعي"""
    template_name = 'ai_features/usage_stats.html'
    
    def get(self, request):
        user = request.user
        
        one_hour_ago = timezone.now() - timedelta(hours=1)
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stats = {
            'hourly_usage': AIUsageLog.objects.filter(
                user=user,
                request_time__gte=one_hour_ago
            ).count(),
            'daily_usage': AIUsageLog.objects.filter(
                user=user,
                request_time__gte=today
            ).count(),
            'total_summaries': AISummary.objects.filter(user=user).count(),
            # تحديث: حساب الأسئلة من الجدول الجديد
            'total_questions': AIGeneratedQuestion.objects.filter(user=user).count(),
            'total_chats': AIChat.objects.filter(user=user).count(),
            'rate_limit': getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        }
        
        recent_usage = AIUsageLog.objects.filter(user=user).order_by('-request_time')[:10]
        
        return render(request, self.template_name, {
            'stats': stats,
            'recent_usage': recent_usage
        })


class ClearChatHistoryView(LoginRequiredMixin, View):
    """مسح سجل المحادثة"""
    
    def post(self, request, file_id):
        AIChat.objects.filter(
            file_id=file_id,
            user=request.user
        ).delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'تم مسح سجل المحادثة.')
        return redirect('ai_features:ask_document', file_id=file_id)