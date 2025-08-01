from fastapi import APIRouter, HTTPException, Body, Query
from server.app.database import db
from typing import Optional

router = APIRouter()

def get_collection_by_group_id(collection_name: str, group_id: str, page: int = 1, page_size: int = 20):
    try:
        # 获取总数
        total_docs = list(db.collection(collection_name).where("group_id", "==", group_id).stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询{collection_name}失败: {str(e)}")

def get_collection_by_user_id(collection_name: str, user_id: str, page: int = 1, page_size: int = 20):
    try:
        # 获取总数
        total_docs = list(db.collection(collection_name).where("userId", "==", user_id).stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询{collection_name}失败: {str(e)}")

@router.get("/api/group_data/note_edit_history/{group_id}")
async def get_note_edit_history_by_group(
    group_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("note_edit_history").where("group_id", "==", group_id).order_by("updatedAt", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询note_edit_history失败: {str(e)}")

@router.get("/api/group_data/note_edit_history/user/{user_id}")
async def get_note_edit_history_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("note_edit_history").where("userId", "==", user_id).order_by("updatedAt", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询note_edit_history失败: {str(e)}")

@router.get("/api/group_data/note_contents/{group_id}")
async def get_note_contents_by_group(
    group_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("note_contents").where("group_id", "==", group_id).order_by("updatedAt", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询note_contents失败: {str(e)}")

@router.get("/api/group_data/note_contents/user/{user_id}")
async def get_note_contents_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("note_contents").where("userId", "==", user_id).order_by("updatedAt", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询note_contents失败: {str(e)}")

@router.get("/api/group_data/pageBehaviorLogs/user/{user_id}")
async def get_page_behavior_logs_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("pageBehaviorLogs").where("userId", "==", user_id).order_by("windowStart", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询pageBehaviorLogs失败: {str(e)}")

@router.get("/api/group_data/speech_transcripts/{group_id}")
async def get_speech_transcripts_by_group(
    group_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("speech_transcripts").where("group_id", "==", group_id).order_by("start", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询speech_transcripts失败: {str(e)}")

@router.get("/api/group_data/anomaly_analysis_results/{group_id}")
async def get_anomaly_analysis_results_by_group(
    group_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("anomaly_analysis_results").where("group_id", "==", group_id).order_by("created_at", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询anomaly_analysis_results失败: {str(e)}")

@router.delete("/api/group_data/anomaly_analysis_results/{doc_id}")
async def delete_anomaly_analysis_result(doc_id: str):
    try:
        db.collection("anomaly_analysis_results").document(doc_id).delete()
        return {"success": True, "deleted": [doc_id]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除anomaly_analysis_results失败: {str(e)}")

@router.delete("/api/group_data/anomaly_analysis_results/batch")
async def batch_delete_anomaly_analysis_results(ids: dict = Body(...)):
    deleted = []
    errors = []
    for doc_id in ids.get("ids", []):
        try:
            db.collection("anomaly_analysis_results").document(doc_id).delete()
            deleted.append(doc_id)
        except Exception as e:
            errors.append({"id": doc_id, "error": str(e)})
    if errors:
        raise HTTPException(status_code=500, detail={"deleted": deleted, "errors": errors})
    return {"success": True, "deleted": deleted} 

@router.get("/api/group_data/anomaly_analysis_group_results/{group_id}")
async def get_anomaly_analysis_group_results_by_group(
    group_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("anomaly_analysis_group_results").where("group_id", "==", group_id).order_by("created_at", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询anomaly_analysis_group_results失败: {str(e)}")

@router.delete("/api/group_data/anomaly_analysis_group_results/{doc_id}")
async def delete_anomaly_analysis_group_result(doc_id: str):
    try:
        db.collection("anomaly_analysis_group_results").document(doc_id).delete()
        return {"success": True, "deleted": [doc_id]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除anomaly_analysis_group_results失败: {str(e)}")

@router.delete("/api/group_data/anomaly_analysis_group_results/batch")
async def batch_delete_anomaly_analysis_group_results(ids: dict = Body(...)):
    deleted = []
    errors = []
    for doc_id in ids.get("ids", []):
        try:
            db.collection("anomaly_analysis_group_results").document(doc_id).delete()
            deleted.append(doc_id)
        except Exception as e:
            errors.append({"id": doc_id, "error": str(e)})
    if errors:
        raise HTTPException(status_code=500, detail={"deleted": deleted, "errors": errors})
    return {"success": True, "deleted": deleted}

@router.get("/api/group_data/local_analyze_history/{group_id}")
async def get_local_analyze_history_by_group(
    group_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("anomaly_local_analyze").where("group_id", "==", group_id).order_by("created_at", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询anomaly_local_analyze失败: {str(e)}")

@router.delete("/api/group_data/local_analyze_history/{doc_id}")
async def delete_local_analyze_history(doc_id: str):
    try:
        db.collection("anomaly_local_analyze").document(doc_id).delete()
        return {"success": True, "deleted": [doc_id]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除anomaly_local_analyze失败: {str(e)}")

@router.delete("/api/group_data/local_analyze_history/batch")
async def batch_delete_local_analyze_history(ids: dict = Body(...)):
    deleted = []
    errors = []
    for doc_id in ids.get("ids", []):
        try:
            db.collection("anomaly_local_analyze").document(doc_id).delete()
            deleted.append(doc_id)
        except Exception as e:
            errors.append({"id": doc_id, "error": str(e)})
    if errors:
        raise HTTPException(status_code=500, detail={"deleted": deleted, "errors": errors})
    return {"success": True, "deleted": deleted}

@router.get("/api/group_data/feedback_clicks/user/{user_id}")
async def get_feedback_clicks_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("feedback_clicks").where("user_id", "==", user_id).order_by("clicked_at", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询feedback_clicks失败: {str(e)}")

@router.get("/api/group_data/peer_prompts/user/{user_id}")
async def get_peer_prompts_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，最大100")
):
    try:
        # 获取总数
        total_docs = list(db.collection("peer_prompts").where("from_user_id", "==", user_id).order_by("created_at", direction="DESCENDING").stream())
        total = len(total_docs)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = total_docs[start:end]
        
        return {
            "data": [doc.to_dict() | {"id": doc.id} for doc in paginated_docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询peer_prompts失败: {str(e)}") 