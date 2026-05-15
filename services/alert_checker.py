"""
预警检查服务
检查库存不足和过期预警
"""
from datetime import datetime, date, timedelta
from models import db, Drug, Alert


def check_all_alerts():
    """
    检查所有药品的预警状态
    包括：库存不足预警、过期预警
    """
    print(f"[{datetime.now()}] 开始检查预警...")
    
    drugs = Drug.query.all()
    
    alert_count = 0
    
    for drug in drugs:
        # 检查库存预警
        low_stock_alert = check_low_stock_alert(drug)
        if low_stock_alert:
            save_alert(low_stock_alert)
            alert_count += 1
        
        # 检查过期预警
        expiry_alert = check_expiry_alert(drug)
        if expiry_alert:
            save_alert(expiry_alert)
            alert_count += 1
    
    print(f"[{datetime.now()}] 预警检查完成，发现{alert_count}条新预警")
    return alert_count


def check_low_stock_alert(drug):
    """
    库存不足预警检查（提前15天）
    规则：
    - 剩余量 = 0: 已用完（危险）
    - 剩余量 ≤ 3天: 严重不足（危险）
    - 剩余量 ≤ 7天: 库存紧张（警告）
    - 剩余量 ≤ 15天: 库存不足（提示）
    """
    if not drug.daily_dosage or drug.daily_dosage == 0:
        return None
    
    days_remaining = drug.remaining_quantity / drug.daily_dosage
    
    # 检查是否已存在相同类型的未解决预警
    existing_alert = Alert.query.filter_by(
        drug_id=drug.id,
        alert_type='low_stock',
        is_resolved=False
    ).first()
    
    # 根据剩余天数判断预警级别
    if drug.remaining_quantity == 0:
        level = 'danger'
        msg = f'{drug.name}已用完，请立即补货'
    elif days_remaining <= 3:
        level = 'danger'
        msg = f'{drug.name}仅剩{drug.remaining_quantity:.0f}片，只够{days_remaining:.0f}天，请立即补货'
    elif days_remaining <= 7:
        level = 'warning'
        msg = f'{drug.name}库存紧张，仅剩{days_remaining:.0f}天用量，建议尽快补货'
    elif days_remaining <= 15:
        level = 'info'
        msg = f'{drug.name}库存不足，剩余{days_remaining:.0f}天，建议补货'
    else:
        # 库存充足，如果存在未解决的预警则标记为已解决
        if existing_alert and existing_alert.alert_level != 'danger':
            existing_alert.is_resolved = True
            existing_alert.resolved_at = datetime.utcnow()
            db.session.commit()
        return None
    
    # 如果已存在相同级别的预警，不重复创建
    if existing_alert and existing_alert.alert_level == level:
        # 更新预警消息
        existing_alert.alert_message = msg
        existing_alert.created_at = datetime.utcnow()
        db.session.commit()
        return None
    
    return Alert(
        drug_id=drug.id,
        alert_type='low_stock',
        alert_level=level,
        alert_message=msg
    )


def check_expiry_alert(drug):
    """
    过期预警检查
    规则：
    - 已过期: 已过期（危险）
    - 30天内过期: 即将过期（警告）
    - 90天内过期: 注意有效期（提示）
    """
    if not drug.expiry_date:
        return None
    
    days_to_expiry = (drug.expiry_date - date.today()).days
    
    # 检查是否已存在相同类型的未解决预警
    existing_alert = Alert.query.filter_by(
        drug_id=drug.id,
        alert_type='expiring_soon',
        is_resolved=False
    ).first()
    
    # 根据距离过期的天数判断预警级别
    if days_to_expiry < 0:
        level = 'danger'
        msg = f'{drug.name}已过期{abs(days_to_expiry)}天，请立即处理'
    elif days_to_expiry <= 30:
        level = 'warning'
        msg = f'{drug.name}将在{days_to_expiry}天后过期，请尽快使用'
    elif days_to_expiry <= 90:
        level = 'info'
        msg = f'{drug.name}将在{days_to_expiry}天后过期，注意有效期'
    else:
        # 未过期，如果存在未解决的预警则标记为已解决
        if existing_alert:
            existing_alert.is_resolved = True
            existing_alert.resolved_at = datetime.utcnow()
            db.session.commit()
        return None
    
    # 如果已存在相同级别的预警，不重复创建
    if existing_alert and existing_alert.alert_level == level:
        # 更新预警消息
        existing_alert.alert_message = msg
        existing_alert.created_at = datetime.utcnow()
        db.session.commit()
        return None
    
    return Alert(
        drug_id=drug.id,
        alert_type='expiring_soon',
        alert_level=level,
        alert_message=msg
    )


def save_alert(alert):
    """保存预警到数据库"""
    try:
        db.session.add(alert)
        db.session.commit()
        print(f"[{datetime.now()}] 新预警: {alert.alert_message}")
    except Exception as e:
        db.session.rollback()
        print(f"[{datetime.now()}] 保存预警失败: {e}")


def get_active_alerts():
    """获取所有活跃的预警（未解决）"""
    return Alert.query.filter_by(is_resolved=False).order_by(Alert.created_at.desc()).all()


def get_alerts_summary():
    """获取预警统计摘要"""
    total_alerts = Alert.query.filter_by(is_resolved=False).count()
    danger_alerts = Alert.query.filter_by(is_resolved=False, alert_level='danger').count()
    warning_alerts = Alert.query.filter_by(is_resolved=False, alert_level='warning').count()
    info_alerts = Alert.query.filter_by(is_resolved=False, alert_level='info').count()
    
    return {
        'total': total_alerts,
        'danger': danger_alerts,
        'warning': warning_alerts,
        'info': info_alerts
    }


def mark_alert_as_read(alert_id):
    """标记预警为已读"""
    alert = Alert.query.get(alert_id)
    if alert:
        alert.is_read = True
        db.session.commit()
        return True
    return False


def resolve_alert(alert_id):
    """标记预警为已解决"""
    alert = Alert.query.get(alert_id)
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        return True
    return False
