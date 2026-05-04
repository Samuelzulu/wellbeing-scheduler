import pytest
from conftest import event_payload


class TestCreateEvent:
    def test_creates_event_returns_201(self, client):
        r = client.post("/events/", json=event_payload())
        assert r.status_code == 201

    def test_response_contains_id(self, client):
        r = client.post("/events/", json=event_payload())
        assert "id" in r.json()

    def test_response_fields_match_payload(self, client):
        r = client.post("/events/", json=event_payload(name="Lab", category="lab"))
        data = r.json()
        assert data["name"] == "Lab"
        assert data["category"] == "lab"

    def test_optional_category_defaults_none(self, client):
        payload = event_payload()
        del payload["category"]
        r = client.post("/events/", json=payload)
        assert r.json()["category"] is None

    def test_end_time_before_start_rejected(self, client):
        r = client.post("/events/", json=event_payload(
            start_time="10:00:00", end_time="09:00:00"
        ))
        assert r.status_code == 422

    def test_end_time_equal_start_rejected(self, client):
        r = client.post("/events/", json=event_payload(
            start_time="10:00:00", end_time="10:00:00"
        ))
        assert r.status_code == 422

    def test_missing_name_rejected(self, client):
        payload = event_payload()
        del payload["name"]
        r = client.post("/events/", json=payload)
        assert r.status_code == 422


class TestListEvents:
    def test_empty_list_on_fresh_db(self, client):
        r = client.get("/events/")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_created_events(self, client):
        client.post("/events/", json=event_payload(name="Lecture"))
        client.post("/events/", json=event_payload(name="Lab"))
        r = client.get("/events/")
        names = [e["name"] for e in r.json()]
        assert "Lecture" in names
        assert "Lab" in names


class TestRetrieveEvent:
    def test_retrieve_existing(self, client):
        created = client.post("/events/", json=event_payload(name="Find me")).json()
        r = client.get(f"/events/{created['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Find me"

    def test_retrieve_nonexistent_returns_404(self, client):
        r = client.get("/events/99999")
        assert r.status_code == 404


class TestDeleteEvent:
    def test_delete_returns_204(self, client):
        created = client.post("/events/", json=event_payload()).json()
        r = client.delete(f"/events/{created['id']}")
        assert r.status_code == 204

    def test_deleted_event_no_longer_retrievable(self, client):
        created = client.post("/events/", json=event_payload()).json()
        client.delete(f"/events/{created['id']}")
        r = client.get(f"/events/{created['id']}")
        assert r.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        r = client.delete("/events/99999")
        assert r.status_code == 404