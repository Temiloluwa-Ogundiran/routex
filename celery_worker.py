from services.celeryService import celery_app

# This file is used to launch the worker:
# celery -A celery_worker.celery_app worker --loglevel=info
