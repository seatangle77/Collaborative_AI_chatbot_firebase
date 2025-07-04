# Collaborative_AI_chatbot

# 用户操作指南（README）

## 项目简介

本系统为小组协作与AI智能分析平台，支持行为数据采集、语音识别、异常分析、实时推送和协作笔记等功能。  
**管理员已为你配置好所有后台服务和插件，你只需关注前端网页的使用。**

---

## 1. 插件安装（仅需一次）

管理员会提供一个浏览器插件（TabBehavior Extension）压缩包或文件夹。

**安装步骤：**
1. 打开 Chrome 浏览器，访问 `chrome://extensions/`
2. 开启右上角"开发者模式"
3. 点击"加载已解压的扩展程序"，选择管理员发给你的插件文件夹
4. 安装完成后，右上角会出现插件图标

> 插件自动采集你的网页行为数据，无需手动操作。请勿随意关闭或卸载。

---

## 2. 语音识别说明

### 2.1 语音识别前的准备

- **首次使用前**，每位用户需用手机或电脑录制一段**20秒左右的清晰语音**（内容不限，普通说话即可）。
- 将录音文件（建议格式：wav/mp3，文件名为"姓名+用户ID"）发送给管理员。
- 管理员会将你的音频样本配置到系统中，以提升语音识别的准确率。
- 只有完成此步骤后，系统才能准确识别你的发言内容。

- 语音识别由管理员统一在会议现场或后台运行，无需用户手动操作。
- 你只需正常发言，系统会自动识别并分析你的语音内容。

---

## 3. 前端网页功能与操作指引

### 3.1 登录与进入

- 打开管理员提供的网址（如 http://xxx.xxx:5173）
- 使用分配的账号登录，进入个人工作区

---

### 3.2 页面主要功能区

#### 1）顶部导航栏
- 显示当前用户信息、小组信息、会议主题等

#### 2）左侧：个人信息与协作区
- **个人信息卡**：显示你的头像、姓名、角色等
- **协作笔记**：可多人实时编辑会议笔记，自动保存
- **历史异常反馈**：可查看自己历史上的异常行为记录

#### 3）右侧：小组成员状态面板
- 显示所有小组成员的当前状态
- **异常成员**会以红色卡片高亮显示异常类型和详细描述
- **正常成员**以绿色标签显示

#### 4）下方/中部：会议议程与阶段
- 展示当前会议议程、阶段进度
- 可查看每个阶段的任务、目标和建议

---

### 3.3 典型交互流程

#### 1）会议开始
- 管理员在公共大屏页面点击"开始会议"
- 所有成员的个人页面会自动同步进入会议状态

#### 2）行为与语音采集
- 你在网页上的操作、发言、笔记编辑等会被系统自动采集和分析

#### 3）异常分析与推送
- 系统会定时分析每位成员的行为和发言
- 检测到异常（如长时间未发言、未参与协作等）会自动推送到你的页面
- 你会在右侧成员面板看到异常提示

#### 4）异常反馈与分享
- 你可以点击异常反馈卡片上的"Share"按钮，将异常信息一键分享给小组其他成员
- 其他成员会实时收到推送，并在自己的成员面板看到你的异常状态

#### 5）协作笔记
- 你可以随时在协作笔记区编辑、补充会议内容
- 所有成员的编辑会实时同步

#### 6）历史记录与自查
- 可随时查看自己的历史异常反馈，了解行为改进建议

---

### 3.4 其他说明

- **推送通知**：如你绑定了移动设备或AR眼镜，异常信息也会通过极光推送实时提醒你
- **页面自动同步**：会议阶段、议程等信息会自动同步，无需手动刷新
- **数据安全**：所有行为数据仅用于小组协作与AI分析，管理员已做好隐私保护

---

## 4. 常见问题

- **为什么要安装插件？**  
  插件用于采集网页行为数据，帮助AI更好地分析协作状态。

- **异常推送会打扰我吗？**  
  只有检测到明显异常时才会推送，帮助你及时调整参与状态。

