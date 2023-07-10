from apscheduler.executors.asyncio import AsyncIOExecutor
# from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR
from pytz import utc


DEFAULT = "default"

jobstores = {
    DEFAULT: MemoryJobStore()
}


executors = {DEFAULT: AsyncIOExecutor()}

# {"coalesce": False, "max_instances": 3, "misfire_grace_time": 3600}
job_defaults = {
    'coalesce': False,
    'max_instances': 300,
    "misfire_grace_time": 600
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc
)

def event_listener(event):
    '''For facebook parser'''
    if event.exception:
        pass

scheduler.add_listener(event_listener, EVENT_JOB_ERROR)


async def on_startup(_):
    scheduler.start()


async def on_shutdown(_):
    scheduler.shutdown()


def setup(runner):
    runner.on_startup(on_startup)
    runner.on_shutdown(on_shutdown)
