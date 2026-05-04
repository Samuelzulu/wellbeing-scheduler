import pytest
from conftest import task_payload


class TestCreateTask:
    def test_creates_task_returns_201(self, client):
        r = client.post("/tasks/", json=task_payload())
        assert r.status_code == 201

    def test_response_contains_id(self, client):
        r = client.post("/tasks/", json=task_payload())
        assert "id" in r.json()

    def test_response_fields_match_payload(self, client):
        payload = task_payload(title="Essay", priority=5, estimated_minutes=90)
        r = client.post("/tasks/", json=payload)
        data = r.json()
        assert data["title"] == "Essay"
        assert data["priority"] == 5
        assert data["estimated_minutes"] == 90

    def test_optional_fields_default_none(self, client):
        r = client.post("/tasks/", json=task_payload())
        data = r.json()
        assert data["course"] is None
        assert data["notes"] is None

    def test_optional_fields_saved_when_provided(self, client):
        r = client.post("/tasks/", json=task_payload(course="COMP 232", notes="Chapter 4"))
        data = r.json()
        assert data["course"] == "COMP 232"
        assert data["notes"] == "Chapter 4"

    def test_zero_estimated_minutes_rejected(self, client):
        r = client.post("/tasks/", json=task_payload(estimated_minutes=0))
        assert r.status_code == 422

    def test_negative_estimated_minutes_rejected(self, client):
        r = client.post("/tasks/", json=task_payload(estimated_minutes=-10))
        assert r.status_code == 422

    def test_priority_below_range_rejected(self, client):
        r = client.post("/tasks/", json=task_payload(priority=0))
        assert r.status_code == 422

    def test_priority_above_range_rejected(self, client):
        r = client.post("/tasks/", json=task_payload(priority=6))
        assert r.status_code == 422

    def test_priority_boundary_values_accepted(self, client):
        for p in (1, 5):
            r = client.post("/tasks/", json=task_payload(priority=p))
            assert r.status_code == 201

    def test_past_due_date_rejected(self, client):
        r = client.post("/tasks/", json=task_payload(due_date="2000-01-01"))
        assert r.status_code == 422

    def test_missing_required_field_rejected(self, client):
        payload = task_payload()
        del payload["title"]
        r = client.post("/tasks/", json=payload)
        assert r.status_code == 422


class TestListTasks:
    def test_empty_list_on_fresh_db(self, client):
        r = client.get("/tasks/")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_created_tasks(self, client):
        client.post("/tasks/", json=task_payload(title="Task A"))
        client.post("/tasks/", json=task_payload(title="Task B"))
        r = client.get("/tasks/")
        titles = [t["title"] for t in r.json()]
        assert "Task A" in titles
        assert "Task B" in titles

    def test_returns_list_type(self, client):
        r = client.get("/tasks/")
        assert isinstance(r.json(), list)


class TestRetrieveTask:
    def test_retrieve_existing_task(self, client):
        created = client.post("/tasks/", json=task_payload(title="Retrieve me")).json()
        r = client.get(f"/tasks/{created['id']}")
        assert r.status_code == 200
        assert r.json()["title"] == "Retrieve me"

    def test_retrieve_nonexistent_returns_404(self, client):
        r = client.get("/tasks/99999")
        assert r.status_code == 404

    def test_retrieve_returns_correct_id(self, client):
        created = client.post("/tasks/", json=task_payload()).json()
        r = client.get(f"/tasks/{created['id']}")
        assert r.json()["id"] == created["id"]


class TestUpdateTask:
    def test_patch_title(self, client):
        created = client.post("/tasks/", json=task_payload(title="Old")).json()
        r = client.patch(f"/tasks/{created['id']}", json={"title": "New"})
        assert r.status_code == 200
        assert r.json()["title"] == "New"

    def test_patch_priority(self, client):
        created = client.post("/tasks/", json=task_payload(priority=2)).json()
        r = client.patch(f"/tasks/{created['id']}", json={"priority": 5})
        assert r.json()["priority"] == 5

    def test_patch_nonexistent_returns_404(self, client):
        r = client.patch("/tasks/99999", json={"title": "Ghost"})
        assert r.status_code == 404

    def test_patch_preserves_unmentioned_fields(self, client):
        created = client.post("/tasks/", json=task_payload(
            title="Original", priority=3, estimated_minutes=60
        )).json()
        client.patch(f"/tasks/{created['id']}", json={"title": "Updated"})
        r = client.get(f"/tasks/{created['id']}")
        assert r.json()["priority"] == 3
        assert r.json()["estimated_minutes"] == 60


class TestDeleteTask:
    def test_delete_returns_204(self, client):
        created = client.post("/tasks/", json=task_payload()).json()
        r = client.delete(f"/tasks/{created['id']}")
        assert r.status_code == 204

    def test_deleted_task_no_longer_retrievable(self, client):
        created = client.post("/tasks/", json=task_payload()).json()
        client.delete(f"/tasks/{created['id']}")
        r = client.get(f"/tasks/{created['id']}")
        assert r.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        r = client.delete("/tasks/99999")
        assert r.status_code == 404

    def test_delete_removes_only_target(self, client):
        a = client.post("/tasks/", json=task_payload(title="Keep")).json()
        b = client.post("/tasks/", json=task_payload(title="Delete me")).json()
        client.delete(f"/tasks/{b['id']}")
        r = client.get(f"/tasks/{a['id']}")
        assert r.status_code == 200