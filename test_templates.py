import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from apps.accounts.models import User, Role
from django.urls import resolve

# Test utilities
factory = RequestFactory()

print("="*50)
print("S-ACM Project Analysis")
print("="*50)

# Test 1: Check database
print("\n1. Database Status:")
try:
    roles_count = Role.objects.count()
    users_count = User.objects.count()
    print(f"   ✅ Roles: {roles_count}")
    print(f"   ✅ Users: {users_count}")
    admin = User.objects.filter(academic_id='admin').first()
    if admin:
        print(f"   ✅ Admin user exists: {admin.full_name}")
    else:
        print("   ❌ Admin user not found!")
except Exception as e:
    print(f"   ❌ Database error: {str(e)}")

# Test 2: URLs configuration
print("\n2. URLs Configuration:")
try:
    from django.urls import reverse
    urls_to_test = [
        ('accounts:login', 'Login'),
        ('accounts:admin_dashboard', 'Dashboard'),
        ('accounts:admin_roles', 'Roles'),
        ('accounts:admin_permissions', 'Permissions'),
        ('accounts:admin_user_list', 'Users List'),
    ]
    for url_name, label in urls_to_test:
        try:
            url = reverse(url_name)
            print(f"   ✅ {label}: {url}")
        except:
            print(f"   ❌ {label}: URL not found")
except Exception as e:
    print(f"   ❌ URLs error: {str(e)}")

# Test 3: Templates exist
print("\n3. Templates:")
import os
templates = [
    'layouts/dashboard_base.html',
    'components/sidebar.html',
    'admin_panel/dashboard.html',
    'admin_panel/roles/list.html',
    'admin_panel/permissions/list.html',
]
for tmpl in templates:
    path = os.path.join('e:/ScamV4/templates', tmpl)
    if os.path.exists(path):
        print(f"   ✅ {tmpl}")
    else:
        print(f"   ❌ {tmpl} - Missing!")

# Test 4: Static files
print("\n4. Static Files:")
static_files = [
    'css/sidebar.css',
    'js/sidebar.js',
]
for sf in static_files:
    path = os.path.join('e:/ScamV4/static', sf)
    if os.path.exists(path):
        print(f"   ✅ {sf}")
    else:
        print(f"   ❌ {sf} - Missing!")

# Test 5: Middleware and Settings
print("\n5. Configuration:")
from django.conf import settings
middleware_check = 'apps.core.middleware.PermissionMiddleware' in settings.MIDDLEWARE
context_check = any('user_role_info' in str(cp) for cp in settings.TEMPLATES[0]['OPTIONS']['context_processors'])
print(f"   {'✅' if middleware_check else '❌'} PermissionMiddleware")
print(f"   {'✅' if context_check else '❌'} user_role_info context processor")

# Test 6: Models
print("\n6. Models:")
try:
    from apps.accounts.models import Permission
    perm_count = Permission.objects.count()
    print(f"   ✅ Permissions: {perm_count}")
except Exception as e:
    print(f"   ❌ Permissions model error: {str(e)}")

print("\n" + "="*50)
print("Analysis Complete!")
print("="*50)
