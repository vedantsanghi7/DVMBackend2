from django.contrib import admin
from .models import PassengerProfile


class PassengerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'phone')
    search_fields = ('user__username', 'user__email', 'phone')


admin.site.register(PassengerProfile, PassengerProfileAdmin)