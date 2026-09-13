"""Tests for the CLI."""



from evident.cli import main


def test_init_creates_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["init", "my-project"])
    assert rc == 0
    root = tmp_path / "my-project"
    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "my_project" / "evaluate.py").exists()
    assert (root / "src" / "my_project" / "improve.py").exists()
    assert (root / "src" / "my_project" / "policy.py").exists()
    assert (root / "tests" / "test_my_project.py").exists()


def test_init_duplicate_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["init", "my-project"])
    rc = main(["init", "my-project"])
    assert rc == 1
    assert "already exists" in capsys.readouterr().err


def test_no_command_prints_help(capsys):
    rc = main([])
    assert rc == 0


def test_init_with_hyphens_creates_underscore_pkg(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["init", "my-cool-app"])
    assert rc == 0
    assert (tmp_path / "my-cool-app" / "src" / "my_cool_app" / "evaluate.py").exists()
