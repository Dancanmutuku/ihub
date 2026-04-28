from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order
from .notifications import send_order_status_update_notification


@receiver(pre_save, sender=Order)
def capture_previous_order_state(sender, instance, **kwargs):
    instance._previous_status = None
    if not instance.pk:
        return

    previous = sender.objects.filter(pk=instance.pk).only("status").first()
    if previous:
        instance._previous_status = previous.status


@receiver(post_save, sender=Order)
def notify_on_order_changes(sender, instance, created, **kwargs):
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)
    if previous_status and previous_status != instance.status:
        send_order_status_update_notification(instance, previous_status)
