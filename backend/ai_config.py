# -*- coding: utf-8 -*-
"""AI 配置加载:解析项目根目录 agnes.env,支持环境变量覆盖。

agnes.env 格式(KEY=VALUE):
    API_KEY=sk-...
    BASE_URL=https://apihub.agnes-ai.com/v1
    MODEL_NAME=agnes-20-flash

生产部署可用环境变量 AGNES_API_KEY / AGNES_BASE_URL / AGNES_MODEL_NAME 覆盖文件值。
密钥仅在后端内存中,不写入日志、不返回前端。
"""
import os

from config import PROJECT_ROOT

_ENV_FILE = os.path.join(PROJECT_ROOT, 'agnes.env')

# 环境变量名映射(环境变量优先于文件值)
_ENV_OVERRIDE = {
    'API_KEY': 'AGNES_API_KEY',
    'BASE_URL': 'AGNES_BASE_URL',
    'MODEL_NAME': 'AGNES_MODEL_NAME',
}

_REQUIRED_KEYS = ('API_KEY', 'BASE_URL', 'MODEL_NAME')

# 缓存哨兵:区分"未加载"(_MISSING)与"加载后无配置"(None)
_MISSING = object()
_cache = _MISSING


def _parse_env_file(path):
    """解析 KEY=VALUE 文件,返回 dict。文件不存在或读取失败返回 {}。"""
    result = {}
    if not os.path.isfile(path):
        return result
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k:
                    result[k] = v
    except (IOError, OSError):
        return {}
    return result


def get_ai_config():
    """返回 AI 配置 dict {api_key, base_url, model_name} 或 None(未配置)。

    环境变量优先于文件值。任一关键字段缺失返回 None。结果缓存。
    """
    global _cache
    if _cache is not _MISSING:
        return _cache if _cache is not None else None

    file_cfg = _parse_env_file(_ENV_FILE)
    values = {}
    for key in _REQUIRED_KEYS:
        env_name = _ENV_OVERRIDE[key]
        val = os.environ.get(env_name) or file_cfg.get(key) or ''
        values[key] = val.strip()

    if not all(values[k] for k in _REQUIRED_KEYS):
        _cache = None
        return None

    _cache = {
        'api_key': values['API_KEY'],
        'base_url': values['BASE_URL'].rstrip('/'),
        'model_name': values['MODEL_NAME'],
    }
    return _cache


def is_ai_ready():
    """AI 是否已配置可用。"""
    return get_ai_config() is not None


def reload_config():
    """清除缓存,强制重新加载(测试用)。"""
    global _cache
    _cache = _MISSING
