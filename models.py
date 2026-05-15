from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Drug(db.Model):
    """药品表"""
    __tablename__ = 'drugs'
    
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specification = db.Column(db.String(50))
    category = db.Column(db.String(50))
    
    # 用药信息
    daily_dosage = db.Column(db.Float, default=1.0)
    before_breakfast = db.Column(db.Boolean, default=False)
    after_breakfast = db.Column(db.Boolean, default=False)
    before_lunch = db.Column(db.Boolean, default=False)
    after_lunch = db.Column(db.Boolean, default=False)
    before_dinner = db.Column(db.Boolean, default=False)
    after_dinner = db.Column(db.Boolean, default=False)
    
    # 有效期信息
    validity_period = db.Column(db.Integer)
    production_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    
    # 库存信息
    stock_quantity = db.Column(db.Integer, default=0)
    remaining_quantity = db.Column(db.Integer, default=0)
    
    # 其他信息
    supplier = db.Column(db.String(100))
    unit_price = db.Column(db.Float)
    instructions = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    stock_records = db.relationship('StockRecord', backref='drug', lazy='dynamic')
    alerts = db.relationship('Alert', backref='drug', lazy='dynamic')
    medication_logs = db.relationship('MedicationLog', backref='drug', lazy='dynamic')
    
    def get_medication_times_str(self):
        """获取服药时间的字符串表示"""
        times = []
        if self.before_breakfast:
            times.append('早饭前')
        if self.after_breakfast:
            times.append('早饭后')
        if self.before_lunch:
            times.append('午饭前')
        if self.after_lunch:
            times.append('午饭后')
        if self.before_dinner:
            times.append('晚饭前')
        if self.after_dinner:
            times.append('晚饭后')
        return ', '.join(times) if times else '未设置'
    
    def get_days_remaining(self):
        """计算剩余可用天数"""
        if self.daily_dosage == 0 or self.daily_dosage is None:
            return 0
        return int(self.remaining_quantity / self.daily_dosage)
    
    def get_stock_status(self):
        """获取库存状态"""
        if self.remaining_quantity == 0:
            return ('danger', '已用完')
        
        days = self.get_days_remaining()
        if days <= 3:
            return ('danger', f'严重不足（剩{days}天）')
        elif days <= 7:
            return ('warning', f'库存紧张（剩{days}天）')
        elif days <= 15:
            return ('info', f'库存不足（剩{days}天）')
        else:
            return ('success', '正常')
    
    def get_expiry_status(self):
        """获取过期状态"""
        if not self.expiry_date:
            return ('secondary', '未知')
        
        days_to_expiry = (self.expiry_date - date.today()).days
        
        if days_to_expiry < 0:
            return ('danger', f'已过期{abs(days_to_expiry)}天')
        elif days_to_expiry <= 30:
            return ('warning', f'即将过期（{days_to_expiry}天）')
        elif days_to_expiry <= 90:
            return ('info', f'注意有效期（{days_to_expiry}天）')
        else:
            return ('success', '正常')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'drug_id': self.drug_id,
            'name': self.name,
            'specification': self.specification,
            'category': self.category,
            'daily_dosage': self.daily_dosage,
            'medication_times': self.get_medication_times_str(),
            'validity_period': self.validity_period,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'stock_quantity': self.stock_quantity,
            'remaining_quantity': self.remaining_quantity,
            'days_remaining': self.get_days_remaining(),
            'stock_status': self.get_stock_status(),
            'expiry_status': self.get_expiry_status(),
            'supplier': self.supplier,
            'unit_price': self.unit_price,
            'instructions': self.instructions
        }


class StockRecord(db.Model):
    """库存变更记录表"""
    __tablename__ = 'stock_records'
    
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    change_type = db.Column(db.String(20), nullable=False)  # 'auto_deduct', 'manual_in', 'manual_out'
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer)
    new_quantity = db.Column(db.Integer)
    change_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'drug_id': self.drug_id,
            'drug_name': self.drug.name if self.drug else None,
            'change_type': self.change_type,
            'quantity': self.quantity,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'change_date': self.change_date.isoformat() if self.change_date else None,
            'notes': self.notes
        }


class Alert(db.Model):
    """预警记录表"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # 'expired', 'expiring_soon', 'low_stock', 'stock_insufficient'
    alert_level = db.Column(db.String(20), nullable=False)  # 'danger', 'warning', 'info'
    alert_message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'drug_id': self.drug_id,
            'drug_name': self.drug.name if self.drug else None,
            'alert_type': self.alert_type,
            'alert_level': self.alert_level,
            'alert_message': self.alert_message,
            'is_read': self.is_read,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class MedicationLog(db.Model):
    """服药日志表"""
    __tablename__ = 'medication_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    medication_date = db.Column(db.Date, nullable=False)
    planned_dosage = db.Column(db.Float)
    actual_dosage = db.Column(db.Float)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'drug_id': self.drug_id,
            'drug_name': self.drug.name if self.drug else None,
            'medication_date': self.medication_date.isoformat() if self.medication_date else None,
            'planned_dosage': self.planned_dosage,
            'actual_dosage': self.actual_dosage,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'notes': self.notes
        }
