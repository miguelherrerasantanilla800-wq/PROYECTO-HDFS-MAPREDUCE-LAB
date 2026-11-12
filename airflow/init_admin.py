#!/usr/bin/env python3
"""Crea el usuario administrador de Airflow solo si todavía no existe."""
import json
import os
import subprocess

username = os.environ.get("AIRFLOW_ADMIN_USERNAME", "admin")
password = os.environ.get("AIRFLOW_ADMIN_PASSWORD", "admin")
users = subprocess.run(
    ["airflow", "users", "list", "--output", "json"],
    check=True,
    capture_output=True,
    text=True,
)
if not isinstance(json.loads(users.stdout), list):
    raise ValueError("Airflow devolvió un listado de usuarios con formato inesperado.")
existing = json.loads(users.stdout)
if any(user.get("username") == username for user in existing):
    print(f"El usuario administrador {username!r} ya existe.")
else:
    subprocess.run(
        [
            "airflow", "users", "create",
            "--username", username,
            "--password", password,
            "--firstname", "Lab",
            "--lastname", "Admin",
            "--role", "Admin",
            "--email", "admin@example.com",
        ],
        check=True,
    )
