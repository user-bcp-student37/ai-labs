import base64
import http.server
import socket
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

OTHER_OWNER_TASK_TITLE = "Trainer notes"
UNAUTHORIZED_DETAIL = {"detail": "Invalid token: invalid token"}


def token(username: str = "student", role: str = "STUDENT") -> str:
    raw = f"{username}|{role}|{int(time.time()) + 3600}|WORKSHOP_SECRET_2026"
    return base64.b64encode(raw.encode()).decode()


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_lists_only_authenticated_owner_tasks_in_id_order(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    tasks = response.json()
    assert response.status_code == 200
    assert [task["owner"] for task in tasks] == ["student", "student"]
    assert [task["id"] for task in tasks] == sorted(task["id"] for task in tasks)


def test_filters_tasks_by_owner_query(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers(), params={"owner": "trainer"})
    assert response.status_code == 200
    assert [task["owner"] for task in response.json()] == ["trainer"]


def test_owner_with_apostrophe_is_matched_as_literal(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers(), params={"owner": "O'Brien"})
    assert response.status_code == 200
    assert response.json() == []


def test_owner_injection_does_not_widen_filter(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers(), params={"owner": "x' OR '1'='1"})
    assert response.status_code == 200
    assert response.json() == []


def test_summary_counts_seeded_owner_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_summary_excludes_done_and_archived_from_high_priority_open(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        for status in ("DONE", "ARCHIVED"):
            client.post("/api/tasks", headers=headers(), json={"title": status, "description": "x", "status": status, "priority": "HIGH"})
        response = client.get("/api/summary", headers=headers())
    body = response.json()
    assert body["total"] == 4
    assert body["byStatus"] == {"TODO": 1, "IN_PROGRESS": 1, "DONE": 1, "ARCHIVED": 1}
    assert body["highPriorityOpen"] == 1


def test_summary_for_other_owner_query(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers(), params={"owner": "trainer"})
    assert response.status_code == 200
    assert response.json() == {"owner": "trainer", "total": 1, "byStatus": {"TODO": 1}, "highPriorityOpen": 0}


def test_summary_owner_with_apostrophe_is_matched_as_literal(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers(), params={"owner": "O'Brien"})
    assert response.status_code == 200
    assert response.json() == {"owner": "O'Brien", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


def test_summary_owner_injection_does_not_widen_count(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers(), params={"owner": "x' OR '1'='1"})
    assert response.status_code == 200
    assert response.json() == {"owner": "x' OR '1'='1", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


def test_create_applies_observed_defaults(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "Defaults", "description": "d"})
    body = response.json()
    assert response.status_code == 201
    assert (body["status"], body["priority"], body["owner"]) == ("TODO", "MEDIUM", "student")
    assert body["createdAt"]


def test_create_keeps_owner_from_body_when_present(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "T", "description": "d", "owner": "trainer"})
    assert response.status_code == 201
    assert response.json()["owner"] == "trainer"


def test_create_coerces_non_string_fields_to_text(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": 123, "description": "d"})
    assert response.status_code == 201
    assert response.json()["title"] == "123"


def test_create_stores_apostrophe_in_title_as_literal(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "O'Brien review", "description": "d"})
    assert response.status_code == 201
    assert response.json()["title"] == "O'Brien review"


def test_create_injection_payload_is_stored_as_text(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    payload = "x'); DELETE FROM tasks; --"
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": payload, "description": "d"})
        summary = client.get("/api/summary", headers=headers())
    assert response.status_code == 201
    assert summary.json()["total"] == 3


def test_rejects_expired_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    raw = f"student|STUDENT|{int(time.time()) - 10}|WORKSHOP_SECRET_2026"
    expired = base64.b64encode(raw.encode()).decode()
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_rejects_token_signed_with_other_secret(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    raw = f"student|ADMIN|{int(time.time()) + 3600}|OTHER_SECRET"
    forged = base64.b64encode(raw.encode()).decode()
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_rejects_malformed_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    malformed = base64.b64encode(b"student|STUDENT|999999999999").decode()
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {malformed}"})
    assert response.status_code == 401


def test_rejects_missing_authorization_header(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks")
    assert response.status_code == 401


def _app(tmp_path: Path, upload_dir: Path | None = None):
    return create_app(str(tmp_path / "workshop.db"), str(upload_dir or tmp_path / "uploads"))


@pytest.fixture
def health_server() -> Iterator[Callable[[int, bytes], str]]:
    servers: list[http.server.HTTPServer] = []

    def start(status: int, body: bytes) -> str:
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self.send_response(status)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args: object) -> None:
                return

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        servers.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{server.server_port}/q/health"

    yield start
    for server in servers:
        server.shutdown()
        server.server_close()


def _closed_local_url() -> str:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return f"http://127.0.0.1:{port}/q/health"


# GET /api/tasks: camino feliz, borde y errores


def test_list_empty_owner_query_falls_back_to_token_user(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/tasks", headers=headers(), params={"owner": ""})
    assert response.status_code == 200
    assert {task["owner"] for task in response.json()} == {"student"}


def test_list_returns_empty_array_for_owner_without_tasks(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/tasks", headers=headers(), params={"owner": "nobody"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_requires_authorization_header(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/tasks", params={"owner": "student"})
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL


@pytest.mark.xfail(strict=True, reason="H-API-05 pendiente: owner de la query reemplaza la identidad del token (api/app/main.py:89)")
def test_list_denies_reading_another_owner_tasks(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/tasks", headers=headers(), params={"owner": "trainer"})
    assert OTHER_OWNER_TASK_TITLE not in [task["title"] for task in response.json()]


# POST /api/tasks: camino feliz, borde y errores


def test_create_with_empty_payload_applies_all_defaults(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/tasks", headers=headers(), json={})
    body = response.json()
    assert response.status_code == 201
    assert (body["title"], body["description"], body["status"], body["priority"], body["owner"]) == (
        "",
        "",
        "TODO",
        "MEDIUM",
        "student",
    )


def test_create_accepts_empty_title_as_observed(tmp_path: Path) -> None:
    # Caracterizacion del comportamiento actual; no aprobado. Ver H-API-12 en HALLAZGOS.md.
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "", "description": "d"})
    assert response.status_code == 201
    assert response.json()["title"] == ""


def test_create_stores_null_owner_as_none_text_as_observed(tmp_path: Path) -> None:
    # Caracterizacion del comportamiento actual; no aprobado. Ver pregunta abierta 3 en docs/ENDPOINTS.md.
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "N", "owner": None})
    assert response.status_code == 201
    assert response.json()["owner"] == "None"


def test_create_rejects_non_object_body_with_422(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/tasks", headers=headers(), json=["x"])
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]


def test_create_requires_authorization_header(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/tasks", json={"title": "x", "description": "d"})
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL


@pytest.mark.xfail(strict=True, reason="H-API-05 pendiente: owner del body reemplaza la identidad del token (api/app/main.py:94)")
def test_create_denies_writing_task_for_another_owner(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "x", "description": "d", "owner": "trainer"})
    assert response.status_code == 403 or response.json()["owner"] == "student"


# GET /api/summary: camino feliz, borde y errores


def test_summary_empty_owner_query_falls_back_to_token_user(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/summary", headers=headers(), params={"owner": ""})
    assert response.status_code == 200
    assert response.json()["owner"] == "student"
    assert response.json()["total"] == 2


def test_summary_requires_authorization_header(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/summary")
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL


@pytest.mark.xfail(strict=True, reason="H-API-05 pendiente: owner de la query reemplaza la identidad del token (api/app/main.py:100)")
def test_summary_denies_reading_another_owner_summary(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/summary", headers=headers(), params={"owner": "trainer"})
    assert response.status_code == 403 or response.json()["total"] == 0


# POST /api/requirements: camino feliz, borde y errores


def test_upload_accepts_file_without_extension_as_observed(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    with TestClient(_app(tmp_path, upload_dir)) as client:
        response = client.post("/api/requirements", headers=headers(), files={"file": ("LEEME", b"nota", "application/octet-stream")})
    assert response.status_code == 201
    assert (upload_dir / "LEEME").read_bytes() == b"nota"


def test_upload_accepts_empty_file_with_size_zero(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/requirements", headers=headers(), files={"file": ("vacio.txt", b"", "text/plain")})
    assert response.status_code == 201
    assert response.json()["size"] == 0


def test_upload_accepts_one_mebibyte_as_observed_without_limit(tmp_path: Path) -> None:
    # Caracterizacion: no existe limite de tamano en el codigo (api/app/main.py:107). Pendiente de acuerdo.
    payload = b"a" * (1024 * 1024)
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/requirements", headers=headers(), files={"file": ("grande.txt", payload, "text/plain")})
    assert response.status_code == 201
    assert response.json()["size"] == len(payload)


def test_upload_requires_file_field_with_422(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/requirements", headers=headers())
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]


def test_upload_requires_authorization_header(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.post("/api/requirements", files={"file": ("r.txt", b"x", "text/plain")})
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL


def test_upload_write_failure_returns_500(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    (upload_dir / "bloqueado.txt").mkdir(parents=True)
    with TestClient(_app(tmp_path, upload_dir), raise_server_exceptions=False) as client:
        response = client.post("/api/requirements", headers=headers(), files={"file": ("bloqueado.txt", b"x", "text/plain")})
    assert response.status_code == 500


@pytest.mark.xfail(strict=True, reason="H-API-06 pendiente: file.filename sin normalizar (api/app/main.py:106)")
def test_upload_filename_cannot_escape_upload_dir(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        client.post("/api/requirements", headers=headers(), files={"file": ("../escape.txt", b"x", "text/plain")})
    assert not (tmp_path / "escape.txt").exists()


# GET /api/backend-health: camino feliz, borde y errores


def test_backend_health_reports_upstream_status_and_body(tmp_path: Path, health_server, monkeypatch) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", health_server(200, b'{"status":"UP"}'))
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}


def test_backend_health_passes_upstream_error_status_through(tmp_path: Path, health_server, monkeypatch) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", health_server(503, b"DOWN"))
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 503, "body": "DOWN"}


def test_backend_health_returns_status_zero_when_unreachable(tmp_path: Path, monkeypatch) -> None:
    # Caracterizacion: el texto de la excepcion llega al cliente (H-API-09). Solo se afirma status 0 y body no vacio.
    monkeypatch.setenv("AUTH_HEALTH_URL", _closed_local_url())
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/backend-health", headers=headers())
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == 0
    assert body["requestedBy"] == "student"
    assert body["body"]


def test_backend_health_requires_authorization_header(tmp_path: Path) -> None:
    with TestClient(_app(tmp_path)) as client:
        response = client.get("/api/backend-health")
    assert response.status_code == 401
    assert response.json() == UNAUTHORIZED_DETAIL
