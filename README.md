# 药品管理系统

一个免费的云端药品管理系统，支持自动扣药和智能预警。

## 功能特性

✅ 药品列表、详情查看  
✅ 新增/编辑药品  
✅ 库存管理（入库操作）  
✅ 过期预警  
✅ 库存不足预警（提前15天）  
✅ **每天自动扣药**（核心功能）

## 技术栈

- **后端**: Flask 3.0
- **数据库**: SQLite（本地）/ PostgreSQL（云端）
- **定时任务**: APScheduler + Render Cron Job
- **前端**: Bootstrap 5 + jQuery
- **部署**: Render.com（免费）

## 本地开发

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python app.py
```

首次运行会自动创建数据库。

### 3. 启动开发服务器

```bash
python app.py
```

访问 http://localhost:5000

## 云端部署（Render.com）

### 步骤1: 创建GitHub仓库

1. 登录 GitHub
2. 创建新仓库：`medicine-manager`
3. 不要添加README、.gitignore或license

### 步骤2: 推送代码到GitHub

```bash
cd C:\Users\Administrator\.qclaw\workspace-agent-16f6b948\medicine-manager
git init
git add .
git commit -m "Initial commit: 药品管理系统"
git branch -M main
git remote add origin https://github.com/你的用户名/medicine-manager.git
git push -u origin main
```

### 步骤3: 在Render创建应用

1. 登录 https://render.com
2. 点击 "New +" → "Blueprint"
3. 连接GitHub仓库：`medicine-manager`
4. Render会自动检测`render.yaml`配置
5. 点击 "Apply" 开始部署

### 步骤4: 等待部署完成

- Web服务部署：约3-5分钟
- Cron Job配置：自动创建
- 访问地址：`https://medicine-manager.onrender.com`

## 自动扣药说明

系统会在每天**凌晨00:05**自动执行扣药任务：

1. 遍历所有活跃药品（剩余量 > 0）
2. 按每日用量自动扣除库存
3. 记录扣药日志
4. 检查库存和过期预警
5. 如有问题，创建预警通知

**注意**：Render免费套餐会在15分钟无访问后休眠，但Cron Job不受影响，仍会按时执行。

## 预警规则

### 库存不足预警（提前15天）

- 🔴 已用完：库存为0
- 🔴 严重不足：剩余 ≤ 3天
- 🟠 库存紧张：剩余 ≤ 7天
- 🟡 库存不足：剩余 ≤ 15天

### 过期预警

- 🔴 已过期：已超过有效期
- 🟠 即将过期：30天内过期
- 🟡 注意有效期：90天内过期

## 项目结构

```
medicine-manager/
├── app.py              # Flask主应用
├── models.py           # 数据库模型
├── scheduler.py        # 定时任务配置
├── cron_jobs.py        # Cron Job入口
├── requirements.txt    # 依赖列表
├── render.yaml         # Render部署配置
├── runtime.txt         # Python版本
├── templates/          # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── drugs/
│   ├── stocks/
│   └── alerts/
├── static/             # 静态文件
│   ├── css/
│   └── js/
├── services/           # 业务逻辑
│   ├── auto_deduct.py
│   └── alert_checker.py
└── instance/           # 数据库文件
    └── medicine.db
```

## 常见问题

### Q: 免费套餐有限制吗？

A: Render免费套餐：
- 750小时/月（足够24小时运行）
- 15分钟无访问会休眠（首次访问需等待10秒唤醒）
- Cron Job免费支持

### Q: 数据会丢失吗？

A: SQLite数据存储在应用容器中，重新部署会丢失数据。建议：
- 定期导出数据（通过API）
- 或使用Render的PostgreSQL（免费）

### Q: 如何导入现有数据？

A: 启动后，通过Web界面手动添加，或联系开发者编写导入脚本。

## 技术支持

- 开发者：土豆 🥔
- 部署平台：Render.com
- 开发时间：2026-05-15

## 许可证

MIT License
