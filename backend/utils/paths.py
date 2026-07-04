# -*- coding: utf-8 -*-
"""路径与文件名安全工具:目录名清洗、重名追加序号、防路径穿越。"""
import os

from config import ILLEGAL_FILENAME_CHARS


def sanitize_name(name):
    """清洗目录/文件名:去除文件系统非法字符,去除首尾空白与点。"""
    if not name:
        return 'unnamed'
    cleaned = ''.join(c for c in str(name) if c not in ILLEGAL_FILENAME_CHARS)
    cleaned = cleaned.strip().strip('.').strip()
    return cleaned or 'unnamed'


def unique_dirname(base, existing):
    """若 base 已存在于 existing 集合,追加 _2、_3… 直到唯一。"""
    if base not in existing:
        return base
    i = 2
    while '{}_{}'.format(base, i) in existing:
        i += 1
    return '{}_{}'.format(base, i)


def safe_join(base_dir, *parts):
    """安全拼接路径:解析后必须仍在 base_dir 内,否则抛 ValueError(防穿越)。"""
    base = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base, *[str(p) for p in parts]))
    if os.path.commonpath([base, target]) != base:
        raise ValueError('非法路径访问: {}'.format(target))
    return target
