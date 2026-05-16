from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Initialize the AsyncIOScheduler.
# AsyncIOScheduler is designed to run within an asynchronous event loop (like FastAPI's).
# It allows you to schedule tasks (jobs) to run at specific intervals, 
# fixed times, or via cron-like expressions.
scheduler = AsyncIOScheduler()

#TODO: WILL USE IT FOR FUTURE PURPOSES