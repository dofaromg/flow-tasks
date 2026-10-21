"""
Ultimate AI Video System - Main FastAPI Service
完整的小影AI終極版主服務
"""

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
import uvicorn
from pathlib import Path
import asyncio
import yaml
import sys

# 添加當前目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent))

from utils.gpu_orchestrator import get_orchestrator
from utils.memory_manager import get_memory_manager
from utils.model_cache import get_model_cache
from ultimate_engines.digital_human_ultra import create_digital_human_engine, DigitalHumanConfig
from ultimate_engines.voice_clone_unlimited import create_voice_clone_engine, VoiceCloneConfig

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="Ultimate AI Video System",
    description="小影AI終極版 - 家庭專用AI視頻生成系統",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態文件
static_dir = Path(__file__).parent / "web_ultimate"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 全局變量
orchestrator = None
memory_manager = None
model_cache = None
family_users = {}
active_websockets = []


# Pydantic模型
class UserInfo(BaseModel):
    user_id: str
    priority: int = 5
    
class DigitalHumanRequest(BaseModel):
    user_id: str
    resolution: str = "4k"
    fps: int = 60
    quality: str = "balanced"
    enable_blink: bool = True
    enable_micro_expressions: bool = True
    enable_breathing: bool = True

class VoiceCloneRequest(BaseModel):
    user_id: str
    text: str
    model: str = "f5_tts_v2"
    language: str = "zh"
    emotion: str = "neutral"
    speed: float = 1.0

class SystemStatus(BaseModel):
    status: str
    gpu_count: int
    total_memory_gb: float
    available_memory_gb: float
    cached_models: int
    active_users: int


