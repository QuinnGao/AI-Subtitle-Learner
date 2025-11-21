"""
测试配置和 Fixtures
"""
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_srt_file(temp_dir):
    """创建示例 SRT 字幕文件"""
    srt_content = """1
00:00:00,000 --> 00:00:02,000
Hello, this is a test subtitle.

2
00:00:02,000 --> 00:00:04,000
This is the second line.

3
00:00:04,000 --> 00:00:06,000
And this is the third line.
"""
    srt_file = temp_dir / "test.srt"
    srt_file.write_text(srt_content, encoding="utf-8")
    return str(srt_file)


@pytest.fixture
def sample_srt_file_not_exist():
    """返回一个不存在的文件路径"""
    return "/path/to/nonexistent/file.srt"


@pytest.fixture
def sample_ass_file(temp_dir):
    """创建示例 ASS 字幕文件"""
    ass_content = """[Script Info]
Title: Test Subtitle
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,Hello, this is a test subtitle.
Dialogue: 0,0:00:02.00,0:00:04.00,Default,,0,0,0,,This is the second line.
"""
    ass_file = temp_dir / "test.ass"
    ass_file.write_text(ass_content, encoding="utf-8")
    return str(ass_file)


@pytest.fixture
def sample_vtt_file(temp_dir):
    """创建示例 VTT 字幕文件"""
    vtt_content = """WEBVTT

00:00:00.000 --> 00:00:02.000
Hello, this is a test subtitle.

00:00:02.000 --> 00:00:04.000
This is the second line.

00:00:04.000 --> 00:00:06.000
And this is the third line.
"""
    vtt_file = temp_dir / "test.vtt"
    vtt_file.write_text(vtt_content, encoding="utf-8")
    return str(vtt_file)

