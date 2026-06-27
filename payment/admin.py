from django.contrib import admin

from .models import OutboxEvent, Payment


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "status", "attempts", "created_at", "published_at")
    list_filter = ("status", "topic")
    search_fields = ("id", "topic", "correlation_id")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order_id", "amount", "currency", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("order_id", "user_id")
