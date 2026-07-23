"""Tests for Lane B: provider-scoped OpenAI STT language propagation.

Goal: replace the old shared-backend ``language='en'`` hardcode with
provider-scoped optional language propagation. Native OpenAI should read
``stt.openai.language``; empty/None omits the kwarg. DeepInfra must remain
independently configurable and must not silently inherit OpenAI's
language. Behavior when unset must be preserved (no ``language`` kwarg
sent to the SDK).

These tests are intentionally scoped to the language kwarg propagation
contract.  They exercise:

* ``_transcribe_openai`` — ``language`` kwarg is forwarded to the SDK
  when provided, and omitted when the value is empty/None.
* ``transcribe_audio`` dispatch for ``provider="openai"`` — reads
  ``stt.openai.language`` from config and forwards it.
* ``_transcribe_deepinfra`` — must NOT inherit OpenAI's language setting.
  DeepInfra-specific config (``stt.deepinfra``) is the only source.

All external dependencies (openai) are mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


pytestmark = pytest.mark.usefixtures("disable_lazy_stt_install")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure no STT env vars leak into tests."""
    monkeypatch.delenv("VOICE_TOOLS_OPENAI_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPINFRA_API_KEY", raising=False)


def _make_audio(tmp_path):
    audio = tmp_path / "speech.ogg"
    audio.write_bytes(b"fake audio")
    return str(audio)


# ---------------------------------------------------------------------------
# _transcribe_openai — language kwarg handling
# ---------------------------------------------------------------------------


class TestTranscribeOpenAILanguageKwarg:
    """``_transcribe_openai`` must forward or omit the ``language`` kwarg
    based on the value passed by the caller."""

    def test_language_forwarded_when_provided(self, monkeypatch, tmp_path):
        monkeypatch.setenv("VOICE_TOOLS_OPENAI_KEY", "sk-test")
        audio_file = _make_audio(tmp_path)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Hello"

        with patch("tools.transcription_tools._HAS_OPENAI", True), \
             patch("openai.OpenAI", return_value=mock_client):
            from tools.transcription_tools import _transcribe_openai
            result = _transcribe_openai(
                audio_file, "whisper-1", language="fr",
            )

        assert result["success"] is True
        create_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert create_kwargs.get("language") == "fr"

    def test_language_omitted_when_empty_string(self, monkeypatch, tmp_path):
        """Empty string must be treated as 'not set' — do NOT send
        ``language=""`` to the OpenAI SDK."""
        monkeypatch.setenv("VOICE_TOOLS_OPENAI_KEY", "sk-test")
        audio_file = _make_audio(tmp_path)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Hello"

        with patch("tools.transcription_tools._HAS_OPENAI", True), \
             patch("openai.OpenAI", return_value=mock_client):
            from tools.transcription_tools import _transcribe_openai
            result = _transcribe_openai(
                audio_file, "whisper-1", language="",
            )

        assert result["success"] is True
        create_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert "language" not in create_kwargs

    def test_language_omitted_when_none(self, monkeypatch, tmp_path):
        """Default (no language kwarg) must not pass ``language`` to the SDK."""
        monkeypatch.setenv("VOICE_TOOLS_OPENAI_KEY", "sk-test")
        audio_file = _make_audio(tmp_path)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Hello"

        with patch("tools.transcription_tools._HAS_OPENAI", True), \
             patch("openai.OpenAI", return_value=mock_client):
            from tools.transcription_tools import _transcribe_openai
            result = _transcribe_openai(audio_file, "whisper-1")

        assert result["success"] is True
        create_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert "language" not in create_kwargs

    def test_language_whitespace_stripped(self, monkeypatch, tmp_path):
        """Whitespace-only language must be treated as empty (omitted)."""
        monkeypatch.setenv("VOICE_TOOLS_OPENAI_KEY", "sk-test")
        audio_file = _make_audio(tmp_path)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Hello"

        with patch("tools.transcription_tools._HAS_OPENAI", True), \
             patch("openai.OpenAI", return_value=mock_client):
            from tools.transcription_tools import _transcribe_openai
            result = _transcribe_openai(
                audio_file, "whisper-1", language="   ",
            )

        assert result["success"] is True
        create_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert "language" not in create_kwargs


