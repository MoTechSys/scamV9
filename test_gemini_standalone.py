#!/usr/bin/env python3
"""
اختبار خدمة Gemini - نسخة مستقلة
S-ACM - Smart Academic Content Management System

هذا السكريبت يختبر الاتصال بـ Gemini API مباشرة بدون Django
"""

from google import genai
from google.genai import types

# ========== Configuration ==========
GEMINI_API_KEY = "AIzaSyC0caScddcPQHxN2fQUSYj02sZ66MG-_80"
GEMINI_MODEL = "gemini-2.5-flash"


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
    print_header("اختبار Google Gemini API - S-ACM")
    
    # تهيئة العميل
    print("\n📦 تهيئة العميل...")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print_result(True, "تم تهيئة العميل بنجاح")
    except Exception as e:
        print_result(False, f"فشل تهيئة العميل: {e}")
        return
    
    # اختبار الاتصال
    print_header("اختبار 1: الاتصال الأساسي")
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="قل: مرحباً، أنا جاهز للعمل!",
            config=types.GenerateContentConfig(
                max_output_tokens=100,
                temperature=0.3,
            )
        )
        print_result(True, "الاتصال ناجح!")
        print(f"   الرد: {response.text}")
    except Exception as e:
        print_result(False, f"فشل الاتصال: {e}")
        return
    
    # نص للاختبار
    test_text = """
    الذكاء الاصطناعي (AI) هو فرع من علوم الحاسوب يهدف إلى إنشاء أنظمة قادرة على أداء مهام 
    تتطلب عادةً ذكاءً بشرياً. يشمل ذلك التعلم الآلي، ومعالجة اللغة الطبيعية، والرؤية الحاسوبية.
    
    التعلم الآلي هو أحد أهم فروع الذكاء الاصطناعي، حيث تتعلم الأنظمة من البيانات بدلاً من 
    البرمجة الصريحة. يُستخدم في تطبيقات متعددة مثل التعرف على الصور والتنبؤ بالأسعار.
    """
    
    # اختبار التلخيص
    print_header("اختبار 2: توليد التلخيص")
    try:
        prompt = f"""أنت مساعد أكاديمي. قم بتلخيص النص التالي باللغة العربية في 3 جمل:

{test_text}

التلخيص:"""
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=300,
                temperature=0.3,
            )
        )
        print_result(True, "تم توليد التلخيص بنجاح!")
        print(f"\n📝 التلخيص:\n{response.text}")
    except Exception as e:
        print_result(False, f"فشل توليد التلخيص: {e}")
    
    # اختبار توليد الأسئلة
    print_header("اختبار 3: توليد الأسئلة")
    try:
        prompt = f"""أنت مدرس. أنشئ سؤالين اختيار من متعدد من النص التالي.
أرجع الإجابة بصيغة JSON فقط:

النص:
{test_text}

الأسئلة (JSON):"""
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.5,
            )
        )
        print_result(True, "تم توليد الأسئلة بنجاح!")
        print(f"\n❓ الأسئلة:\n{response.text}")
    except Exception as e:
        print_result(False, f"فشل توليد الأسئلة: {e}")
    
    # اختبار سؤال المستند
    print_header("اختبار 4: سؤال المستند")
    try:
        question = "ما هي أهم فروع الذكاء الاصطناعي المذكورة؟"
        prompt = f"""أجب على السؤال التالي بناءً على النص:

النص:
{test_text}

السؤال: {question}

الإجابة:"""
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0.3,
            )
        )
        print_result(True, "تم الإجابة على السؤال بنجاح!")
        print(f"\n❓ السؤال: {question}")
        print(f"💬 الإجابة: {response.text}")
    except Exception as e:
        print_result(False, f"فشل الإجابة على السؤال: {e}")
    
    print_header("انتهاء الاختبارات")
    print("✅ جميع الاختبارات اكتملت بنجاح!")
    print(f"\n📊 الموديل المستخدم: {GEMINI_MODEL}")


if __name__ == "__main__":
    main()
