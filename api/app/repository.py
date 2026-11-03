from __future__ import annotations

import sqlite3

TASK_COLUMNS = "id,title,description,status,owner,priority,created_at"


def list_tasks_for_owner(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    sql = f"SELECT {TASK_COLUMNS} FROM tasks WHERE owner = ? ORDER BY id"
    return connection.execute(sql, (owner,)).fetchall()


def list_status_and_priority_for_owner(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return connection.execute("SELECT status,priority FROM tasks WHERE owner = ?", (owner,)).fetchall()


def insert_task(
    connection: sqlite3.Connection,
    title: str,
    description: str,
    status: str,
    owner: str,
    priority: str,
) -> sqlite3.Row:
    sql = "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))"
    cursor = connection.execute(sql, (title, description, status, owner, priority))
    connection.commit()
    return connection.execute(f"SELECT {TASK_COLUMNS} FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