# ---------------------------------------------------------------------------
# transcribe_audio — openai provider reads stt.openai.language
# ---------------------------------------------------------------------------


class TestTranscribeAudioOpenAIProviderConfig:
    """``transcribe_audio`` with provider='openai' must read
    ``stt.openai.language`` from config and forward it to the SDK."""

    def test_openai_provider_reads_stt_openai_language(self, monkeypatch, tmp_path):
        monkeypatch.setenv("VOICE_TOOLS_OPENAI_KEY", "sk-test")
        audio_file = _make_audio(tmp_path)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "bonjour"

        stt_config = {
            "enabled": True,
            "provider": "openai",
            "openai": {"model": "whisper-1", "language": "fr"},
        }

        with patch("tools.transcription_tools._load_stt_config", return_value=stt_config), \
             patch("tools.transcription_tools._get_provider", return_value="openai"), \
             patch("tools.transcription_tools._HAS_OPENAI", True), \
             patch("openai.OpenAI", return_value=mock_client):
            from tools.transcription_tools import transcribe_audio
            result = transcribe_audio(audio_file)

        assert result["success"] is True
        create_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert create_kwargs.get("language") == "fr"

    def test_openai_provider_no_language_omits_kwarg(self, monkeypatch, tmp_path):
        """When ``stt.openai.language`` is unset/empty, the SDK call must
        not include a ``language`` kwarg (preserves current behavior)."""
        monkeypatch.setenv("VOICE_TOOLS_OPENAI_KEY", "sk-test")
        audio_file = _make_audio(tmp_path)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Hello"

        stt_config = {
            "enabled": True,
            "provider": "openai",
            "openai": {"model": "whisper-1"},  # no language
        }

        with patch("tools.transcription_tools._load_stt_config", return_value=stt_config), \
             patch("tools.transcription_tools._get_provider", return_value="openai"), \
             patch("tools.transcription_tools._HAS_OPENAI", True), \
             patch("openai.OpenAI", return_value=mock_client):
            from tools.transcription_tools import transcribe_audio
            result = transcribe_audio(audio_file)

        assert result["success"] is True
        create_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert "language" not in create_kwargs

    def test_openai_provider_empty_language_string_omits_kwarg(self, monkeypatch, tmp_path):
        """An explicit empty string in ``stt.openai.language`` must be
        treated as 'not set' — backward-compatibility with the old
        shared-backend pattern."""


# ---------------------------------------------------------------------------
# DeepInfra isolation note
# -----------------------------------------------------------------------------


class TestDeepInfraLanguageIsolation:
    """DeepInfra is not in active use on this profile (no DeepInfra
    transcription observed in the last two months). The original
    isolation test is kept as a structural guard so a future refactor
    that wires DeepInfra to read a language config cannot silently
    inherit ``stt.openai.language``."""

    def test_deepinfra_does_not_inherit_openai_language(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DEEPINFRA_API_KEY", "di-test")
        audio_file = _make_audio(tmp_path)

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "Hello"

        # OpenAI is set to French, but DeepInfra is being used.
        # DeepInfra must not pick up "fr" from stt.openai.language.
        stt_config = {
            "enabled": True,
            "provider": "deepinfra",
            "openai": {"model": "whisper-1", "language": "fr"},
            "deepinfra": {"model": "vendor/test-stt"},
        }

        with patch("tools.transcription_tools._load_stt_config", return_value=stt_config), \
             patch("tools.transcription_tools._HAS_OPENAI", True), \
             patch("openai.OpenAI", return_value=mock_client):
            from tools.transcription_tools import transcribe_audio
            result = transcribe_audio(audio_file)

        assert result["success"] is True
        assert result["provider"] == "deepinfra"
        create_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        # DeepInfra must NOT have inherited OpenAI's language.
        assert "language" not in create_kwargs
