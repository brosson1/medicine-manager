"""
药品管理系统 - Flask主应用
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from models import db, Drug, StockRecord, Alert, MedicationLog
from services.auto_deduct import auto_deduct_daily_medication, get_medication_schedule
from services.alert_checker import check_all_alerts, get_active_alerts, get_alerts_summary
import os

# 创建Flask应用
app = Flask(__name__)

# 配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'medicine.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'medicine-manager-secret-key-2026'

# 初始化数据库
db.init_app(app)


# ==================== 首页和数据看板 ====================

@app.route('/')
def index():
    """首页 - 数据看板"""
    # 获取统计信息
    total_drugs = Drug.query.count()
    active_drugs = Drug.query.filter(Drug.remaining_quantity > 0).count()
    
    # 获取预警摘要
    alerts_summary = get_alerts_summary()
    
    # 获取最新5条预警
    latest_alerts = Alert.query.filter_by(is_resolved=False).order_by(Alert.created_at.desc()).limit(5).all()
    
    # 获取今日服药计划
    schedule = get_medication_schedule()
    
    # 获取今日扣药日志
    today = date.today()
    today_logs = MedicationLog.query.filter_by(medication_date=today).all()
    
    # 计算今日扣药总量
    today_total = sum([log.actual_dosage for log in today_logs if log.actual_dosage])
    
    # 检查今日是否已扣药
    auto_deduct_executed = len(today_logs) > 0
    
    return render_template('index.html',
                         total_drugs=total_drugs,
                         active_drugs=active_drugs,
                         alerts_summary=alerts_summary,
                         latest_alerts=latest_alerts,
                         schedule=schedule,
                         today_logs=today_logs,
                         today_total=today_total,
                         auto_deduct_executed=auto_deduct_executed)


# ==================== 药品管理 ====================

@app.route('/drugs')
def drugs_list():
    """药品列表"""
    # 获取筛选参数
    category = request.args.get('category', '')
    stock_status = request.args.get('stock_status', '')
    
    # 基础查询
    query = Drug.query
    
    # 分类筛选
    if category:
        query = query.filter(Drug.category == category)
    
    # 库存状态筛选
    if stock_status == 'low':
        # 库存不足（剩余15天以内）
        query = query.filter(Drug.remaining_quantity > 0)
        drugs = [d for d in query.all() if d.get_days_remaining() <= 15]
    elif stock_status == 'out':
        # 已用完
        query = query.filter(Drug.remaining_quantity == 0)
    elif stock_status == 'normal':
        # 正常
        query = query.filter(Drug.remaining_quantity > 0)
        drugs = [d for d in query.all() if d.get_days_remaining() > 15]
    else:
        drugs = query.all()
    
    # 获取所有分类（用于筛选下拉框）
    categories = db.session.query(Drug.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('drugs/list.html', 
                         drugs=drugs, 
                         categories=categories,
                         selected_category=category,
                         selected_stock_status=stock_status)


@app.route('/drugs/<int:drug_id>')
def drug_detail(drug_id):
    """药品详情"""
    drug = Drug.query.get_or_404(drug_id)
    
    # 获取最近7天的扣药记录
    recent_records = StockRecord.query.filter_by(drug_id=drug_id)\
        .order_by(StockRecord.change_date.desc()).limit(7).all()
    
    # 获取最近7天的服药日志
    recent_logs = MedicationLog.query.filter_by(drug_id=drug_id)\
        .order_by(MedicationLog.medication_date.desc()).limit(7).all()
    
    return render_template('drugs/detail.html', 
                         drug=drug, 
                         recent_records=recent_records,
                         recent_logs=recent_logs)


@app.route('/drugs/new', methods=['GET', 'POST'])
def drug_new():
    """新增药品"""
    if request.method == 'POST':
        try:
            # 创建药品对象
            drug = Drug(
                drug_id=request.form.get('drug_id'),
                name=request.form.get('name'),
                specification=request.form.get('specification'),
                category=request.form.get('category'),
                daily_dosage=float(request.form.get('daily_dosage', 0)),
                before_breakfast='before_breakfast' in request.form,
                after_breakfast='after_breakfast' in request.form,
                before_lunch='before_lunch' in request.form,
                after_lunch='after_lunch' in request.form,
                before_dinner='before_dinner' in request.form,
                after_dinner='after_dinner' in request.form,
                validity_period=int(request.form.get('validity_period', 0)),
                supplier=request.form.get('supplier'),
                unit_price=float(request.form.get('unit_price', 0)) if request.form.get('unit_price') else None,
                instructions=request.form.get('instructions')
            )
            
            # 处理日期字段
            if request.form.get('production_date'):
                drug.production_date = datetime.strptime(request.form.get('production_date'), '%Y-%m-%d').date()
            
            if request.form.get('expiry_date'):
                drug.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()
            
            # 处理库存
            stock_qty = int(request.form.get('stock_quantity', 0))
            drug.stock_quantity = stock_qty
            drug.remaining_quantity = stock_qty
            
            db.session.add(drug)
            db.session.commit()
            
            flash('药品添加成功！', 'success')
            return redirect(url_for('drug_detail', drug_id=drug.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败：{str(e)}', 'danger')
    
    return render_template('drugs/form.html', drug=None)


@app.route('/drugs/<int:drug_id>/edit', methods=['GET', 'POST'])
def drug_edit(drug_id):
    """编辑药品"""
    drug = Drug.query.get_or_404(drug_id)
    
    if request.method == 'POST':
        try:
            drug.drug_id = request.form.get('drug_id')
            drug.name = request.form.get('name')
            drug.specification = request.form.get('specification')
            drug.category = request.form.get('category')
            drug.daily_dosage = float(request.form.get('daily_dosage', 0))
            drug.before_breakfast = 'before_breakfast' in request.form
            drug.after_breakfast = 'after_breakfast' in request.form
            drug.before_lunch = 'before_lunch' in request.form
            drug.after_lunch = 'after_lunch' in request.form
            drug.before_dinner = 'before_dinner' in request.form
            drug.after_dinner = 'after_dinner' in request.form
            drug.validity_period = int(request.form.get('validity_period', 0))
            drug.supplier = request.form.get('supplier')
            drug.unit_price = float(request.form.get('unit_price', 0)) if request.form.get('unit_price') else None
            drug.instructions = request.form.get('instructions')
            
            if request.form.get('production_date'):
                drug.production_date = datetime.strptime(request.form.get('production_date'), '%Y-%m-%d').date()
            
            if request.form.get('expiry_date'):
                drug.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()
            
            db.session.commit()
            flash('药品更新成功！', 'success')
            return redirect(url_for('drug_detail', drug_id=drug.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('drugs/form.html', drug=drug)


@app.route('/drugs/<int:drug_id>/delete', methods=['POST'])
def drug_delete(drug_id):
    """删除药品"""
    drug = Drug.query.get_or_404(drug_id)
    try:
        db.session.delete(drug)
        db.session.commit()
        flash('药品已删除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('drugs_list'))


# ==================== 库存管理 ====================

@app.route('/stocks')
def stocks_manage():
    """库存管理页面"""
    drugs = Drug.query.filter(Drug.remaining_quantity >= 0).all()
    return render_template('stocks/manage.html', drugs=drugs)


@app.route('/stocks/add', methods=['POST'])
def stock_add():
    """入库操作"""
    drug_id = int(request.form.get('drug_id'))
    quantity = int(request.form.get('quantity'))
    notes = request.form.get('notes', '')
    
    drug = Drug.query.get_or_404(drug_id)
    
    try:
        previous_qty = drug.remaining_quantity
        drug.remaining_quantity += quantity
        drug.stock_quantity += quantity
        
        record = StockRecord(
            drug_id=drug.id,
            change_type='manual_in',
            quantity=quantity,
            previous_quantity=previous_qty,
            new_quantity=drug.remaining_quantity,
            notes=notes
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash(f'成功入库 {drug.name} {quantity}片！', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'入库失败：{str(e)}', 'danger')
    
    return redirect(url_for('stocks_manage'))


@app.route('/stocks/logs')
def stocks_logs():
    """扣药日志"""
    # 获取筛选参数
    drug_id = request.args.get('drug_id', '')
    change_type = request.args.get('change_type', '')
    
    query = StockRecord.query
    
    if drug_id:
        query = query.filter(StockRecord.drug_id == int(drug_id))
    
    if change_type:
        query = query.filter(StockRecord.change_type == change_type)
    
    logs = query.order_by(StockRecord.change_date.desc()).limit(100).all()
    
    drugs = Drug.query.all()
    
    return render_template('stocks/logs.html', logs=logs, drugs=drugs, 
                         selected_drug=drug_id, selected_type=change_type)


# ==================== 预警管理 ====================

@app.route('/alerts')
def alerts_list():
    """预警列表"""
    # 获取筛选参数
    alert_level = request.args.get('alert_level', '')
    is_read = request.args.get('is_read', '')
    
    query = Alert.query.filter_by(is_resolved=False)
    
    if alert_level:
        query = query.filter(Alert.alert_level == alert_level)
    
    if is_read == 'unread':
        query = query.filter(Alert.is_read == False)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    return render_template('alerts/list.html', 
                         alerts=alerts,
                         selected_level=alert_level,
                         selected_read=is_read)


@app.route('/alerts/<int:alert_id>/read', methods=['POST'])
def alert_read(alert_id):
    """标记预警为已读"""
    from services.alert_checker import mark_alert_as_read
    if mark_alert_as_read(alert_id):
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@app.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def alert_resolve(alert_id):
    """标记预警为已解决"""
    from services.alert_checker import resolve_alert
    if resolve_alert(alert_id):
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


# ==================== 手动触发扣药（测试用） ====================

@app.route('/admin/deduct', methods=['POST'])
def manual_deduct():
    """手动触发扣药（仅用于测试）"""
    try:
        auto_deduct_daily_medication()
        flash('手动扣药执行成功！', 'success')
    except Exception as e:
        flash(f'扣药失败：{str(e)}', 'danger')
    
    return redirect(url_for('index'))


# ==================== API接口 ====================

@app.route('/api/stats')
def api_stats():
    """获取统计信息API"""
    stats = {
        'total_drugs': Drug.query.count(),
        'active_drugs': Drug.query.filter(Drug.remaining_quantity > 0).count(),
        'alerts': get_alerts_summary(),
        'out_of_stock': Drug.query.filter(Drug.remaining_quantity == 0).count()
    }
    return jsonify(stats)


@app.route('/api/drugs')
def api_drugs():
    """获取药品列表API"""
    drugs = Drug.query.all()
    return jsonify([d.to_dict() for d in drugs])


# ==================== 初始化数据库 ====================

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("数据库初始化完成！")


# ==================== 启动应用 ====================

if __name__ == '__main__':
    # 创建instance目录（如果不存在）
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    
    # 初始化数据库
    init_db()
    
    # 启动开发服务器
    app.run(debug=True, host='0.0.0.0', port=5000)
