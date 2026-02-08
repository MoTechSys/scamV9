#!/usr/bin/env python3
"""
اختبار خدمة Gemini
S-ACM - Smart Academic Content Management System

هذا السكريبت يختبر:
1. الاتصال بـ Gemini API
2. توليد التلخيص
3. توليد الأسئلة
4. سؤال المستند
"""

import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, '/home/ubuntu/ProjectSCAM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# تهيئة Django
import django
django.setup()

from apps.ai_features.services import GeminiService, QuestionType

def print_header(title: str):
    """طباعة عنوان."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(success: bool, message: str):
    """طباعة النتيجة."""
    status = "✅" if success else "❌"
    print(f"{status} {message}")

def main():
    print_header("اختبار خدمة Gemini - S-ACM")
    
    # إنشاء الخدمة
    print("\n📦 تهيئة الخدمة...")
    try:
        service = GeminiService()
        print_result(True, "تم تهيئة الخدمة بنجاح")
    except Exception as e:
        print_result(False, f"فشل تهيئة الخدمة: {e}")
        return
    
    # اختبار الاتصال
    print_header("اختبار 1: الاتصال بـ Gemini API")
    result = service.test_connection()
    if result.success:
        print_result(True, f"الاتصال ناجح!")
        print(f"   الرد: {result.data}")
    else:
        print_result(False, f"فشل الاتصال: {result.error}")
        return
    
    # نص للاختبار
    test_text = """
    الذكاء الاصطناعي (AI) هو فرع من علوم الحاسوب يهدف إلى إنشاء أنظمة قادرة على أداء مهام 
    تتطلب عادةً ذكاءً بشرياً. يشمل ذلك التعلم الآلي، ومعالجة اللغة الطبيعية، والرؤية الحاسوبية.
    
    التعلم الآلي هو أحد أهم فروع الذكاء الاصطناعي، حيث تتعلم الأنظمة من البيانات بدلاً من 
    البرمجة الصريحة. يُستخدم في تطبيقات متعددة مثل التعرف على الصور والتنبؤ بالأسعار.
    
    معالجة اللغة الطبيعية (NLP) تمكّن الحواسيب من فهم وتوليد اللغة البشرية. تُستخدم في 
    المساعدات الصوتية والترجمة الآلية وتحليل المشاعر.
    """
    
    # اختبار التلخيص
    print_header("اختبار 2: توليد التلخيص")
    try:
        summary = service.generate_summary(test_text, max_length=200)
        print_result(True, "تم توليد التلخيص بنجاح!")
        print(f"\n📝 التلخيص:\n{summary}")
    except Exception as e:
        print_result(False, f"فشل توليد التلخيص: {e}")
    
    # اختبار توليد الأسئلة
    print_header("اختبار 3: توليد الأسئلة")
    try:
        questions = service.generate_questions(test_text, QuestionType.MCQ, 3)
        print_result(True, f"تم توليد {len(questions)} سؤال بنجاح!")
        
        for i, q in enumerate(questions, 1):
            print(f"\n❓ السؤال {i}: {q.get('question', 'N/A')}")
            if q.get('options'):
                for j, opt in enumerate(q['options'], 1):
                    print(f"   {j}. {opt}")
            print(f"   ✓ الإجابة: {q.get('answer', 'N/A')}")
    except Exception as e:
        print_result(False, f"فشل توليد الأسئلة: {e}")
    
    # اختبار سؤال المستند
    print_header("اختبار 4: سؤال المستند")
    try:
        question = "ما هي أهم فروع الذكاء الاصطناعي المذكورة في النص؟"
        answer = service.ask_document(test_text, question)
        print_result(True, "تم الإجابة على السؤال بنجاح!")
        print(f"\n❓ السؤال: {question}")
        print(f"💬 الإجابة: {answer}")
    except Exception as e:
        print_result(False, f"فشل الإجابة على السؤال: {e}")
    
    print_header("انتهاء الاختبارات")
    print("✅ جميع الاختبارات اكتملت!")

if __name__ == "__main__":
    main()
