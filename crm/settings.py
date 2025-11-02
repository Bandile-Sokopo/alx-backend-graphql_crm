from celery.schedules import crontab

CELERY_BROKER_URL = "redis://localhost:6379/0"

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'django_filters',
    'crm',
    'graphene_django',
    'django_filters',
    'django_crontab',
    'django_celery_beat',
]

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