@app.on_event("startup")
async def startup_event():
    """啟動時初始化"""
    global orchestrator, memory_manager, model_cache, family_users
    
    logger.info("🚀 Starting Ultimate AI Video System...")
    
    # 初始化核心組件
    orchestrator = get_orchestrator()
    memory_manager = get_memory_manager()
    model_cache = get_model_cache()
    
    # 加載家庭用戶配置
    family_users = load_family_users()
    logger.info(f"Loaded {len(family_users)} family users")
    
    # 預加載模型（如果配置啟用）
    # 注意：實際部署時這裡會加載真實模型
    logger.info("Model preloading skipped (using placeholder models)")
    
    # 監控GPU健康
    orchestrator.monitor_gpu_health()
    
    logger.info("✅ System initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """關閉時清理"""
    logger.info("🛑 Shutting down Ultimate AI Video System...")
    
    # 清理WebSocket連接
    for ws in active_websockets:
        try:
            await ws.close()
        except:
            pass
    
    logger.info("✅ System shutdown complete")


def load_family_users() -> Dict:
    """加載家庭用戶配置"""
    try:
        config_path = Path("configs/family_users.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                users = {}
                for user in config.get('users', []):
                    users[user['id']] = user
                return users
    except Exception as e:
        logger.error(f"Failed to load family users: {e}")
    
    # 返回默認用戶
    return {
        'admin': {
            'id': 'admin',
            'name': '管理員',
            'priority': 10,
            'role': 'admin'
        }
    }


def get_user_priority(user_id: str) -> int:
    """獲取用戶優先級"""
    user = family_users.get(user_id)
    if user:
        return user.get('priority', 5)
    return 5


@app.get("/")
async def root():
    """首頁"""
    html_file = Path("web_ultimate/index.html")
    if html_file.exists():
        return FileResponse(html_file)
    return {"message": "Ultimate AI Video System API"}


@app.get("/api/status")
async def get_status() -> SystemStatus:
    """獲取系統狀態"""
    memory_stats = memory_manager.get_memory_stats()
    cache_stats = model_cache.get_cache_stats()
    
    return SystemStatus(
        status="running",
        gpu_count=orchestrator.num_gpus,
        total_memory_gb=memory_stats.total,
        available_memory_gb=memory_stats.available,
        cached_models=cache_stats['total_models'],
        active_users=len(family_users)
    )


@app.get("/api/users")
async def get_users():
    """獲取家庭成員列表"""
    return {
        "users": list(family_users.values())
    }


@app.get("/api/gpu-status")
async def get_gpu_status():
    """獲取GPU狀態"""
    gpu_statuses = []
    for i in range(orchestrator.num_gpus):
        try:
            status = orchestrator.get_gpu_status(i)
            gpu_statuses.append({
                'gpu_id': status.gpu_id,
                'name': status.name,
                'memory_total_gb': round(status.memory_total, 2),
                'memory_used_gb': round(status.memory_used, 2),
                'memory_free_gb': round(status.memory_free, 2),
                'utilization': round(status.utilization * 100, 1),
                'temperature': status.temperature
            })
        except Exception as e:
            logger.error(f"Failed to get GPU {i} status: {e}")
    
    return {"gpus": gpu_statuses}


@app.post("/api/digital-human/generate")
async def generate_digital_human(
    request: DigitalHumanRequest,
    image: UploadFile = File(...),
    audio: UploadFile = File(...)
):
    """
    生成數字人視頻
    
    - **user_id**: 用戶ID
    - **image**: 人物照片
    - **audio**: 語音文件
    - **resolution**: 分辨率 (720p, 1080p, 4k, 8k)
    - **fps**: 幀率 (30, 60, 120)
    - **quality**: 質量 (fast, balanced, high, ultra)
    """
    try:
        # 獲取用戶優先級
        priority = get_user_priority(request.user_id)
        
        # 創建引擎
        engine = create_digital_human_engine(
            resolution=request.resolution,
            fps=request.fps,
            quality=request.quality,
            user_priority=priority
        )
        
        # 保存上傳的文件
        upload_dir = Path(f"workspaces/{request.user_id}/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = upload_dir / image.filename
        audio_path = upload_dir / audio.filename
        
        with open(image_path, "wb") as f:
            f.write(await image.read())
        
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
        
        # 生成數字人
        output_dir = Path(f"workspaces/{request.user_id}/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"digital_human_{int(asyncio.get_event_loop().time())}.mp4"
        
        result = engine.generate(
            image_path=str(image_path),
            audio_path=str(audio_path),
            output_path=str(output_path)
        )
        
        if result.success:
            return {
                "success": True,
                "video_url": f"/workspaces/{request.user_id}/outputs/{output_path.name}",
                "duration": result.duration,
                "resolution": result.resolution,
                "fps": result.fps,
                "processing_time": result.processing_time
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)
            
    except Exception as e:
        logger.error(f"Digital human generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-clone/generate")
async def clone_voice(
    request: VoiceCloneRequest,
    reference_audio: UploadFile = File(...)
):
    """
    克隆聲音並生成語音
    
    - **user_id**: 用戶ID
    - **reference_audio**: 參考音頻 (30秒-10分鐘)
    - **text**: 要合成的文本
    - **model**: 模型 (f5_tts_v2, cosyvoice, gpt_sovits_v2, xtts_v3)
    - **language**: 語言 (zh, en, ja, ko, multi)
    - **emotion**: 情感 (neutral, happy, sad, angry, excited)
    """
    try:
        # 獲取用戶優先級
        priority = get_user_priority(request.user_id)
        
        # 創建引擎
        engine = create_voice_clone_engine(
            model=request.model,
            language=request.language,
            emotion=request.emotion,
            user_priority=priority
        )
        
        # 保存上傳的文件
        upload_dir = Path(f"workspaces/{request.user_id}/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        reference_path = upload_dir / reference_audio.filename
        with open(reference_path, "wb") as f:
            f.write(await reference_audio.read())
        
        # 克隆聲音
        output_dir = Path(f"workspaces/{request.user_id}/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"cloned_voice_{int(asyncio.get_event_loop().time())}.wav"
        
        result = engine.clone_voice(
            reference_audio_path=str(reference_path),
            text=request.text,
            output_path=str(output_path)
        )
        
        if result.success:
            return {
                "success": True,
                "audio_url": f"/workspaces/{request.user_id}/outputs/{output_path.name}",
                "duration": result.duration,
                "sample_rate": result.sample_rate,
                "processing_time": result.processing_time
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)
            
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket實時狀態更新"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # 發送GPU狀態
            gpu_statuses = []
            for i in range(orchestrator.num_gpus):
                try:
                    status = orchestrator.get_gpu_status(i)
                    gpu_statuses.append({
                        'gpu_id': i,
                        'utilization': round(status.utilization * 100, 1),
                        'memory_used': round(status.memory_used, 2)
                    })
                except:
                    pass
            
            # 發送記憶體狀態
            memory_stats = memory_manager.get_memory_stats()
            
            await websocket.send_json({
                'type': 'status_update',
                'gpus': gpu_statuses,
                'memory': {
                    'used_gb': round(memory_stats.used, 2),
                    'available_gb': round(memory_stats.available, 2),
                    'percent': round(memory_stats.percent, 1)
                }
            })
            
            await asyncio.sleep(2)  # 每2秒更新一次
            
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_websockets.remove(websocket)


if __name__ == "__main__":
    # 啟動服務
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