- **协作笔记会丢失吗？**  
  不会，所有内容自动保存并实时同步。

- **我需要手动启动语音识别吗？**  
  不需要，管理员已统一配置好。

---

## 5. 联系方式

如有疑问或遇到技术问题，请联系管理员或技术支持团队。

---

**祝你协作愉快，会议高效！**

---

## 功能亮点

- **AI 协作助手**：集成大语言模型（如 GPT-4），为小组讨论提供认知引导、智能总结与知识支持。
- **实时语音识别**：支持腾讯云 ASR，自动转写会议音频，区分发言人并生成字幕。
- **异常行为检测**：自动分析用户行为数据，检测并反馈会议中的异常（如沉默、发言不均等）。
- **多端同步**：支持 Web 前端、浏览器插件、后端 API、音频采集与分析等多端协作。
- **浏览器行为采集插件**：实时采集用户网页行为（点击、滚动、切换等），辅助行为分析。
- **会议议程与任务管理**：可视化展示当前任务、议程进度，支持一键启动在线会议（Jitsi）。
- **数据可视化与反馈**：异常分析结果以图表和富文本形式展示，支持用户反馈与分享。

---

## 目录结构

```
.
├── audio_runtime/         # 语音识别与音频处理（腾讯云 ASR，分组音频、参考说话人等）
├── client/                # 前端 Vue3 + Vite 项目（主 UI、用户交互、WebSocket、API 调用等）
├── server/                # 后端 FastAPI 服务（API、WebSocket、AI分析、异常检测等）
├── tabbehavior-extension/ # 浏览器插件（用户行为采集、与主系统联动）
├── README.md              # 项目说明文档
└── ...
```

---

## 当前部署信息

### 🌐 访问地址

- **前端页面**：https://collaborative-ai-chatbot.web.app
- **后端API**：https://collaborative-backend.onrender.com
- **API文档**：https://collaborative-backend.onrender.com/docs

#### 📱 前端路由示例

**公共显示页面**（大屏展示）：
- `https://collaborative-ai-chatbot.web.app/#/public-display/Group%20G`
- `https://collaborative-ai-chatbot.web.app/#/public-display/Group%20B`

**个人工作台**（用户个人页面）：
- `https://collaborative-ai-chatbot.web.app/#/personal-dashboard/TestUser1`
- `https://collaborative-ai-chatbot.web.app/#/personal-dashboard/TestUser2`


### 🗄️ 数据库信息

- **数据库类型**：Firebase Firestore
- **项目ID**：`collaborative-ai-chatbot`
- **Firebase控制台**：https://console.firebase.google.com/project/collaborative-ai-chatbot
- **主要集合**：
  - `users_info` - 用户信息
  - `groups` - 小组信息
  - `chat_messages` - 聊天记录
  - `speech_transcripts` - 语音转写记录
  - `discussion_core` - 讨论核心数据
  - `anomaly_analysis_results` - 异常分析结果

---

## 各模块部署与启动方式

### 1. 后端服务（server）

- **依赖安装**  
  ```bash
  cd server
  pip install -r requirements.txt
  ```
- **环境变量**  
  - `.env` 文件需配置 Firebase、JPush、AI API 等密钥（参考 `.env.example`）。
  - 需有 `firebase-key.json`（Firebase 服务账号密钥）。
- **启动服务**  
  ```bash
  uvicorn app.main:app --reload
  ```
  默认监听端口：8000

- **生产部署**  
  可用 Render、Docker、云服务器等，参考 `render.yaml`。

### 2. 前端项目（client）

- **依赖安装**  
  ```bash
  cd client
  npm install
  ```
- **环境变量**  
  - `.env` 文件需配置 VITE_API_BASE、VITE_WS_BASE、Firebase 等。
- **本地开发**  
  ```bash
  npm run dev
  ```
  默认监听端口：3000

- **生产构建**  
  ```bash
  npm run build
  ```
  构建产物在 `client/dist`，可配合 Firebase Hosting 或其他静态服务器部署。

