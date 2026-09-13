"""Tests for the examples – they should run without errors."""

import importlib.util
import sys
from pathlib import Path


def _load_example(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_document_extraction_example_runs(capsys):
    mod = _load_example(
        "doc_ex",
        Path(__file__).parent.parent / "examples" / "document_extraction" / "run.py",
    )
    mod.run()
    out = capsys.readouterr().out
    assert "Document Extraction" in out


def test_config_validation_example_runs(capsys):
    mod = _load_example(
        "cfg_ex",
        Path(__file__).parent.parent / "examples" / "config_validation" / "run.py",
    )
    mod.run()
    out = capsys.readouterr().out
    assert "Config Validation" in out
    assert "Final config" in out
