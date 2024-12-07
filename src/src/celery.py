from __future__ import absolute_import, unicode_literals
import os
from celery.schedules import crontab

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

app = Celery(__name__)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(
    CELERYBEAT_SCHEDULE={
        "archive_expired_bookings": {
            "task": "base.tasks.archive_expired_bookings",
            "schedule": crontab(),
        }
    }
)