### 3. 浏览器插件（tabbehavior-extension）

- **依赖安装与构建**  
  ```bash
  cd tabbehavior-extension
  npm install
  npm run build
  ```
- **加载插件**  
  1. 打开 Chrome 扩展管理页面 `chrome://extensions`
  2. 开启开发者模式
  3. "加载已解压的扩展程序"，选择 `tabbehavior-extension/dist` 目录

- **环境变量**  
  - `.env` 文件需配置 Firebase 相关参数（如 API KEY 等）

### 4. 语音识别与音频处理（audio_runtime）

- **依赖安装**  
  ```bash
  pip install pyaudio websocket-client
  ```
- **配置**  
  - 配置腾讯云 ASR 相关密钥
  - `config/` 目录下为各小组的分组配置
  - `groups/` 目录下为各小组的参考音频
- **使用**  
  - 运行 `list_audio_devices.py` 查看可用音频输入设备
  - 运行自定义脚本进行音频采集、识别与分组管理

### 5. 语音识别启动命令（手动配置）

```bash
# 设置代理（如需要）
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

# 激活虚拟环境
source newenv/bin/activate

# 启动语音识别（指定小组和设备）
python asr_record.py --group groupB --device 2
python asr_record.py --group groupG --device 2
```

**参数说明**：
- `--group`：指定小组名称（groupA、groupB、groupC、groupD、groupG）
- `--device`：指定音频设备索引（通过 `list_audio_devices.py` 查看）

---

## 后端 API 接口说明（部分）

### 用户相关

- `GET /api/users/`  
  获取所有用户信息

- `GET /api/users/{user_id}`  
  获取指定用户信息

- `PUT /api/users/{user_id}`  
  更新用户信息（name, academic_background, academic_advantages, device_token）

### 小组相关

- `GET /api/groups/`  
  获取所有小组信息

- `GET /api/groups/{group_id}`  
  获取指定小组详细信息

- `GET /api/groups/{group_id}/members`  
  获取指定小组成员列表

- `PUT /api/groups/{group_id}`  
  更新小组信息（名称、目标等）

- `GET /api/user/{user_id}/group-context`  
  获取用户所在小组、成员、session、AI Bot 等上下文信息

### 聊天与议程

- `GET /api/chat/{group_id}`  
  获取指定小组的聊天历史记录

- `GET /api/sessions/{group_id}`  
  获取指定小组当前活跃 session

- `GET /api/chat/agenda/session/{session_id}`  
  获取指定 session 下的所有议程项

- `POST /api/chat/agenda`  
  新增议程项

- `PATCH /api/chat/agenda/reset_status/{group_id}?stage=1`  
  批量更新议程状态（not_started/in_progress/completed）

### AI Bot 管理

- `GET /api/ai_bots`  
  获取所有 AI Bot

- `GET /api/ai_bots/{bot_id}`  
  获取指定 AI Bot 信息

- `GET /api/ai_bots/group/{group_id}`  
  获取指定小组的 AI Bot

- `PUT /api/ai_bots/{bot_id}/model`  
  更新 AI Bot 的模型

### 异常分析与反馈

- `POST /analysis/anomalies`  
  提交行为数据，获取异常分析结果  
  **请求体**（示例）：
  ```json
  {
    "group_id": "xxx",
    "round_index": 1,
    "start_time": "2025-07-01T10:00:00",
    "end_time": "2025-07-01T10:05:00",
    "members": [{"id": "user1", "name": "张三"}, ...],
    "current_user": {
      "user_id": "user1",
      "name": "张三",
      "device_token": "xxxx"
    }
  }
  ```
  **返回**：异常分析结果、摘要、详细建议等

- `GET /analysis/anomaly_results_by_user?user_id=xxx&page=1&page_size=10`  
  分页获取用户历史异常分析结果

- `POST /analysis/anomaly_polling/feedback_click`  
  记录异常反馈点击（如"更少提示""分享"等）

