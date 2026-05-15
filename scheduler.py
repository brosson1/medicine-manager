"""
定时任务配置 - 使用APScheduler
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


def init_scheduler(app):
    """初始化定时任务调度器"""
    scheduler = BackgroundScheduler()
    
    # 每天00:05执行自动扣药
    @scheduler.scheduled_job(CronTrigger(hour=0, minute=5))
    def auto_deduct_job():
        """自动扣药任务"""
        with app.app_context():
            from services.auto_deduct import auto_deduct_daily_medication
            print(f"[{datetime.now()}] 开始执行定时扣药任务...")
            try:
                auto_deduct_daily_medication()
                print(f"[{datetime.now()}] 定时扣药任务执行完成")
            except Exception as e:
                print(f"[{datetime.now()}] 定时扣药任务执行失败: {e}")
    
    # 每小时检查预警（可选）
    @scheduler.scheduled_job(CronTrigger(hour='*', minute=0))
    def check_alerts_job():
        """检查预警任务"""
        with app.app_context():
            from services.alert_checker import check_all_alerts
            print(f"[{datetime.now()}] 开始检查预警...")
            try:
                check_all_alerts()
                print(f"[{datetime.now()}] 预警检查完成")
            except Exception as e:
                print(f"[{datetime.now()}] 预警检查失败: {e}")
    
    scheduler.start()
    print(f"[{datetime.now()}] 定时任务调度器已启动")
    
    return scheduler
