# -*- coding: utf-8 -*-
"""文件上传:存 uploads/{阶段名}/{团队名}/{文件名},同名归档历史版本。

版本快照:同一任务再次上传同名文件时,旧版移动到 .versions/ 子目录并加时间戳,
任务记录里保留 file_versions 历史列表,需要时可找回。
"""
import os
import shutil
from datetime import datetime

from config import DATA_DIR, ALLOWED_UPLOAD_EXT
from utils.paths import sanitize_name, safe_join


def save_upload(dir_, stage_name, team_name, filename, file_obj):
    """保存上传文件。返回 (相对路径, 新增的历史版本列表) 或 (None, 错误信息)。"""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXT:
        return None, '不支持的文件类型: {}'.format(ext or '(无扩展名)')
    safe_fn = sanitize_name(filename)
    if not safe_fn or safe_fn in ('.', '..'):
        return None, '文件名非法'

    s_team = sanitize_name(team_name) or '未分团队'
    if stage_name:
        rel_dir = 'projects/{}/uploads/{}/{}'.format(
            dir_, sanitize_name(stage_name) or '未分阶段', s_team)
    else:
        rel_dir = 'projects/{}/uploads/{}'.format(dir_, s_team)
    abs_dir = safe_join(DATA_DIR, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    target = os.path.join(abs_dir, safe_fn)
    new_versions = []
    if os.path.exists(target):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, e = os.path.splitext(safe_fn)
        ver_dir = os.path.join(abs_dir, '.versions')
        os.makedirs(ver_dir, exist_ok=True)
        archived = os.path.join(ver_dir, '{}_{}{}'.format(name, ts, e))
        shutil.move(target, archived)
        new_versions.append(os.path.relpath(archived, DATA_DIR).replace('\\', '/'))

    file_obj.save(target)
    rel = os.path.relpath(target, DATA_DIR).replace('\\', '/')
    return rel, new_versions
