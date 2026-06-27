"""Payment API.

`POST /charge/` is called service-to-service by order-service (not through Kong),
so it doesn't carry an X-User-Id header — the caller passes user_id in the body
and the default-deny NetworkPolicy (Phase 6) is what restricts who may call it.

The charge writes the Payment row AND its outbox event in one transaction, then
the relay publishes payment.succeeded / payment.failed to Kafka.
"""
from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from .events import emit_event
from .models import Payment
from .serializers import ChargeRequestSerializer, PaymentSerializer


def _is_declined(amount) -> bool:
    """Mock gateway: decline when the whole-dollar amount is divisible by 13.
    Deterministic so both the success and decline paths are demoable."""
    return int(amount) % 13 == 0


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def charge(request: Request) -> Response:
    req = ChargeRequestSerializer(data=request.data)
    req.is_valid(raise_exception=True)
    data = req.validated_data
    now = timezone.now()

    declined = _is_declined(data["amount"])
    with transaction.atomic():
        payment = Payment.objects.create(
            order_id=data["order_id"],
            user_id=data["user_id"],
            amount=data["amount"],
            currency=data["currency"],
            status=Payment.Status.FAILED if declined else Payment.Status.SUCCEEDED,
            reason="declined: amount divisible by 13" if declined else "",
        )
        base = {
            "event_id": str(uuid.uuid4()),
            "payment_id": str(payment.id),
            "order_id": payment.order_id,
            "user_id": payment.user_id,
            "amount": str(payment.amount),
            "currency": payment.currency,
        }
        if declined:
            emit_event(
                "payment.failed", key=payment.order_id,
                payload={**base, "reason": payment.reason, "failed_at": now.isoformat()},
            )
        else:
            emit_event(
                "payment.succeeded", key=payment.order_id,
                payload={**base, "succeeded_at": now.isoformat()},
            )

    return Response(PaymentSerializer(payment).data, status=201)
