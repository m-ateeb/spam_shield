import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spam_shield.settings')

app = Celery('spam_shield')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()