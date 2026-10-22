"""Compatibility test for the bundled notebook-style full `.pth` checkpoint."""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


_REPO_ROOT = Path(__file__).resolve().parents[2]


class LegacyCheckpointTests(unittest.TestCase):
    def test_torch_loader_temporarily_maps_notebook_resnet9_name(self) -> None:
        torch_module = types.ModuleType("torch")
        torch_module.__path__ = []
        nn_module = types.ModuleType("torch.nn")

        class FakeModule:
            pass

        nn_module.Module = FakeModule
        torch_module.nn = nn_module
        loaded = object()
        calls: list[dict[str, object]] = []
        main_module = sys.modules["__main__"]
        missing = object()
        previous_resnet9 = getattr(main_module, "ResNet9", missing)

        def fake_torch_load(_path: str, **kwargs):
            self.assertIs(main_module.ResNet9, model_module.ResNet9)
            calls.append(kwargs)
            if len(calls) == 1:
                raise RuntimeError("new PyTorch defaults to weights_only")
            return loaded

        torch_module.load = fake_torch_load
        spec = importlib.util.spec_from_file_location(
            "arena_test_disease_model", _REPO_ROOT / "disease_model.py"
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        model_module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"torch": torch_module, "torch.nn": nn_module}):
            spec.loader.exec_module(model_module)
            result = model_module._torch_load("plant-disease-model-complete.pth")

        self.assertIs(result, loaded)
        self.assertEqual(
            calls,
            [
                {"map_location": "cpu"},
                {"map_location": "cpu", "weights_only": False},
            ],
        )
        if previous_resnet9 is missing:
            self.assertFalse(hasattr(main_module, "ResNet9"))
        else:
            self.assertIs(main_module.ResNet9, previous_resnet9)


if __name__ == "__main__":
    unittest.main()
