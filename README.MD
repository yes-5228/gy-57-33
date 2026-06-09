# 驾校约车系统

FastAPI + Vue 3 实现的驾校约车系统，包含学员预约练车时段、教练管理、课时统计和取消规则校验。项目按前后端模块拆分，方便继续扩展数据库、认证、排班和支付等能力。

## 功能

- 学员管理：新增学员、查看剩余课时
- 教练管理：新增教练、启用/停用教练、维护车辆和擅长项目
- 练车预约：选择学员、教练、开始/结束时间创建预约
- 取消规则：默认要求开课前至少 2 小时取消，不允许取消已完成预约
- 冲突校验：同一教练同一时段不可重复预约
- 课时统计：按学员统计已完成课时、已预约课时、取消次数和剩余课时
- 运营概览：学员数、教练数、当前预约数、已完成课时和取消规则

## 项目结构

```text
.
├── backend
│   ├── app
│   │   ├── routes        # FastAPI 路由模块
│   │   ├── services      # 预约规则和统计逻辑
│   │   ├── main.py       # 应用入口
│   │   ├── models.py     # 领域模型
│   │   ├── schemas.py    # 请求/响应结构
│   │   └── store.py      # 内存数据与演示数据
│   ├── Dockerfile
│   └── requirements.txt
├── frontend
│   ├── src
│   │   ├── api           # API 请求封装
│   │   ├── components    # 通用组件
│   │   ├── utils         # 日期工具
│   │   ├── views         # 页面模块
│   │   ├── App.vue
│   │   └── main.js
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.MD
```

## Docker Compose 启动

```bash
docker compose up --build
```

启动后访问：

- 前端：http://127.0.0.1:15173
- 后端健康检查：http://127.0.0.1:18000/api/health
- API 文档：http://127.0.0.1:18000/docs

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## 说明

当前版本使用内存数据存储，服务重启后数据会重置为演示数据。生产化时建议替换为 PostgreSQL/MySQL，并增加登录鉴权、审计日志、按教练排班生成可预约时段等模块。
