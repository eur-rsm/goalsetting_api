from django.contrib import admin

from .models import ChatMessage


class ChatMessageAdmin(admin.ModelAdmin):
    fields = ['roomname', 'username', 'text', 'timestamp']


admin.site.register(ChatMessage, ChatMessageAdmin)
