import traceback

import Levenshtein
from fastapi import APIRouter, HTTPException, Body, Request
from pydantic import BaseModel, Field
from typing import Any, Dict

from server.app.logger.logger_loader import logger
from server.app.database import db

router = APIRouter()

class EditorContentRequest(BaseModel):
    user_id: str
    content: str


def describe_editops(s1, s2):
    """
    将 Levenshtein.editops 的结果转化为描述性的操作说明，连续字符合并输出
    """
    ops = Levenshtein.editops(s1, s2)
    descs = []
    if not ops:
        return descs

    # 合并连续操作
    merged = []
    prev_op, prev_i, prev_j = ops[0]
    group = [(prev_op, prev_i, prev_j)]
    for op, i, j in ops[1:]:
        if op == prev_op and (
                (op == 'insert' and j == prev_j + 1) or
                (op == 'delete' and i == prev_i + 1) or
                (op == 'replace' and i == prev_i + 1 and j == prev_j + 1)
        ):
            group.append((op, i, j))
            prev_i, prev_j = i, j
        else:
            merged.append(group)
            group = [(op, i, j)]
            prev_op, prev_i, prev_j = op, i, j
    merged.append(group)

    for group in merged:
        op = group[0][0]
        if op == 'insert':
            chars = ''.join([s2[j] for _, _, j in group])
            descs.append(f"\"insert\":\"{chars}\"")
        elif op == 'delete':
            chars = ''.join([s1[i] for _, i, _ in group])
            descs.append(f"\"delete\":\"{chars}\"")
        elif op == 'replace':
            chars_from = ''.join([s1[i] for _, i, _ in group])
            chars_to = ''.join([s2[j] for _, _, j in group])
            descs.append(f"\"replace\": \"{chars_from}\" --> \"{chars_to}\"")
    return descs

_user_editor_last_content = {}

# 内存模拟存储
_note_contents_store: Dict[str, Any] = {}
_note_edit_history_store: Dict[str, list] = {}

class NoteContentRequest(BaseModel):
    note_id: str = Field(..., alias="noteId")
    user_id: str = Field(..., alias="userId")
    content: Any  # delta
    html: str
    updated_at: str = Field(..., alias="updatedAt")

class NoteEditHistoryRequest(BaseModel):
    note_id: str = Field(..., alias="noteId")
    user_id: str = Field(..., alias="userId")
    delta: Any
    char_count: int = Field(..., alias="charCount")
    is_delete: bool = Field(False, alias="isDelete")
    has_header: bool = Field(False, alias="hasHeader")
    has_list: bool = Field(False, alias="hasList")
    updated_at: str = Field(..., alias="updatedAt")
    summary: str = ""
    affected_text: str = Field("", alias="affectedText")

@router.post("/api/editor/push_content")
async def editor_push_content(req:EditorContentRequest):
    """
    编辑器上传内容
    """
    try:
        logger.info(req.content)

        last_content = _user_editor_last_content.get(req.user_id, "")
        _user_editor_last_content[req.user_id] = req.content

        logger.info(describe_editops(last_content, req.content))

        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"editor_push_content 失败: {traceback.format_exc()}")

@router.post("/api/note/content")
async def save_note_content(req: Request):
    """
    保存笔记内容（直接存前端传来的字段）
    """
    try:
        data = await req.json()
        db.collection("note_contents").add(data)
        logger.info(f"[save_note_content] {data}")
        return {"success": True}
    except Exception as e:
        logger.error(f"save_note_content 失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"save_note_content 失败: {traceback.format_exc()}")

@router.post("/api/note/edit-history")
async def save_note_edit_history(req: Request):
    """
    保存编辑历史（直接存前端传来的字段）
    """
    try:
        data = await req.json()
        db.collection("note_edit_history").add(data)
        logger.info(f"[save_note_edit_history] {data}")
        return {"success": True}
    except Exception as e:
        logger.error(f"save_note_edit_history 失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"save_note_edit_history 失败: {traceback.format_exc()}")
