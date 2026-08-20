"""Provides InTouch QuickScript support through the native intouch-language server."""

import logging
import os
import shutil

from solidlsp.ls import (
    LanguageServerDependencyProvider,
    LanguageServerDependencyProviderSinglePath,
    SolidLanguageServer,
)
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.settings import SolidLSPSettings

log = logging.getLogger(__name__)


class QuickScriptLanguageServer(SolidLanguageServer):
    """Connect Serena to the native intouch-language QuickScript server."""

    def __init__(self, config: LanguageServerConfig, repository_root_path: str, solidlsp_settings: SolidLSPSettings):
        super().__init__(config, repository_root_path, None, "quickscript", solidlsp_settings)

    def _create_dependency_provider(self) -> LanguageServerDependencyProvider:
        return self.DependencyProvider(self._custom_settings, self._ls_resources_dir)

    class DependencyProvider(LanguageServerDependencyProviderSinglePath):
        def _get_or_install_core_dependency(self) -> str:
            raise FileNotFoundError(
                "The intouch-language QuickScript server is not bundled with Serena. "
                "Set ls_specific_settings.quickscript.ls_path to its dist/server.js entry point."
            )

        def _create_launch_command(self, core_path: str) -> list[str]:
            if not os.path.isfile(core_path):
                raise FileNotFoundError(f"QuickScript language server entry point not found: {core_path}")

            node_path = shutil.which("node")
            if node_path is None:
                raise FileNotFoundError("Node.js is required to launch the intouch-language QuickScript server.")
            return [node_path, core_path, "--stdio"]

    def _supports_pull_diagnostics(self) -> bool:
        return False

    def _create_base_initialize_params(self) -> dict:
        return {
            "locale": "en",
            "capabilities": {
                "textDocument": {
                    "synchronization": {"didSave": True, "dynamicRegistration": True},
                    "definition": {"dynamicRegistration": True, "linkSupport": True},
                    "references": {"dynamicRegistration": True},
                    "documentSymbol": {
                        "dynamicRegistration": True,
                        "hierarchicalDocumentSymbolSupport": True,
                        "symbolKind": {"valueSet": list(range(1, 27))},
                    },
                    "completion": {
                        "dynamicRegistration": True,
                        "completionItem": {
                            "snippetSupport": True,
                            "documentationFormat": ["markdown", "plaintext"],
                        },
                    },
                    "hover": {
                        "dynamicRegistration": True,
                        "contentFormat": ["markdown", "plaintext"],
                    },
                },
                "workspace": {
                    "workspaceFolders": True,
                    "configuration": True,
                },
            },
        }

    def _start_server(self) -> None:
        def configuration_handler(params: dict) -> list[dict]:
            items = params.get("items", []) if isinstance(params, dict) else []
            return [{} for _ in items]

        def do_nothing(_params: dict) -> None:
            return

        self.server.on_request("client/registerCapability", do_nothing)
        self.server.on_request("workspace/configuration", configuration_handler)
        self.server.on_notification("window/logMessage", do_nothing)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)

        log.info("Starting intouch-language QuickScript server process")
        self.server.start()

        log.info("Initializing intouch-language QuickScript server")
        init_response = self.server.send.initialize(self._create_initialize_params())
        capabilities = init_response["capabilities"]
        assert capabilities.get("documentSymbolProvider") is True
        assert capabilities.get("definitionProvider") is True
        assert capabilities.get("referencesProvider") is True

        self.server.notify.initialized({})
