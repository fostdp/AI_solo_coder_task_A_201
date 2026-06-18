# 古代失蜡法精密铸造充型仿真与缺陷预测系统

> 曾侯乙尊盘失蜡法工艺复原研究数字化仿真平台

## 目录

- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [模块说明](#模块说明)
- [快速开始](#快速开始)
- [部署方式](#部署方式)
- [模拟器使用](#模拟器使用)
- [API 文档](#api-文档)
- [配置说明](#配置说明)

## 系统架构

```
┌───────────────────────────────────────────────────────────────────┐
│                        前端 (React + Three.js)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ lost_wax_3d │  │defect_panel │  │  WebSocket Client        │  │
│  │  (3D可视化) │  │ (缺陷面板)  │  │  (实时数据推送)          │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────────┬───────────┘  │
└─────────┼────────────────┼────────────────────────┼──────────────┘
          │                │                        │
          └────────────────┼────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Nginx     │  (Gzip压缩, 反向代理, 静态资源)
                    └──────┬──────┘
                           │
┌──────────────────────────┼───────────────────────────────────────────┐
│       后端 (FastAPI + gunicorn + uvicorn workers)                    │
│                          │                                            │
│                    API Gateway (main.py)                              │
│                          │                                            │
│  ┌──────────────┐ ┌─────▼──────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ dtu_receiver │ │filling_sim │ │defect_predict│ │  alarm_ws    │  │
│  │ (传感器采集) │ │ (CFD+传热) │ │ (Niyama判据) │ │ (告警推送)   │  │
│  └──────┬───────┘ └─────┬──────┘ └──────┬───────┘ └──────┬───────┘  │
│         │                │                │                 │          │
│         └────────────────▼────────────────▼─────────────────┘          │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │              Redis Pub/Sub 消息总线                       │         │
│  │  sensor_data → filling_result → heat_result → niyama_result         │
│  │              → defect_result → alerts                              │
│  └──────────────────────────────────────────────────────────┘         │
│                          │                                            │
│  ┌───────────────────────┴────────────────────┐ ┌───────────────┐   │
│  │          MongoDB (副本集)                   │ │  MQTT Broker  │   │
│  │  castings / sensors / simulations / defects│ │  (EMQX)       │   │
│  │  / alerts                                   │ │               │   │
│  └─────────────────────────────────────────────┘ └───────┬───────┘   │
│                                                          │           │
└──────────────────────────────────────────────────────────┼───────────┘
                                                           │
                                                ┌──────────▼──────────┐
                                                │  失蜡法铸造模拟器   │
                                                │  (casting_simulator)│
                                                └─────────────────────┘
```

## 技术栈

### 后端
- **框架**: FastAPI 0.108.0
- **Web服务器**: gunicorn 22.0 + uvicorn 0.27
- **数据库**: MongoDB 7.0 (副本集)
- **消息总线**: Redis 7.2 (Pub/Sub)
- **消息队列**: EMQX 5.7 (MQTT)
- **数值计算**: NumPy, SciPy
- **数据验证**: Pydantic v2

### 前端
- **框架**: React 18 + TypeScript
- **3D渲染**: Three.js
- **图表**: ECharts
- **状态管理**: Zustand
- **构建工具**: Vite
- **静态服务**: Nginx (带Gzip压缩)

## 模块说明

### 后端模块

| 模块 | 路径 | 职责 |
|------|------|------|
| **dtu_receiver** | `backend/dtu_receiver/` | 传感器数据采集、校验、MQTT接收 |
| **filling_simulator** | `backend/filling_simulator/` | AMR网格CFD、传热计算、凝固仿真 |
| **defect_predictor** | `backend/defect_predictor/` | Niyama判据计算、缩孔缩松分析、聚类 |
| **alarm_ws** | `backend/alarm_ws/` | 告警规则引擎、WebSocket实时推送 |
| **common** | `backend/common/` | 配置加载、Redis消息总线、MongoDB客户端、仓储层 |

### 前端模块

| 模块 | 路径 | 职责 |
|------|------|------|
| **lost_wax_3d** | `src/lib/lost_wax_3d.ts` | Three.js场景、缺陷投影、粒子动画、温度可视化 |
| **defect_panel** | `src/lib/defect_panel.ts` | 缺陷排序、统计计算、Niyama直方图数据 |

## 快速开始

### 前置要求

- Docker 24.0+
- Docker Compose v2+
- 至少 4GB 可用内存

### 一键启动

```bash
# 克隆项目后，在项目根目录执行
docker compose up -d
```

等待所有服务启动后：
- **前端**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **MQTT控制台**: http://localhost:18083 (默认 admin/public)

### 启动模拟器

```bash
# 启动默认配置的模拟器（青铜 + 硅溶胶型壳）
docker compose --profile simulator up simulator

# 或自定义参数
docker compose --profile simulator run --rm simulator \
    --alloy stainless_steel \
    --shell ethyl_silicate \
    --pouring-temp 1600 \
    --steps 100 \
    --interval 2
```

## 部署方式

### Docker Compose 部署（推荐）

```bash
# 生产环境启动
docker compose -f docker-compose.yml up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 停止服务
docker compose down

# 停止并清除数据卷（慎用）
docker compose down -v
```

### 环境变量配置

可以在项目根目录创建 `.env` 文件来自定义配置：

```env
# 数据库
MONGODB_URL=mongodb://mongodb:27017/?replicaSet=rs0
DATABASE_NAME=lost_wax_casting

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# MQTT
MQTT_HOST=mqtt
MQTT_PORT=1883
MQTT_TOPIC=lwc/sensor/data/#

# 后端服务
GUNICORN_WORKERS=4
LOG_LEVEL=info

# API地址（模拟器用）
API_BASE_URL=http://backend:8000
```

### 独立模块部署

每个后端模块都可以独立部署为微服务：

```bash
# 仅启动 DTU Receiver
cd backend/dtu_receiver
python main.py

# 仅启动 Filling Simulator
cd backend/filling_simulator
python main.py
```

各模块通过 Redis Pub/Sub 通信，确保连接同一个 Redis 实例即可。

## 模拟器使用

### 命令行参数

```bash
python simulator/casting_simulator.py [选项]
```

#### 基础选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--api` | `http://localhost:8000` | 后端API地址 |
| `--interval` | `3` | 数据上报间隔（秒） |
| `--steps` | `60` | 总仿真步数 |
| `--fast` | - | 快速模式（无延迟） |
| `--casting-id` | 自动生成 | 指定铸造任务ID |

#### 合金材料选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--alloy` | `bronze_cu_sn` | 合金类型 |
| `--pouring-temp` | 自动 | 自定义浇铸温度 (°C) |
| `--list-alloys` | - | 列出所有可用合金 |

**可用合金类型：**

| 类型标识 | 名称 | 标准浇铸温度 |
|----------|------|-------------|
| `bronze_cu_sn` | 青铜 Cu-Sn 12% Pb 2% | 1180°C |
| `brass` | 黄铜 Cu-Zn 30% | 1060°C |
| `stainless_steel` | 不锈钢 304 | 1580°C |
| `cast_iron` | 灰口铸铁 HT200 | 1350°C |
| `aluminum_alloy` | 铝合金 A356 | 720°C |

#### 型壳条件选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--shell` | `silica_sol` | 型壳材料 |
| `--shell-layers` | 自动 | 自定义型壳层数 |
| `--wax-temp` | `60.0` | 蜡模初始温度 (°C) |
| `--list-shells` | - | 列出所有可用型壳材料 |

**可用型壳材料：**

| 类型标识 | 名称 | 标准层数 | 透气度基准 | 热导率 |
|----------|------|---------|-----------|--------|
| `silica_sol` | 硅溶胶+石英砂 | 9层 | 50% | 1.2 W/(m·K) |
| `water_glass` | 水玻璃+石英砂 | 7层 | 35% | 0.8 W/(m·K) |
| `ethyl_silicate` | 硅酸乙酯+锆英砂 | 10层 | 65% | 1.5 W/(m·K) |
| `gypsum` | 石膏型 | 1层 | 20% | 0.5 W/(m·K) |

#### MQTT选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mqtt` | - | 使用MQTT上传数据 |
| `--mqtt-host` | `localhost` | MQTT Broker地址 |
| `--mqtt-port` | `1883` | MQTT Broker端口 |
| `--mqtt-topic` | `lwc/sensor/data` | MQTT主题前缀 |

#### 缺陷控制选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--defect-intensity` | `1.0` | 缺陷强度因子 (0.1-2.0) |

### 使用示例

```bash
# 1. 查看可用合金
python simulator/casting_simulator.py --list-alloys

# 2. 查看可用型壳
python simulator/casting_simulator.py --list-shells

# 3. 不锈钢 + 硅酸乙酯型壳 高温浇注
python simulator/casting_simulator.py \
    --alloy stainless_steel \
    --shell ethyl_silicate \
    --pouring-temp 1620 \
    --steps 80 \
    --interval 2

# 4. 铝合金低压铸造（低缺陷）
python simulator/casting_simulator.py \
    --alloy aluminum_alloy \
    --defect-intensity 0.3 \
    --fast

# 5. 使用MQTT上传数据
python simulator/casting_simulator.py \
    --alloy bronze_cu_sn \
    --mqtt \
    --mqtt-host localhost \
    --steps 120
```

### Docker方式运行

```bash
# 构建模拟器镜像
docker build -f Dockerfile.simulator -t lwc-simulator .

# 运行
docker run --rm --network host lwc-simulator \
    --alloy brass \
    --shell water_glass \
    --pouring-temp 1080
```

## API 文档

启动服务后访问 Swagger UI:
- http://localhost:8000/docs

### 主要API端点

| 类别 | 端点 | 方法 | 说明 |
|------|------|------|------|
| **铸造任务** | `/api/castings` | GET | 获取铸造任务列表 |
| | `/api/castings` | POST | 创建铸造任务 |
| | `/api/castings/{id}` | GET | 获取任务详情 |
| **传感器** | `/api/sensor/data` | POST | 上传传感器数据 |
| | `/api/sensor/latest/{casting_id}` | GET | 获取最新数据 |
| | `/api/sensor/history/{casting_id}` | GET | 获取历史数据 |
| **仿真** | `/api/simulation/start` | POST | 启动仿真 |
| | `/api/simulation/stop` | POST | 停止仿真 |
| | `/api/simulation/status` | GET | 仿真状态 |
| **缺陷** | `/api/defects/{casting_id}` | GET | 获取缺陷列表 |
| | `/api/defects/{casting_id}/niyama` | GET | Niyama数据 |
| **告警** | `/api/alerts` | GET | 获取告警列表 |
| | `/api/alerts/{id}/ack` | POST | 确认告警 |
| **WebSocket** | `/ws/alerts` | WS | 告警实时推送 |
| | `/ws/simulation` | WS | 仿真数据推送 |

## 配置说明

### 铸造参数配置

配置文件: `backend/config/casting_parameters.json`

```json
{
  "grid_size": [100, 100, 50],
  "time_step": 0.1,
  "total_steps": 600,
  "thermal_properties": {
    "density": 8700,
    "specific_heat": 380,
    "thermal_conductivity": 60
  },
  "pouring": {
    "default_temp": 1180,
    "min_temp": 1100,
    "max_temp": 1250
  },
  "shell": {
    "default_permeability": 0.5,
    "thickness_ratio": 0.1
  },
  "alarm_thresholds": {
    "temperature_drop_critical": 50,
    "permeability_low": 30,
    "defect_severity_high": 0.7
  }
}
```

### 判据参数配置

配置文件: `backend/config/criteria_parameters.json`

```json
{
  "niyama_thresholds": {
    "default": 1.0,
    "bronze_cu_sn": 0.8,
    "stainless_steel": 1.2,
    "aluminum_alloy": 0.5
  },
  "severity_levels": [
    {"level": "low", "min_ratio": 0.0, "max_ratio": 0.3, "label": "轻微"},
    {"level": "medium", "min_ratio": 0.3, "max_ratio": 0.6, "label": "中等"},
    {"level": "high", "min_ratio": 0.6, "max_ratio": 1.0, "label": "严重"}
  ],
  "defect_detection": {
    "min_cluster_size": 5,
    "max_defects": 50,
    "volume_threshold": 0.01
  }
}
```

### Redis/消息配置

配置文件: `backend/config/redis_config.json`

```json
{
  "host": "localhost",
  "port": 6379,
  "db": 0,
  "channels": {
    "sensor_data": "lwc:sensor:data",
    "filling_result": "lwc:filling:result",
    "heat_result": "lwc:heat:result",
    "niyama_result": "lwc:niyama:result",
    "defect_result": "lwc:defect:result",
    "alerts": "lwc:alerts",
    "simulation_control": "lwc:simulation:control"
  }
}
```

## 开发指南

### 本地开发环境

```bash
# 1. 启动依赖服务（MongoDB, Redis, MQTT）
docker compose up mongodb redis mqtt -d

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 启动后端（开发模式，热重载）
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. 启动前端
npm install
npm run dev
```

### 运行测试

```bash
# 后端单元测试
cd backend
python -m pytest tests/ -v

# 前端类型检查
npx tsc --noEmit

# 前端Lint
npm run lint
```

## 性能优化

- **后端**: gunicorn多worker + uvicorn异步 + Redis消息解耦
- **前端**: Nginx Gzip压缩 + 静态资源缓存 + Three.js GPU渲染
- **数据库**: MongoDB副本集 + 索引优化 + TTL自动清理
- **通信**: MQTT低延迟 + WebSocket实时推送

## 故障排查

### MongoDB副本集未初始化

```bash
# 手动初始化副本集
docker compose exec mongodb mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [{ _id: 0, host: "mongodb:27017" }]
})'
```

### Redis连接失败

```bash
# 检查Redis状态
docker compose exec redis redis-cli ping

# 查看Redis日志
docker compose logs redis
```

### MQTT连接不上

```bash
# 检查EMQX状态
docker compose exec mqtt emqx ctl status

# 访问控制台: http://localhost:18083 (admin/public)
```

## 许可证

本项目用于学术研究和教育目的。

## 参考文献

- Niyama criterion for shrinkage prediction
- AMR (Adaptive Mesh Refinement) CFD methods
- Lost-wax casting process simulation
