from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.logger import log

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            log.info("APScheduler started successfully.")

    def add_cron_job(self, job_id: str, func, cron_expr: str, args=None):
        if args is None:
            args = []
        trigger = CronTrigger.from_crontab(cron_expr)
        job = self.scheduler.add_job(func, trigger, args=args, id=job_id, replace_existing=True)
        self.jobs[job_id] = job
        log.info(f"Added cron job {job_id} with expression {cron_expr}")

    def pause_job(self, job_id: str):
        self.scheduler.pause_job(job_id)
        log.info(f"Paused job {job_id}")

    def resume_job(self, job_id: str):
        self.scheduler.resume_job(job_id)
        log.info(f"Resumed job {job_id}")

    def remove_job(self, job_id: str):
        self.scheduler.remove_job(job_id)
        self.jobs.pop(job_id, None)
        log.info(f"Removed job {job_id}")

scheduler_service = SchedulerService()
