"""Smoke tests for the native InTouch QuickScript language server adapter."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import LanguageServerId
from test.conftest import start_ls_context


@pytest.fixture(scope="module")
def quickscript_language_server() -> Iterator[SolidLanguageServer]:
    """Start the external intouch-language server configured for this smoke test."""
    entrypoint = os.environ.get("INTOUCH_LANGUAGE_SERVER_ENTRYPOINT")
    if entrypoint is None:
        pytest.skip("INTOUCH_LANGUAGE_SERVER_ENTRYPOINT is not configured")

    resolved_entrypoint = str(Path(entrypoint).resolve())
    with start_ls_context(
        LanguageServerId.QUICKSCRIPT,
        ls_specific_settings={LanguageServerId.QUICKSCRIPT: {"ls_path": resolved_entrypoint}},
    ) as language_server:
        yield language_server


@pytest.mark.quickscript
class TestQuickScriptLanguageServerBasics:
    """Validate the minimal Serena-to-intouch-language integration surface."""

    def test_initialization_and_file_matching(self, quickscript_language_server: SolidLanguageServer) -> None:
        assert quickscript_language_server.ls_id == LanguageServerId.QUICKSCRIPT
        matcher = quickscript_language_server.get_source_fn_matcher()
        assert matcher.is_relevant_filename("definition.vbi")
        assert matcher.is_relevant_filename("caller.vi")

    def test_document_symbols(self, quickscript_language_server: SolidLanguageServer) -> None:
        symbols, _roots = quickscript_language_server.request_document_symbols("definition.vbi").get_all_symbols_and_roots()
        assert [symbol["name"] for symbol in symbols] == ["SerenaTestFunction"]

    def test_definition(self, quickscript_language_server: SolidLanguageServer) -> None:
        definitions = quickscript_language_server.request_definition("caller.vi", 0, 7)
        assert len(definitions) == 1
        assert definitions[0]["relativePath"] == "definition.vbi"

    def test_references(self, quickscript_language_server: SolidLanguageServer) -> None:
        references = quickscript_language_server.request_references("definition.vbi", 2, 7)
        assert len(references) == 1
        assert references[0]["relativePath"] == "caller.vi"
