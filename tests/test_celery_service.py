from services.celeryService import celery_app


def test_worker_registers_all_runtime_queues():
    assert {"default", "expiry_queue", "payout_queue", "webhook_queue"} <= set(
        celery_app.amqp.queues.keys()
    )
    assert celery_app.amqp.queues["webhook_queue"].routing_key == "webhook_queue"
