import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spam_shield.settings')

app = Celery('spam_shield')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Register tasks from email_connector
app.autodiscover_tasks(['email_connector'])


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')