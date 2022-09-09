from django.contrib import admin

from .forms import UserForm
from .models import User


class UserAdmin(admin.ModelAdmin):
    model = User
    form = UserForm


admin.site.register(User, UserAdmin)
