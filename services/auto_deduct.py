"""
自动扣药服务
每天凌晨自动扣除药品库存
"""
from datetime import datetime, date
from models import db, Drug, StockRecord, MedicationLog, Alert


def auto_deduct_daily_medication():
    """
    每天自动扣除药品库存
    执行时间: 每天00:05
    """
    print(f"[{datetime.now()}] 开始执行自动扣药任务...")
    
    today = date.today()
    
    # 获取所有活跃药品（剩余量 > 0）
    drugs = Drug.query.filter(Drug.remaining_quantity > 0).all()
    
    if not drugs:
        print(f"[{datetime.now()}] 没有需要扣药的药品")
        return
    
    success_count = 0
    failed_count = 0
    
    for drug in drugs:
        try:
            # 计算今日应扣除量
            daily_dosage = drug.daily_dosage or 0
            
            if daily_dosage == 0:
                print(f"[{datetime.now()}] {drug.name} 每日用量为0，跳过")
                continue
            
            # 记录扣药前数量
            previous_qty = drug.remaining_quantity
            
            # 检查是否足够扣除
            if drug.remaining_quantity >= daily_dosage:
                # 扣除库存
                drug.remaining_quantity -= daily_dosage
                
                # 记录库存变更
                record = StockRecord(
                    drug_id=drug.id,
                    change_type='auto_deduct',
                    quantity=-daily_dosage,
                    previous_quantity=previous_qty,
                    new_quantity=drug.remaining_quantity,
                    notes=f'自动扣除今日用药 {daily_dosage}片'
                )
                db.session.add(record)
                
                # 记录服药日志
                log = MedicationLog(
                    drug_id=drug.id,
                    medication_date=today,
                    planned_dosage=daily_dosage,
                    actual_dosage=daily_dosage,
                    notes='自动执行'
                )
                db.session.add(log)
                
                success_count += 1
                print(f"[{datetime.now()}] ✅ {drug.name}: 扣除{daily_dosage}片，剩余{drug.remaining_quantity}片")
            
            else:
                # 库存不足，记录警告
                log = MedicationLog(
                    drug_id=drug.id,
                    medication_date=today,
                    planned_dosage=daily_dosage,
                    actual_dosage=0,
                    notes=f'库存不足，无法扣药（剩余{drug.remaining_quantity}片，需{daily_dosage}片）'
                )
                db.session.add(log)
                
                # 创建紧急预警
                alert = Alert(
                    drug_id=drug.id,
                    alert_type='stock_insufficient',
                    alert_level='danger',
                    alert_message=f'{drug.name}库存不足，无法完成今日服药计划（剩余{drug.remaining_quantity}片，需{daily_dosage}片）'
                )
                db.session.add(alert)
                
                failed_count += 1
                print(f"[{datetime.now()}] ❌ {drug.name}: 库存不足（剩余{drug.remaining_quantity}片，需{daily_dosage}片）")
        
        except Exception as e:
            print(f"[{datetime.now()}] ❌ {drug.name} 扣药失败: {e}")
            failed_count += 1
            continue
    
    # 提交数据库更改
    try:
        db.session.commit()
        print(f"[{datetime.now()}] 数据库更新成功")
    except Exception as e:
        db.session.rollback()
        print(f"[{datetime.now()}] 数据库更新失败: {e}")
        return
    
    # 执行完扣药后，检查所有预警
    try:
        from services.alert_checker import check_all_alerts
        check_all_alerts()
        print(f"[{datetime.now()}] 预警检查完成")
    except Exception as e:
        print(f"[{datetime.now()}] 预警检查失败: {e}")
    
    print(f"[{datetime.now()}] 自动扣药任务完成: 成功{success_count}个，失败{failed_count}个")


def get_medication_schedule():
    """
    获取今日服药计划
    返回按时间段分组的药品列表
    """
    drugs = Drug.query.filter(Drug.remaining_quantity > 0, Drug.daily_dosage > 0).all()
    
    schedule = {
        '早饭前': [],
        '早饭后': [],
        '午饭前': [],
        '午饭后': [],
        '晚饭前': [],
        '晚饭后': []
    }
    
    for drug in drugs:
        # 计算每次的用量（如果每天多次，则平均分配）
        times_count = sum([
            drug.before_breakfast, drug.after_breakfast,
            drug.before_lunch, drug.after_lunch,
            drug.before_dinner, drug.after_dinner
        ])
        
        if times_count == 0:
            continue
        
        dosage_per_time = drug.daily_dosage / times_count
        
        if drug.before_breakfast:
            schedule['早饭前'].append(f"{drug.name}({dosage_per_time}片)")
        if drug.after_breakfast:
            schedule['早饭后'].append(f"{drug.name}({dosage_per_time}片)")
        if drug.before_lunch:
            schedule['午饭前'].append(f"{drug.name}({dosage_per_time}片)")
        if drug.after_lunch:
            schedule['午饭后'].append(f"{drug.name}({dosage_per_time}片)")
        if drug.before_dinner:
            schedule['晚饭前'].append(f"{drug.name}({dosage_per_time}片)")
        if drug.after_dinner:
            schedule['晚饭后'].append(f"{drug.name}({dosage_per_time}片)")
    
    return schedule
