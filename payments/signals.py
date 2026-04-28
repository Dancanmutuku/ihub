from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Payment
from orders.notifications import (
    send_payment_completed_notifications,
    send_payment_failed_notification,
)


@receiver(pre_save, sender=Payment)
def capture_previous_payment_state(sender, instance, **kwargs):
    instance._previous_status = None
    if not instance.pk:
        return

    previous = sender.objects.filter(pk=instance.pk).only("status").first()
    if previous:
        instance._previous_status = previous.status


@receiver(post_save, sender=Payment)
def notify_on_payment_changes(sender, instance, created, **kwargs):
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)
    if previous_status == instance.status:
        return

    if instance.status == "completed":
        send_payment_completed_notifications(instance)
    elif instance.status in {"failed", "cancelled"}:
        send_payment_failed_notification(instance)
