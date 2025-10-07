from app.tasks import celery

if __name__ == "__main__":
    celery.worker_main(argv=["worker", "-l", "INFO", "-Q", "celery"])
