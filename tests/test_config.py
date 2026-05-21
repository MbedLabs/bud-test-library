"""Tests for BudConfig lazy default and properties loading."""

import importlib
import logging
from unittest.mock import patch

import budtestlibrary.config as config_mod


class TestGetDefaultConfig:
    def test_not_instantiated_until_first_call(self):
        importlib.reload(config_mod)
        assert config_mod._default_config is None

    def test_returns_singleton(self):
        importlib.reload(config_mod)
        first = config_mod.get_default_config()
        second = config_mod.get_default_config()
        assert first is second

    def test_exported_from_package(self):
        from budtestlibrary import get_default_config

        cfg = get_default_config()
        assert isinstance(cfg, config_mod.BudConfig)


class TestPropertiesLoading:
    def test_load_warning_uses_logging(self, caplog):
        importlib.reload(config_mod)
        caplog.set_level(logging.WARNING, logger="budtestlibrary.config")

        config = config_mod.BudConfig(_properties_file="/nonexistent/path/app.properties")
        config._load_from_properties("/definitely/missing.properties")

        with patch("builtins.open", side_effect=PermissionError("denied")):
            config._load_from_properties("/fake/app.properties")

        assert any("Error loading properties file" in r.message for r in caplog.records)

    def test_invalid_suffix_does_not_raise(self, tmp_path):
        props = tmp_path / "app.properties"
        props.write_text("runnerSocketPort=not-a-number\n")
        config = config_mod.BudConfig(_properties_file=str(props))
        assert config.runner_socket_port == 53035  # default kept on bad conversion
