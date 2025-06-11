from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router  # 导入所有的 API 路由
from app.websocket_routes import websocket_router  # 导入 WebSocket 路由

# ✅ 创建 FastAPI 实例
app = FastAPI()

# ✅ 允许的前端源
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.50.246:3000",
    "https://localhost:3000",
    "https://192.168.50.246:3000",
    "http://10.4.153.143:3000",
    "https://10.4.153.143:3000",
    "https://10.4.131.51:3000",
    "https://collaborative-ai-chatbot.web.app",
]

# ✅ 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 🚀 允许特定来源
    allow_credentials=True,  # 🚀 允许携带 Cookie/session
    allow_methods=["*"],  # 🚀 允许所有 HTTP 方法（GET, POST, OPTIONS, PUT, DELETE）
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Headers"],  # 🚀 明确允许 Content-Type
)

# ✅ WebSocket 需要手动添加 CORS 允许
@app.middleware("http")
async def websocket_cors_middleware(request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# ✅ 处理 OPTIONS 预检请求，防止 CORS 拦截 POST 请求
@app.options("/api/chat/send/")
async def options_handler(request: Request):
    origin = request.headers.get("origin")
    headers = {
        "Access-Control-Allow-Methods": "POST, GET, PUT, DELETE, PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Credentials": "true"
    }
    if origin in origins:
        headers["Access-Control-Allow-Origin"] = origin
    return Response(status_code=204, headers=headers)

# ✅ 注册 API 路由
app.include_router(router)

# ✅ 注册 WebSocket 路由
app.include_router(websocket_router)

# ✅ 根路径测试 API
@app.get("/")
async def root():
    return {"message": "Welcome to Collaborative AI Chatbot API with WebSocket!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

# Note: To adapt the WebSocket connection protocol for different environments,
# update the frontend WebSocket initialization logic as follows:
#
# const WS_BASE = window.location.protocol === "https:" ? "wss" : "ws";
# const socket = new WebSocket(`${WS_BASE}://${window.location.host}/ws/${groupId}`);
#
# This ensures that in development (http) the connection uses ws://,
# and in production (https) it uses wss:// without any backend changes.
# Just make sure your backend is deployed with HTTPS/WSS support.