"""
سكريبت لتنظيف البيانات القديمة قبل تطبيق migration الجديدة
"""
import os
import sys
import django

# إعداد Django
sys.path.insert(0, 'e:/ScamV4')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# حذف البيانات القديمة
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DELETE FROM role_permissions")
    cursor.execute("DELETE FROM permissions")
    # حذف الأدوار القديمة (سنستبدلها بالجديدة)
    cursor.execute("DELETE FROM roles")
    print("✅ تم حذف البيانات القديمة بنجاح!")

print("الآن قم بتشغيل: python manage.py migrate")
