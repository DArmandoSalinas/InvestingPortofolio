from pathlib import Path

import app.paths as paths


def test_walk_finds_monorepo_from_api_package(tmp_path: Path, monkeypatch):
    repo = tmp_path / "InvestingPortofolio"
    api_app = repo / "apps" / "api" / "app"
    api_app.mkdir(parents=True)
    (repo / "supabase").mkdir()
    (repo / "supabase" / "seed.sql").write_text("-- seed\n")
    monkeypatch.delenv("REPO_ROOT", raising=False)
    monkeypatch.delenv("INVESTING_REPO_ROOT", raising=False)
    paths.clear_repo_root_cache()

    assert paths.walk_repo_root(api_app / "render_seed.py") == repo.resolve()
    assert paths.repo_root(api_app / "config.py") == repo.resolve()
    assert paths.seed_sql_path(repo.resolve()) == repo.resolve() / "supabase" / "seed.sql"


def test_shallow_docker_layout_does_not_need_parents_3(tmp_path: Path, monkeypatch):
    """Image layout: /app/app/*.py and /app/supabase — parents[3] would IndexError."""
    root = tmp_path / "app"
    package = root / "app"
    package.mkdir(parents=True)
    (root / "supabase").mkdir()
    (root / "supabase" / "seed.sql").write_text("-- seed\n")
    monkeypatch.delenv("REPO_ROOT", raising=False)
    monkeypatch.delenv("INVESTING_REPO_ROOT", raising=False)
    paths.clear_repo_root_cache()

    found = paths.walk_repo_root(package / "render_seed.py")
    assert found == root.resolve()
    assert paths.seed_sql_path(found) == root.resolve() / "supabase" / "seed.sql"


def test_repo_root_env_wins(tmp_path: Path, monkeypatch):
    chosen = tmp_path / "custom-root"
    chosen.mkdir()
    (chosen / "supabase").mkdir()
    monkeypatch.setenv("REPO_ROOT", str(chosen))
    paths.clear_repo_root_cache()

    assert paths.repo_root() == chosen.resolve()
    assert paths.repo_root(tmp_path / "elsewhere" / "file.py") == chosen.resolve()


def test_render_seed_main_writes_under_discovered_root(tmp_path: Path, monkeypatch):
    from app import render_seed

    repo = tmp_path / "repo"
    (repo / "supabase").mkdir(parents=True)
    monkeypatch.setenv("REPO_ROOT", str(repo))
    paths.clear_repo_root_cache()

    render_seed.main()
    written = repo / "supabase" / "seed.sql"
    assert written.is_file()
    text = written.read_text()
    assert "insert into public.companies" in text
    assert "insert into public.score_snapshots" in text
