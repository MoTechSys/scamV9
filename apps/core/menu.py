"""
نظام القائمة الديناميكية المبني على الصلاحيات
S-ACM - Smart Academic Content Management System

هذا الملف يعرف عناصر القائمة الجانبية (Sidebar) بناءً على الصلاحيات.
القائمة تتشكل ديناميكياً حسب صلاحيات المستخدم - لا حاجة لتحديد الدور.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from django.urls import reverse, NoReverseMatch


@dataclass
class MenuItem:
    """
    عنصر قائمة واحد
    
    Attributes:
        code: معرف فريد للعنصر (مثل: 'dashboard', 'manage_files')
        icon: أيقونة Bootstrap Icons (مثل: 'bi-house', 'bi-folder')
        label: النص المعروض (بالعربية)
        url_name: اسم الـ URL في urls.py (مثل: 'courses:instructor_files')
        required_perm: كود الصلاحية المطلوبة (None = متاح للجميع)
        children: قائمة عناصر فرعية
        order: ترتيب العرض
        badge: نص الـ badge (مثل: 'جديد')
        badge_class: CSS class للـ badge
    """
    code: str
    icon: str
    label: str
    url_name: str = ''
    required_perm: Optional[str] = None
    children: List['MenuItem'] = field(default_factory=list)
    order: int = 0
    badge: str = ''
    badge_class: str = 'bg-primary'
    
    def get_url(self) -> str:
        """الحصول على URL العنصر"""
        if not self.url_name:
            return '#'
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return '#'
    
    def has_children(self) -> bool:
        """هل للعنصر عناصر فرعية؟"""
        return len(self.children) > 0
    
    def get_visible_children(self, user_permissions: set) -> List['MenuItem']:
        """الحصول على العناصر الفرعية المرئية للمستخدم"""
        return [
            child for child in self.children
            if child.required_perm is None or child.required_perm in user_permissions
        ]


# ========== تعريف عناصر القائمة ==========

MENU_ITEMS = [
    # === لوحة التحكم (للجميع) ===
    MenuItem(
        code='dashboard',
        icon='bi-house-door',
        label='لوحة التحكم',
        url_name='core:dashboard_redirect',
        required_perm=None,
        order=0,
    ),
    
    # === المقررات ===
    MenuItem(
        code='courses',
        icon='bi-book',
        label='المقررات',
        url_name='courses:student_courses',
        required_perm='view_courses',
        order=10,
    ),
    
    # === الملفات والمحتوى (للمدرسين) ===
    MenuItem(
        code='manage_files',
        icon='bi-folder-plus',
        label='إدارة الملفات',
        url_name='courses:instructor_courses',
        required_perm='upload_files',
        order=20,
    ),
    
    # === الإشعارات ===
    MenuItem(
        code='notifications',
        icon='bi-bell',
        label='الإشعارات',
        url_name='notifications:list',
        required_perm=None,
        order=30,
    ),
    
    # === الذكاء الاصطناعي ===
    MenuItem(
        code='ai_features',
        icon='bi-robot',
        label='الذكاء الاصطناعي',
        url_name='ai_features:student_tools',
        required_perm='use_ai_features',
        order=40,
    ),
    
    # ========== قسم الإدارة (للأدمن والمدرسين) ==========
    MenuItem(
        code='admin_separator',
        icon='',
        label='--- الإدارة ---',
        url_name='',
        required_perm='view_users',
        order=100,
    ),
    
    # === إدارة المستخدمين ===
    MenuItem(
        code='users_management',
        icon='bi-people',
        label='إدارة المستخدمين',
        required_perm='view_users',
        order=110,
        children=[
            MenuItem(
                code='users_list',
                icon='bi-person-lines-fill',
                label='قائمة المستخدمين',
                url_name='accounts:admin_users',
                required_perm='view_users',
                order=1,
            ),
            MenuItem(
                code='users_add',
                icon='bi-person-plus',
                label='إضافة مستخدم',
                url_name='accounts:admin_user_add',
                required_perm='manage_users',
                order=2,
            ),
            MenuItem(
                code='users_import',
                icon='bi-upload',
                label='استيراد مستخدمين',
                url_name='accounts:admin_import',
                required_perm='import_users',
                order=3,
            ),
            MenuItem(
                code='students_promote',
                icon='bi-arrow-up-circle',
                label='ترقية الطلاب',
                url_name='accounts:admin_promote',
                required_perm='promote_students',
                order=4,
            ),
        ],
    ),
    
    # === إدارة المقررات ===
    MenuItem(
        code='courses_management',
        icon='bi-journal-bookmark',
        label='إدارة المقررات',
        required_perm='manage_courses',
        order=120,
        children=[
            MenuItem(
                code='courses_list',
                icon='bi-journal-text',
                label='قائمة المقررات',
                url_name='courses:admin_courses',
                required_perm='manage_courses',
                order=1,
            ),
            MenuItem(
                code='courses_add',
                icon='bi-journal-plus',
                label='إضافة مقرر',
                url_name='courses:admin_course_add',
                required_perm='manage_courses',
                order=2,
            ),
        ],
    ),
    
    # === إدارة الإشعارات ===
    MenuItem(
        code='notifications_management',
        icon='bi-megaphone',
        label='إرسال إشعارات',
        url_name='notifications:admin_create',
        required_perm='send_notifications',
        order=130,
    ),
    
    # ========== قسم النظام (للأدمن فقط) ==========
    MenuItem(
        code='system_separator',
        icon='',
        label='--- النظام ---',
        url_name='',
        required_perm='manage_roles',
        order=200,
    ),
    
    # === إدارة الأدوار والصلاحيات ===
    MenuItem(
        code='roles_management',
        icon='bi-shield-lock',
        label='الأدوار والصلاحيات',
        required_perm='manage_roles',
        order=210,
        children=[
            MenuItem(
                code='roles_list',
                icon='bi-person-badge',
                label='الأدوار',
                url_name='accounts:admin_roles',
                required_perm='manage_roles',
                order=1,
            ),
            MenuItem(
                code='permissions_list',
                icon='bi-key',
                label='الصلاحيات',
                url_name='accounts:admin_permissions',
                required_perm='manage_permissions',
                order=2,
            ),
        ],
    ),
    
    # === إعدادات النظام ===
    MenuItem(
        code='settings',
        icon='bi-gear',
        label='إعدادات النظام',
        url_name='core:admin_settings',
        required_perm='manage_settings',
        order=220,
    ),
    
    # === سجلات التدقيق ===
    MenuItem(
        code='audit_logs',
        icon='bi-clipboard-data',
        label='سجلات التدقيق',
        url_name='core:admin_audit_logs',
        required_perm='view_audit_logs',
        order=230,
    ),
    
    # === الإحصائيات ===
    MenuItem(
        code='statistics',
        icon='bi-bar-chart-line',
        label='الإحصائيات',
        url_name='core:admin_statistics',
        required_perm='view_statistics',
        order=240,
    ),
]


def get_menu_for_user(user) -> List[MenuItem]:
    """
    الحصول على القائمة المخصصة للمستخدم بناءً على صلاحياته
    
    Args:
        user: كائن المستخدم
        
    Returns:
        قائمة عناصر القائمة المرئية للمستخدم
    """
    if not user.is_authenticated:
        return []
    
    # الأدمن يرى كل شيء
    if user.is_superuser or user.is_admin():
        user_permissions = {'__all__'}
    else:
        user_permissions = user.get_permissions()
    
    visible_items = []
    
    for item in sorted(MENU_ITEMS, key=lambda x: x.order):
        # تحقق من الصلاحية
        if item.required_perm is not None:
            if '__all__' not in user_permissions and item.required_perm not in user_permissions:
                continue
        
        # نسخ العنصر مع الأطفال المرئيين فقط
        if item.has_children():
            visible_children = item.get_visible_children(
                user_permissions if '__all__' not in user_permissions else {'__all__'}
            )
            
            # تخطي إذا لم يكن هناك أطفال مرئيين
            if not visible_children and '__all__' not in user_permissions:
                continue
            
            # إنشاء نسخة مع الأطفال المرئيين
            new_item = MenuItem(
                code=item.code,
                icon=item.icon,
                label=item.label,
                url_name=item.url_name,
                required_perm=item.required_perm,
                children=visible_children if '__all__' not in user_permissions else item.children,
                order=item.order,
                badge=item.badge,
                badge_class=item.badge_class,
            )
            visible_items.append(new_item)
        else:
            visible_items.append(item)
    
    return visible_items


def get_current_menu_item(request, menu_items: List[MenuItem]) -> Optional[str]:
    """
    تحديد العنصر الحالي في القائمة بناءً على الـ URL
    
    Returns:
        كود العنصر الحالي أو None
    """
    current_path = request.path
    
    for item in menu_items:
        if item.url_name:
            try:
                if current_path.startswith(reverse(item.url_name)):
                    return item.code
            except NoReverseMatch:
                pass
        
        for child in item.children:
            if child.url_name:
                try:
                    if current_path.startswith(reverse(child.url_name)):
                        return child.code
                except NoReverseMatch:
                    pass
    
    return None
