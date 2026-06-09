from django.contrib import admin

from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "cartilla",
        "module_key",
        "row_key",
        "slot",
        "original_name",
        "mime_type",
        "size",
        "created_at",
    )
    search_fields = ("client_attachment_id", "original_name", "module_key", "row_key")
    list_filter = ("module_key", "mime_type")
