#!/usr/bin/env python3
"""Simple health-check for local dev stack: Postgres, Redis, MLflow.

Usage:
  python scripts/check_stack.py

Environment variables (optional):
  POSTGRES_HOST, POSTGRES_PORT, REDIS_HOST, REDIS_PORT, MLFLOW_URL
"""
import os
import socket
import sys
import json
import urllib.request


def tcp_check(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def http_check(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "predicast-healthcheck/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.getcode() < 400
    except Exception:
        return False


def main():
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    rd_host = os.getenv("REDIS_HOST", "localhost")
    rd_port = int(os.getenv("REDIS_PORT", "6379"))
    mlflow_url = os.getenv("MLFLOW_URL", "http://localhost:5000")

    results = {
        "postgres": tcp_check(pg_host, pg_port),
        "redis": tcp_check(rd_host, rd_port),
        "mlflow": http_check(mlflow_url),
    }

    ok = all(results.values())
    out = {"ok": ok, "services": results}
    print(json.dumps(out, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
