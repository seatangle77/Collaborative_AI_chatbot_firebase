from fastapi import APIRouter

# 导入各子模块路由
from .users import router as users_router
# 后续你也可以加入更多，比如：
from .groups import router as groups_router
from .chat import router as chat_router
from .ai_bots import router as ai_bots_router
from .agent import router as agent_router
from .insights import router as insights_router



# 创建主路由对象
router = APIRouter()

# 注册子路由
router.include_router(users_router)
router.include_router(groups_router)
router.include_router(chat_router)
router.include_router(ai_bots_router)
router.include_router(agent_router)
router.include_router(insights_router)