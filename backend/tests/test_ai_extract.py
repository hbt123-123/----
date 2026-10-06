# -*- coding: utf-8 -*-
"""utils.extract 单元测试:文本提取、编码回退、截断、不支持类型。"""
from utils.extract import extract_text


def test_txt_utf8(tmp_path):
    p = tmp_path / 'a.txt'
    p.write_text('你好世界\nhello', encoding='utf-8')
    text, note = extract_text(str(p))
    assert '你好世界' in text
    assert note == ''


def test_txt_gbk(tmp_path):
    p = tmp_path / 'g.txt'
    p.write_text('中文内容', encoding='gbk')
    text, note = extract_text(str(p))
    assert '中文内容' in text
    assert note == ''


def test_csv(tmp_path):
    p = tmp_path / 'c.csv'
    p.write_text('a,b,c\n1,2,3', encoding='utf-8')
    text, note = extract_text(str(p))
    assert '1,2,3' in text
    assert note == ''


def test_unsupported_pdf(tmp_path):
    p = tmp_path / 'x.pdf'
    p.write_bytes(b'%PDF-1.4 fake')
    text, note = extract_text(str(p))
    assert text == ''
    assert '暂不支持' in note


def test_unsupported_docx(tmp_path):
    p = tmp_path / 'd.docx'
    p.write_bytes(b'PK\x03\x04')
    text, note = extract_text(str(p))
    assert text == ''
    assert '暂不支持' in note


def test_truncate(tmp_path):
    p = tmp_path / 'big.txt'
    p.write_text('x' * 10000, encoding='utf-8')
    text, note = extract_text(str(p))
    assert len(text) <= 8100  # 8000 字符 + 截断提示
    assert '截断' in text


def test_not_exist(tmp_path):
    text, note = extract_text(str(tmp_path / 'no.txt'))
    assert text == ''
    assert '不存在' in note


def test_empty_path():
    text, note = extract_text('')
    assert text == ''
    assert '不存在' in note
