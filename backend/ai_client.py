# -*- coding: utf-8 -*-
"""Agnes AI 客户端:OpenAI 兼容的 chat completions 调用。

用标准库 urllib 实现,零第三方依赖。密钥从 ai_config.get_ai_config() 获取,
不打印到日志、不抛出到前端响应。
"""
import json
import urllib.request
import urllib.error

from ai_config import get_ai_config


class AIClientError(Exception):
    """AI 调用异常,带 HTTP 状态码(供路由层映射为响应码)。"""

    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def chat(messages, temperature=0.3, max_tokens=2000, timeout=60):
    """调用 Agnes chat completions,返回 assistant 文本。

    messages: [{role, content}, ...]
    失败抛 AIClientError。
    """
    cfg = get_ai_config()
    if not cfg:
        raise AIClientError('AI 未配置', status_code=503)

    url = '{}/chat/completions'.format(cfg['base_url'].rstrip('/'))
    payload = {
        'model': cfg['model_name'],
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Authorization': 'Bearer {}'.format(cfg['api_key']),
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        # 透传错误信息但不泄露 api_key
        detail = ''
        try:
            detail = e.read().decode('utf-8', errors='replace')
        except Exception:
            pass
        msg = 'AI 服务返回 HTTP {}'.format(e.code)
        if detail:
            msg = '{}: {}'.format(msg, detail[:300])
        raise AIClientError(msg, status_code=502)
    except urllib.error.URLError as e:
        reason = getattr(e, 'reason', e)
        raise AIClientError('AI 服务网络错误: {}'.format(reason), status_code=504)
    except TimeoutError:
        raise AIClientError('AI 服务请求超时', status_code=504)

    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        raise AIClientError('AI 返回非 JSON 数据', status_code=502)

    try:
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        raise AIClientError('AI 返回结构异常', status_code=502)
