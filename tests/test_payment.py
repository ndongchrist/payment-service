import pytest

from payment.models import OutboxEvent, Payment

pytestmark = pytest.mark.django_db


def _charge(api, amount, order_id="ord-1"):
    return api.post(
        "/charge/",
        {"order_id": order_id, "user_id": "u1", "amount": amount, "currency": "USD"},
        format="json",
    )


def test_successful_charge_emits_payment_succeeded(api):
    resp = _charge(api, "40.00")  # 40 % 13 != 0 -> success
    assert resp.status_code == 201
    assert resp.json()["status"] == "SUCCEEDED"
    assert Payment.objects.count() == 1
    evt = OutboxEvent.objects.get()
    assert evt.topic == "payment.succeeded"
    assert evt.key == "ord-1"
    assert evt.payload["amount"] == "40.00"


def test_declined_charge_emits_payment_failed(api):
    resp = _charge(api, "13.00")  # divisible by 13 -> decline
    assert resp.status_code == 201
    assert resp.json()["status"] == "FAILED"
    evt = OutboxEvent.objects.get()
    assert evt.topic == "payment.failed"
    assert "reason" in evt.payload


def test_charge_validates_input(api):
    resp = api.post("/charge/", {"order_id": "x"}, format="json")
    assert resp.status_code == 400


def test_charge_is_atomic_payment_and_event(api):
    _charge(api, "40.00")
    # one Payment <-> one outbox event, written in the same transaction
    assert Payment.objects.count() == OutboxEvent.objects.count() == 1
