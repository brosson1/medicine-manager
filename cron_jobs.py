"""
Render Cron Job 入口文件
这个文件会被Render的Cron Job服务调用，执行自动扣药任务
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from services.auto_deduct import auto_deduct_daily_medication
from services.alert_checker import check_all_alerts
from datetime import datetime


def run_auto_deduct():
    """执行自动扣药任务（Render Cron Job调用）"""
    print(f"[{datetime.now()}] === Render Cron Job: 自动扣药开始 ===")
    
    with app.app_context():
        try:
            # 执行自动扣药
            auto_deduct_daily_medication()
            
            # 检查预警
            check_all_alerts()
            
            print(f"[{datetime.now()}] === Render Cron Job: 自动扣药完成 ===")
            
        except Exception as e:
            print(f"[{datetime.now()}] === Render Cron Job: 自动扣药失败 ===")
            print(f"错误详情: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    run_auto_deduct()
