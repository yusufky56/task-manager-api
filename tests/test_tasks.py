from datetime import date, timedelta

from tests.conftest import register_and_login


def create(client, headers, **fields):
    payload = {"title": "Task", **fields}
    res = client.post("/tasks", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_and_get_task(client, auth_headers):
    task = create(client, auth_headers, title="Write report", priority="high")
    assert task["status"] == "todo"
    assert task["priority"] == "high"

    res = client.get(f"/tasks/{task['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Write report"


def test_update_task(client, auth_headers):
    task = create(client, auth_headers)
    res = client.patch(f"/tasks/{task['id']}", json={"status": "done"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "done"
    assert res.json()["title"] == "Task"


def test_delete_task(client, auth_headers):
    task = create(client, auth_headers)
    assert client.delete(f"/tasks/{task['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/tasks/{task['id']}", headers=auth_headers).status_code == 404


def test_users_cannot_see_each_others_tasks(client, auth_headers):
    task = create(client, auth_headers)
    other = register_and_login(client, email="other@example.com")

    assert client.get(f"/tasks/{task['id']}", headers=other).status_code == 404
    assert client.patch(f"/tasks/{task['id']}", json={"title": "x"}, headers=other).status_code == 404
    assert client.delete(f"/tasks/{task['id']}", headers=other).status_code == 404
    assert client.get("/tasks", headers=other).json()["total"] == 0


def test_filter_search_and_pagination(client, auth_headers):
    create(client, auth_headers, title="Buy milk", priority="low")
    create(client, auth_headers, title="Fix login bug", priority="high", status="in_progress")
    create(client, auth_headers, title="Fix signup bug", priority="high")
    for i in range(5):
        create(client, auth_headers, title=f"Chore {i}")

    res = client.get("/tasks", params={"priority": "high"}, headers=auth_headers).json()
    assert res["total"] == 2

    res = client.get("/tasks", params={"status": "in_progress"}, headers=auth_headers).json()
    assert [t["title"] for t in res["items"]] == ["Fix login bug"]

    res = client.get("/tasks", params={"q": "bug"}, headers=auth_headers).json()
    assert res["total"] == 2

    page = client.get("/tasks", params={"limit": 3, "offset": 6}, headers=auth_headers).json()
    assert page["total"] == 8
    assert len(page["items"]) == 2


def test_sort_by_title(client, auth_headers):
    for title in ["b", "c", "a"]:
        create(client, auth_headers, title=title)
    res = client.get("/tasks", params={"sort": "title", "order": "asc"}, headers=auth_headers).json()
    assert [t["title"] for t in res["items"]] == ["a", "b", "c"]


def test_stats(client, auth_headers):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    create(client, auth_headers, due_date=yesterday)
    create(client, auth_headers, due_date=yesterday, status="done")
    create(client, auth_headers, status="in_progress")

    stats = client.get("/tasks/stats", headers=auth_headers).json()
    assert stats["total"] == 3
    assert stats["by_status"] == {"todo": 1, "in_progress": 1, "done": 1}
    assert stats["overdue"] == 1


def test_validation_errors(client, auth_headers):
    assert client.post("/tasks", json={"title": ""}, headers=auth_headers).status_code == 422
    assert client.post("/tasks", json={"title": "x", "priority": "urgent"}, headers=auth_headers).status_code == 422
    assert client.get("/tasks", params={"limit": 500}, headers=auth_headers).status_code == 422


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
