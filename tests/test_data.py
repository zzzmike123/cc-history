"""Tests for data.py module."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.cc_history.app import _is_valid_uuid, _is_under_projects_dir, _resolve_known_project_path
from src.cc_history.data import (
    _extract_content,
    _parse_skill_md,
    load_settings,
    save_settings,
)


class TestUuidValidation:
    """UUID 格式验证测试。"""

    def test_valid_uuid(self):
        assert _is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_uppercase(self):
        assert _is_valid_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_invalid_uuid_no_dashes(self):
        assert _is_valid_uuid("550e8400e29b41d4a716446655440000") is False

    def test_invalid_uuid_short(self):
        assert _is_valid_uuid("550e8400-e29b-41d4") is False

    def test_invalid_uuid_letters(self):
        assert _is_valid_uuid("not-a-uuid-at-all-here") is False

    def test_empty_string(self):
        assert _is_valid_uuid("") is False

    def test_none(self):
        assert _is_valid_uuid(None) is False

    def test_path_traversal(self):
        assert _is_valid_uuid("../../../etc/passwd") is False

    def test_special_chars(self):
        assert _is_valid_uuid("'; DROP TABLE--") is False


class TestPathValidation:
    """路径穿越防护测试。"""

    @patch("src.cc_history.app.get_claude_dir")
    def test_valid_path(self, mock_dir):
        mock_dir.return_value = Path.home() / ".claude"
        projects = Path.home() / ".claude" / "projects" / "test"
        assert _is_under_projects_dir(str(projects)) is True

    @patch("src.cc_history.app.get_claude_dir")
    def test_path_traversal(self, mock_dir):
        mock_dir.return_value = Path.home() / ".claude"
        # 使用 .. 尝试穿越
        bad_path = str(Path.home() / ".claude" / "projects" / ".." / ".." / ".." / "etc")
        assert _is_under_projects_dir(bad_path) is False

    @patch("src.cc_history.app.get_claude_dir")
    def test_absolute_path_outside(self, mock_dir):
        mock_dir.return_value = Path.home() / ".claude"
        assert _is_under_projects_dir("C:\\Windows\\System32") is False

    @patch("src.cc_history.app.get_claude_dir")
    def test_projects_root(self, mock_dir):
        mock_dir.return_value = Path.home() / ".claude"
        projects = Path.home() / ".claude" / "projects"
        assert _is_under_projects_dir(str(projects)) is True
    @patch("src.cc_history.app._get_sessions_cached")
    def test_resolve_known_project_path(self, mock_sessions, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        mock_sessions.return_value = [{"realProjectPath": str(project)}]
        assert _resolve_known_project_path(str(project)) == project.resolve()

    @patch("src.cc_history.app._get_sessions_cached")
    def test_reject_unknown_project_path(self, mock_sessions, tmp_path):
        known = tmp_path / "known"
        other = tmp_path / "other"
        known.mkdir()
        other.mkdir()
        mock_sessions.return_value = [{"realProjectPath": str(known)}]
        assert _resolve_known_project_path(str(other)) is None


class TestExtractContent:
    """消息内容提取测试。"""

    def test_string_content(self):
        msg = {"content": "hello world"}
        assert _extract_content(msg) == "hello world"

    def test_list_content(self):
        msg = {"content": [
            {"type": "text", "text": "line 1"},
            {"type": "text", "text": "line 2"},
        ]}
        assert _extract_content(msg) == "line 1\nline 2"

    def test_mixed_list_content(self):
        msg = {"content": [
            {"type": "text", "text": "text"},
            "plain string",
        ]}
        assert _extract_content(msg) == "text\nplain string"

    def test_empty_content(self):
        msg = {"content": ""}
        assert _extract_content(msg) == ""

    def test_none_content(self):
        msg = {"content": None}
        assert _extract_content(msg) == ""

    def test_no_content_key(self):
        msg = {}
        assert _extract_content(msg) == ""

    def test_non_dict(self):
        assert _extract_content("not a dict") == ""
        assert _extract_content(None) == ""


class TestParseSkillMd:
    """SKILL.md 解析测试。"""

    def test_valid_skill(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: A test skill\nlicense: MIT\n---\n\nContent here",
            encoding="utf-8",
        )
        result = _parse_skill_md(skill_dir)
        assert result is not None
        assert result["name"] == "test-skill"
        assert result["description"] == "A test skill"
        assert result["license"] == "MIT"
        assert result["scope"] == "user"

    def test_no_skill_md(self, tmp_path):
        skill_dir = tmp_path / "empty-skill"
        skill_dir.mkdir()
        assert _parse_skill_md(skill_dir) is None

    def test_no_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "no-front"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("No frontmatter here", encoding="utf-8")
        assert _parse_skill_md(skill_dir) is None

    def test_missing_fields(self, tmp_path):
        skill_dir = tmp_path / "minimal"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
        result = _parse_skill_md(skill_dir)
        assert result is not None
        assert result["name"] == "minimal"  # fallback to dir name
