"""
Template Tags للصلاحيات والقائمة الديناميكية
S-ACM - Smart Academic Content Management System

Usage in templates:
    {% load permissions %}
    
    {% has_perm 'manage_files' %}
        <button>رفع ملف</button>
    {% endhas_perm %}
    
    {% if request.user|has_permission:'view_courses' %}
        ...
    {% endif %}
"""

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, permission_code):
    """
    التحقق مما إذا كان المستخدم يمتلك صلاحية معينة
    
    Usage:
        {% has_perm 'manage_files' as can_manage %}
        {% if can_manage %}...{% endif %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user_permissions = getattr(request, 'user_permissions', set())
    
    # الأدمن له كل الصلاحيات
    if '__all__' in user_permissions:
        return True
    
    return permission_code in user_permissions


@register.filter
def has_permission(user, permission_code):
    """
    فلتر للتحقق من صلاحية المستخدم
    
    Usage:
        {% if request.user|has_permission:'view_courses' %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.has_perm(permission_code)


@register.inclusion_tag('components/sidebar.html', takes_context=True)
def render_sidebar(context):
    """
    رندر القائمة الجانبية الديناميكية
    
    Usage:
        {% render_sidebar %}
    """
    request = context.get('request')
    menu_items = context.get('menu_items', [])
    
    # تحديد العنصر الحالي
    current_path = request.path if request else ''
    current_item = None
    
    for item in menu_items:
        if item.url_name:
            try:
                if current_path.startswith(reverse(item.url_name)):
                    current_item = item.code
                    break
            except NoReverseMatch:
                pass
        
        for child in getattr(item, 'children', []):
            if child.url_name:
                try:
                    if current_path.startswith(reverse(child.url_name)):
                        current_item = child.code
                        break
                except NoReverseMatch:
                    pass
    
    return {
        'menu_items': menu_items,
        'current_item': current_item,
        'request': request,
    }


@register.simple_tag
def menu_item_url(item):
    """
    الحصول على URL عنصر القائمة
    
    Usage:
        {% menu_item_url item as url %}
    """
    if not item.url_name:
        return '#'
    try:
        return reverse(item.url_name)
    except NoReverseMatch:
        return '#'


@register.simple_tag(takes_context=True)
def is_active_menu(context, item_code):
    """
    التحقق مما إذا كان العنصر نشطاً
    
    Usage:
        {% is_active_menu 'dashboard' as is_active %}
    """
    request = context.get('request')
    if not request:
        return False
    
    from apps.core.menu import get_current_menu_item
    menu_items = context.get('menu_items', [])
    current = get_current_menu_item(request, menu_items)
    
    return current == item_code


@register.filter
def get_item_attr(item, attr_name):
    """
    الحصول على خاصية من عنصر القائمة
    
    Usage:
        {{ item|get_item_attr:'icon' }}
    """
    return getattr(item, attr_name, '')
