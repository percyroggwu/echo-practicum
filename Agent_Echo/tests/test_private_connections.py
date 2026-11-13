"""Offline selection of private connection settings; no credentials or network."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agents.connections import DEFAULT_CONFIG, ModelRegistry, load_connection_config


class PrivateConnectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.shared = Path(self.directory.name) / "connections.json"
        self.private = self.shared.with_name("connections.private.json")
        self.config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
        self.shared.write_text(json.dumps(self.config), encoding="utf-8")
        self.default = patch("agents.connections.DEFAULT_CONFIG", self.shared)
        self.default.start()
        self.addCleanup(self.default.stop)

    def write_private(self):
        config = json.loads(self.shared.read_text(encoding="utf-8"))
        config["profiles"]["gw_azure"].update(
            endpoint="https://offline-private-resource.openai.azure.com/",
            model="offline-private-deployment", request_interval_seconds=0)
        self.private.write_text(json.dumps(config), encoding="utf-8-sig")
        return config

    def test_shared_template_is_used_without_private_file(self):
        self.assertEqual(load_connection_config(), self.config)

    def test_private_file_is_used_by_every_gw_role_without_loading_keys(self):
        private = self.write_private()
        with patch.object(ModelRegistry, "_key", side_effect=AssertionError("No key access")):
            registry = ModelRegistry(config=self.shared, force_profile="gw_azure", env_file=None)
            self.assertEqual(registry.config, private)
            self.assertTrue(all(v["model"] == "offline-private-deployment"
                                and v["request_interval_seconds"] == 0
                                for v in registry.describe().values()))
        self.assertEqual(json.loads(self.shared.read_text(encoding="utf-8")), self.config)

    def test_explicit_other_config_does_not_load_default_private_file(self):
        self.write_private()
        other = self.shared.with_name("connections.local.json")
        other.write_text(json.dumps(self.config), encoding="utf-8")
        self.assertEqual(load_connection_config(other), self.config)

    def test_invalid_private_file_does_not_silently_use_shared_template(self):
        self.private.write_text("{invalid", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            ModelRegistry(config=self.shared, env_file=None)

    def test_azure_client_uses_private_endpoint_and_deployment(self):
        self.write_private()
        clients = []

        def client(**options):
            clients.append(options)
            return SimpleNamespace(close=lambda: None)

        with patch.object(ModelRegistry, "_key", return_value="offline-key"), \
             patch.dict("sys.modules", {"openai": SimpleNamespace(AzureOpenAI=client, OpenAI=client)}):
            registry = ModelRegistry(config=self.shared, force_profile="gw_azure", env_file=None)
            model = registry.get("Original")
            self.assertEqual(model.model, "offline-private-deployment")
            self.assertEqual(clients[0]["azure_endpoint"],
                             "https://offline-private-resource.openai.azure.com/")
            self.assertNotIn("request_pacer", clients[0])
            registry.close()
