import time
from apscheduler.schedulers.background import BackgroundScheduler
from config import SCRAPE_INTERVAL_HOURS
from scraper import WebScraper

scheduler = BackgroundScheduler()

def scheduled_job_task():
    print(f"[Scheduler Task] Automated periodic scrape started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    scraper = WebScraper()
    result = scraper.run_pipeline()
    print(f"[Scheduler Task Completed] Result: {result}")

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            scheduled_job_task,
            trigger="interval",
            hours=SCRAPE_INTERVAL_HOURS,
            id="job_scrape_task",
            replace_existing=True
        )
        scheduler.start()
        print(f"[Scheduler] Background scheduler started. Runs every {SCRAPE_INTERVAL_HOURS} hours.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Scheduler stopped.")

if __name__ == "__main__":
    from database import init_db
    init_db()
    start_scheduler()
    print("Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
