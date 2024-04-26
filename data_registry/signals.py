from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from data_registry import models


@receiver(post_save, sender=models.Job)
def create_tasks(sender, instance, created, raw, **kwargs):
    if created and not raw:
        for order, task_type in enumerate(settings.JOB_TASKS_PLAN, 1):
            instance.task_set.create(type=task_type, order=order)
