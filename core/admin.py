from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Poll, Option, VoteLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)


class OptionInline(admin.TabularInline):
    model = Option
    extra = 2
    min_num = 2
    max_num = 5


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'total_votes', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('question', 'author__username')
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'poll', 'vote_count')
    search_fields = ('text', 'poll__question')


@admin.register(VoteLog)
class VoteLogAdmin(admin.ModelAdmin):
    list_display = ('poll', 'option', 'user', 'session_key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('poll__question', 'user__username', 'session_key')
