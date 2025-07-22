import traceback

import Levenshtein
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.app.logger.logger_loader import logger

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
