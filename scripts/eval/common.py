"""Shared helpers for the evaluation scripts: env guards, run configuration, probes, IO.

Never reads or prints values from ``.env``.
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from scripts.eval import data_loading as dl

ROOT = dl.ROOT
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def set_env_guards() -> None:
    """Make runs hermetic. Must be called BEFORE importing anything from ``app``."""
    os.environ["HF_HUB_OFFLINE"] = "1"  # use the local HF cache only
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ["GEMINI_API_KEY"] = ""  # never call an LLM
    os.environ["NEO4J_URI"] = "bolt://127.0.0.1:1"  # unreachable on purpose
    os.environ.setdefault("SECRET_KEY", "eval-secret-key-not-for-production")
    os.environ.setdefault("ENVIRONMENT", "test")


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False
        )
        return out.stdout.strip()
    except Exception:  # pragma: no cover - git missing
        return ""


def git_info() -> Dict[str, Any]:
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    return {"commit": commit or "unknown", "dirty": bool(status), "dirty_files": len(status.splitlines()) if status else 0}


def tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_services() -> Dict[str, Dict[str, Any]]:
    """TCP probes of the services the graph/pgvector methods need (localhost only)."""
    probes = {
        "postgres_5432": ("127.0.0.1", 5432),
        "postgres_55432": ("127.0.0.1", 55432),
        "neo4j_7687": ("127.0.0.1", 7687),
    }
    return {k: {"host": h, "port": p, "reachable": tcp_open(h, p)} for k, (h, p) in probes.items()}


def cpu_name() -> str:
    name = platform.processor() or ""
    try:  # Windows: friendlier name
        if os.name == "nt":
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"],
                capture_output=True, text=True, timeout=20, check=False,
            ).stdout.strip()
            if out:
                name = out
    except Exception:
        pass
    return name or "unknown"


def lib_versions() -> Dict[str, str]:
    out = {"python": platform.python_version()}
    for mod in ("numpy", "torch", "sentence_transformers"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = "unavailable"
    return out


def label_file_hashes() -> Dict[str, str]:
    return {
        p.name: dl.sha1_file(p)
        for p in (dl.PAIRS_FILE, dl.SKILLS_GOLD_FILE, dl.GAP_GOLD_FILE, dl.EVAL_DIR / "ANNOTATION_GUIDELINE.md")
        if p.exists()
    }


def base_config(extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {
        "date_utc": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "git": git_info(),
        "python_executable": Path(sys.executable).name,
        "versions": lib_versions(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu": cpu_name(),
        "cpu_count": os.cpu_count(),
        "model_requested": MODEL_NAME,
        "label_file_sha1": label_file_hashes(),
        "service_probes": probe_services(),
        "env_guards": {"HF_HUB_OFFLINE": "1", "GEMINI_API_KEY": "<empty>", "NEO4J_URI": "unreachable-by-design"},
    }
    if extra:
        cfg.update(extra)
    return cfg


def model_info() -> Dict[str, Any]:
    """Load the real model through the project's client (needs set_env_guards first)."""
    try:
        from app.clients.sentence_transformer import get_sentence_transformer

        client = get_sentence_transformer()
        return {
            "status": "ok",
            "model_name": client.model_name,
            "device": client.device,
            "embedding_dim": client.embedding_dimension,
        }
    except Exception as exc:  # model not available offline etc.
        return {"status": "error", "reason": f"{type(exc).__name__}: {exc}"[:300]}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
