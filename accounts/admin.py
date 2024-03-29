from django.contrib import admin
from accounts.models import *
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
# Register your models here.

class AccountInline(admin.StackedInline):
    model = Account
    can_delete = False
    verbose_name_plural = 'Account'

class CustomizedUserAdmin(UserAdmin):
    inlines = (AccountInline,)


admin.site.unregister(User)
admin.site.register(User,CustomizedUserAdmin)

admin.site.register(Menu)
admin.site.register(Account)

admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(Modifier)


admin.site.register(Reviews)

admin.site.register(Order)

admin.site.register(Clients)