---

## WebSocket 接口说明

- `ws://<server>/ws/{group_id}`  
  小组级 WebSocket，推送议程进度、AI 分析等实时消息

- `ws://<server>/ws/user/{user_id}`  
  用户级 WebSocket，推送个人异常分析、分享等消息

**消息类型举例**：
- `agenda_stage_update`：议程阶段变更
- `share`：异常分析结果分享
- `anomaly_analysis`：推送异常分析结果

---

## 依赖与环境变量

### 后端（server/requirements.txt）

- fastapi
- uvicorn
- python-dotenv
- websockets
- openai
- google-generativeai
- firebase-admin
- jpush
- apscheduler
- 其它

### 前端（client/package.json）

- vue
- element-plus
- axios
- quill
- echarts
- 其它

### 插件（tabbehavior-extension/package.json）

- vue
- element-plus
- firebase
- 其它

### 语音识别

- pyaudio
- websocket-client

### 主要环境变量

#### 后端环境变量（server/.env）
```bash
# Firebase 配置
FIREBASE_KEY_JSON={"type":"service_account",...}  # Firebase 服务账号密钥 JSON
GOOGLE_APPLICATION_CREDENTIALS=./firebase-key.json

# AI API 配置
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1
GEMINI_API_KEY=...

# JPush 推送配置
JPUSH_APP_KEY=...
JPUSH_MASTER_SECRET=...

# 环境配置
ENV=development  # 或 production
```

#### 前端环境变量（client/.env）
```bash
# API 配置
VITE_API_BASE=https://collaborative-ai-chatbot.onrender.com
VITE_WS_BASE=wss://collaborative-ai-chatbot.onrender.com

# Firebase 配置
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=collaborative-ai-chatbot.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=collaborative-ai-chatbot
VITE_FIREBASE_STORAGE_BUCKET=collaborative-ai-chatbot.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

#### 语音识别配置（audio_runtime/.env）
```bash
# 腾讯云 ASR 配置
TENCENT_SECRET_ID=...
TENCENT_SECRET_KEY=...
TENCENT_APP_ID=...
```

---

## 常见问题与开发建议

### 🔧 开发调试

- **接口文档**：建议用 Postman 或 Swagger UI 进行调试，FastAPI 默认支持 `/docs` 文档页面。
- **数据库**：默认使用 Firebase Firestore，需提前配置好密钥。
- **WebSocket**：前后端需保持协议一致，生产环境建议使用 wss。
- **音频识别**：需提前开通腾讯云 ASR 服务，配置好密钥与音频设备。
- **插件与主系统联动**：通过 Chrome Storage、消息机制与主系统同步用户信息与行为数据。

### 🚀 部署相关

- **Firebase Hosting**：前端已配置自动部署到 Firebase Hosting
- **Render 部署**：后端已配置自动部署到 Render 平台
- **环境变量**：生产环境请使用环境变量而非 `.env` 文件
- **CORS 配置**：后端已配置允许的域名列表，新增域名需更新 `server/app/main.py`

### 🔒 安全建议

- **密钥管理**：生产环境请勿泄露密钥，使用环境变量或密钥管理服务
- **HTTPS 部署**：生产环境必须使用 HTTPS
- **权限控制**：Firebase 安全规则需正确配置
- **API 限流**：考虑添加 API 调用频率限制

### 📊 监控与日志

- **Firebase Analytics**：前端已集成用户行为分析
- **日志记录**：后端使用 Python logging，语音识别有独立日志文件
- **错误监控**：建议集成 Sentry 等错误监控服务

---

## 贡献与支持

欢迎提交 Issue 和 PR，建议先阅读各子目录下的 README 或代码注释。  
如有问题或合作意向，请联系项目维护者或在 GitHub 提 Issue。

---

如需更详细的模块说明或接口文档，请查阅各子目录下的代码与注释，或联系开发者获取更详细的技术文档。

---

如需英文版或更详细的接口示例，也可以告知我！
