# -*- coding: utf-8 -*-
"""基于文件系统的 JSON 存储:原子写 + 文件锁。

所有数据相对 DATA_DIR 存放。写入采用「临时文件 + os.replace 原子重命名」,
并用 filelock 软锁串行化同一文件的并发写,防止低并发场景下的数据覆盖。
"""
import os
import json
import tempfile
from filelock import FileLock

from config import DATA_DIR


def _abs(rel):
    """相对 DATA_DIR 的绝对路径。rel 为 '' 时返回 DATA_DIR 本身。"""
    return os.path.join(DATA_DIR, rel) if rel else DATA_DIR


def ensure_dir(rel=''):
    """确保目录存在。"""
    p = _abs(rel)
    os.makedirs(p, exist_ok=True)
    return p


def exists(rel):
    return os.path.exists(_abs(rel))


def read_json(rel, default=None):
    """读取 JSON 文件。不存在或解析失败时返回 default(default 可为 callable)。"""
    p = _abs(rel)
    if not os.path.exists(p):
        return default() if callable(default) else default
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return default() if callable(default) else default


def write_json(rel, data):
    """原子写入 JSON:临时文件 → os.replace 重命名,中途异常不会写坏原文件。"""
    p = _abs(rel)
    os.makedirs(os.path.dirname(p) or DATA_DIR, exist_ok=True)
    lock = FileLock(p + '.lock', timeout=15)
    with lock:
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(p) or DATA_DIR, suffix='.tmp', prefix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, p)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
    return data


def list_json_files(dir_rel):
    """列出某目录下所有 .json 文件名(不含路径)。"""
    p = _abs(dir_rel)
    if not os.path.isdir(p):
        return []
    return [f for f in os.listdir(p) if f.endswith('.json')]
