"""DRF serializers for the payment domain."""
from __future__ import annotations

from rest_framework import serializers

from .models import Payment


class ChargeRequestSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=64)
    user_id = serializers.CharField(max_length=64)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    currency = serializers.CharField(max_length=3, default="USD")


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order_id", "user_id", "amount", "currency", "status", "reason", "created_at"]
