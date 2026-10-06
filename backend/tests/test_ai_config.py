# -*- coding: utf-8 -*-
"""ai_config 单元测试:agnes.env 解析、环境变量覆盖、缺失处理。"""
import ai_config


def _clear_env(monkeypatch):
    for k in ('AGNES_API_KEY', 'AGNES_BASE_URL', 'AGNES_MODEL_NAME'):
        monkeypatch.delenv(k, raising=False)


def test_parse_env_file(tmp_path, monkeypatch):
    env = tmp_path / 'agnes.env'
    env.write_text(
        '# comment\nAPI_KEY=sk-test\nBASE_URL=https://api.example.com/v1\nMODEL_NAME=m1\n',
        encoding='utf-8')
    monkeypatch.setattr(ai_config, '_ENV_FILE', str(env))
    _clear_env(monkeypatch)
    ai_config.reload_config()

    cfg = ai_config.get_ai_config()
    assert cfg is not None
    assert cfg['api_key'] == 'sk-test'
    assert cfg['base_url'] == 'https://api.example.com/v1'
    assert cfg['model_name'] == 'm1'
    assert ai_config.is_ai_ready() is True


def test_env_var_override(tmp_path, monkeypatch):
    """环境变量优先于文件值。"""
    env = tmp_path / 'agnes.env'
    env.write_text('API_KEY=sk-file\nBASE_URL=https://file.com/v1\nMODEL_NAME=mfile\n', encoding='utf-8')
    monkeypatch.setattr(ai_config, '_ENV_FILE', str(env))
    _clear_env(monkeypatch)
    monkeypatch.setenv('AGNES_API_KEY', 'sk-env')
    ai_config.reload_config()

    cfg = ai_config.get_ai_config()
    assert cfg['api_key'] == 'sk-env'   # 环境变量覆盖
    assert cfg['model_name'] == 'mfile'  # 文件值


def test_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_config, '_ENV_FILE', str(tmp_path / 'nope.env'))
    _clear_env(monkeypatch)
    ai_config.reload_config()

    assert ai_config.get_ai_config() is None
    assert ai_config.is_ai_ready() is False


def test_missing_key(tmp_path, monkeypatch):
    """缺关键字段(Missing MODEL_NAME)返回 None。"""
    env = tmp_path / 'agnes.env'
    env.write_text('API_KEY=sk-x\nBASE_URL=https://x.com/v1\n', encoding='utf-8')
    monkeypatch.setattr(ai_config, '_ENV_FILE', str(env))
    _clear_env(monkeypatch)
    ai_config.reload_config()

    assert ai_config.get_ai_config() is None


def test_base_url_trailing_slash(tmp_path, monkeypatch):
    """base_url 去掉尾部斜杠。"""
    env = tmp_path / 'agnes.env'
    env.write_text('API_KEY=sk\nBASE_URL=https://x.com/v1/\nMODEL_NAME=m\n', encoding='utf-8')
    monkeypatch.setattr(ai_config, '_ENV_FILE', str(env))
    _clear_env(monkeypatch)
    ai_config.reload_config()

    cfg = ai_config.get_ai_config()
    assert cfg['base_url'] == 'https://x.com/v1'


def test_quoted_value(tmp_path, monkeypatch):
    """带引号的值被剥离。"""
    env = tmp_path / 'agnes.env'
    env.write_text('API_KEY="sk-quoted"\nBASE_URL=https://x.com/v1\nMODEL_NAME=m\n', encoding='utf-8')
    monkeypatch.setattr(ai_config, '_ENV_FILE', str(env))
    _clear_env(monkeypatch)
    ai_config.reload_config()

    cfg = ai_config.get_ai_config()
    assert cfg['api_key'] == 'sk-quoted'
