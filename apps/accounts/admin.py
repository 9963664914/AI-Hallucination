from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_organization', 'get_role')

    def get_organization(self, instance):
        return instance.profile.organization if hasattr(instance, 'profile') else '-'
    get_organization.short_description = 'Organization'

    def get_role(self, instance):
        return instance.profile.get_role_display() if hasattr(instance, 'profile') else '-'
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
