# -*- coding: utf-8 -*-
"""材料文件文本提取:供 AI 摘要功能使用。

仅提取纯文本类文件(txt/csv/md/log),二进制文档(pdf/doc/docx 等)暂不支持,
返回空文本与提示说明。不引入 pdfplumber/python-docx 等重依赖。
"""
import os

# 支持直接读取的文本扩展名
_TEXT_EXT = {'.txt', '.csv', '.md', '.log'}
# 单文件提取上限(字符),避免超长文本撑爆 prompt
_MAX_CHARS = 8000


def extract_text(abs_path):
    """从文件提取纯文本。

    返回 (text, note):
      text — 提取到的文本(可能为空)
      note — 提取说明,空字符串表示正常提取;否则为原因说明
    """
    if not abs_path or not os.path.isfile(abs_path):
        return '', '文件不存在'

    ext = os.path.splitext(abs_path)[1].lower()
    if ext not in _TEXT_EXT:
        return '', '该文件类型({})暂不支持文本提取,已基于文件名与任务信息生成摘要'.format(ext or '未知')

    # 尝试 utf-8,失败回退 gbk
    text = None
    for enc in ('utf-8', 'gbk'):
        try:
            with open(abs_path, 'r', encoding=enc) as f:
                text = f.read(_MAX_CHARS + 1)
            break
        except (UnicodeDecodeError, IOError, OSError):
            continue
    if text is None:
        return '', '文件读取失败'

    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS] + '\n...(内容已截断)'
    return text, ''
