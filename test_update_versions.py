import json
from unittest.mock import MagicMock, patch

import pytest

import update_versions

DOCKERFILE_CONTENT = """\
FROM base AS npm-builder

ARG OPENCHAMBER_VERSION=2.7.0
ARG OPENCODE_VERSION=2.2.5

RUN npm install -g --prefix /npm-global \\
    @openchamber/web@${OPENCHAMBER_VERSION}
"""


def _urlopen_mock(version: str) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = json.dumps({"version": version}).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestGetLatestVersion:
    def test_returns_version_from_registry(self):
        with patch("urllib.request.urlopen", return_value=_urlopen_mock("2.7.2")):
            assert update_versions.get_latest_version("@openchamber/web") == "2.7.2"

    def test_encodes_slash_in_scoped_package(self):
        captured = []

        def fake_urlopen(url, timeout=None):
            captured.append(url)
            return _urlopen_mock("2.7.2")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            update_versions.get_latest_version("@openchamber/web")

        assert len(captured) == 1
        assert "@openchamber%2Fweb" in captured[0]


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    dockerfile = tmp_path / "Dockerfile"
    version_file = tmp_path / "VERSION"
    dockerfile.write_text(DOCKERFILE_CONTENT)
    version_file.write_text("2.7.0\n")
    monkeypatch.setattr(update_versions, "DOCKERFILE", dockerfile)
    monkeypatch.setattr(update_versions, "VERSION_FILE", version_file)
    return {"dockerfile": dockerfile, "version_file": version_file}


def mock_latest(monkeypatch, openchamber="2.7.0", opencode="2.2.5"):
    versions = {"@openchamber/web": openchamber, "@opencode/cli": opencode}
    monkeypatch.setattr(update_versions, "get_latest_version", lambda pkg: versions[pkg])


class TestMainUpToDate:
    def test_no_changes(self, repo, monkeypatch):
        mock_latest(monkeypatch)
        before = repo["dockerfile"].read_text()
        assert update_versions.main() == 0
        assert repo["version_file"].read_text() == "2.7.0\n"
        assert repo["dockerfile"].read_text() == before


class TestMainUpdates:
    def test_openchamber_bumped(self, repo, monkeypatch):
        mock_latest(monkeypatch, openchamber="2.7.2")
        assert update_versions.main() == 0
        assert repo["version_file"].read_text() == "2.7.2\n"
        assert "ARG OPENCHAMBER_VERSION=2.7.2" in repo["dockerfile"].read_text()

    def test_opencode_only_bumped_preserves_version_file(self, repo, monkeypatch):
        mock_latest(monkeypatch, opencode="2.3.0")
        assert update_versions.main() == 0
        assert repo["version_file"].read_text() == "2.7.0\n"
        assert "ARG OPENCODE_VERSION=2.3.0" in repo["dockerfile"].read_text()
