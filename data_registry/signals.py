from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from data_registry import models
from data_registry.process_manager import get_task_manager


# FYI, not called by qs.bulk_create(), qs.bulk_update() or qs.update().
# https://docs.djangoproject.com/en/4.2/ref/models/querysets/#bulk-create
# https://docs.djangoproject.com/en/4.2/ref/models/querysets/#bulk-update
# https://docs.djangoproject.com/en/4.2/ref/models/querysets/#update
@receiver(post_save, sender=models.Job)
def create_tasks(sender, instance, created, raw, **kwargs):
    if created and not raw:
        for order, task_type in enumerate(settings.JOB_TASKS_PLAN, 1):
            instance.task_set.create(type=task_type, order=order)


# qs.delete() emits signals for deleted instances, including cascaded deletions, but doesn't call the model's delete().
# https://docs.djangoproject.com/en/4.2/ref/models/querysets/#delete
@receiver(pre_delete, sender=models.Task)
def wipe_task(sender, instance, **kwargs):
    get_task_manager(instance).wipe()
