import yaml

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import ExternalLanguageServerId, FilenameMatcher, LanguageServerId
from solidlsp.settings import SolidLSPSettings


def test_yaml_string_keyed_builtin_settings_are_preserved(tmp_path):
    values = yaml.safe_load("python:\n  ls_path: configured.py\n")
    settings = SolidLSPSettings(solidlsp_dir=str(tmp_path), ls_specific_settings=values)
    assert settings.get_ls_specific_settings(LanguageServerId.PYTHON).get("ls_path") == "configured.py"


def test_string_keyed_external_settings_are_preserved(tmp_path):
    class ExternalServer(SolidLanguageServer):
        pass

    external = ExternalLanguageServerId("external", FilenameMatcher(".ext"), ExternalServer)
    settings = SolidLSPSettings(solidlsp_dir=str(tmp_path), ls_specific_settings={"external": {"value": 1}})
    assert settings.get_ls_specific_settings(external).get("value") == 1


def test_object_keyed_builtin_and_external_settings_remain_readable(tmp_path):
    class ExternalServer(SolidLanguageServer):
        pass

    external = ExternalLanguageServerId("external", FilenameMatcher(".ext"), ExternalServer)
    settings = SolidLSPSettings(
        solidlsp_dir=str(tmp_path),
        ls_specific_settings={LanguageServerId.PYTHON: {"value": 1}, external: {"value": 2}},
    )
    assert settings.get_ls_specific_settings(LanguageServerId.PYTHON).get("value") == 1
    assert settings.get_ls_specific_settings(external).get("value") == 2


def test_empty_object_keyed_settings_take_precedence(tmp_path):
    settings = SolidLSPSettings(
        solidlsp_dir=str(tmp_path),
        ls_specific_settings={LanguageServerId.PYTHON: {}, "python": {"value": 1}},
    )
    assert settings.get_ls_specific_settings(LanguageServerId.PYTHON).get("value", "default") == "default"


def test_missing_settings_return_default(tmp_path):
    settings = SolidLSPSettings(solidlsp_dir=str(tmp_path))
    assert settings.get_ls_specific_settings(LanguageServerId.PYTHON).get("value", "default") == "default"
