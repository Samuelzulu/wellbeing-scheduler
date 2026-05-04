import pytest
from conftest import task_payload, event_payload, plan_payload


class TestGeneratePlan:
    def test_generate_returns_201(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        assert r.status_code == 201

    def test_response_contains_id_and_week_start(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        data = r.json()
        assert "id" in data
        assert "week_start" in data

    def test_response_contains_blocks(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        data = r.json()
        assert "blocks" in data
        assert isinstance(data["blocks"], list)
        assert len(data["blocks"]) > 0

    def test_blocks_have_required_fields(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        for block in r.json()["blocks"]:
            assert "day" in block
            assert "start_time" in block
            assert "end_time" in block
            assert "category" in block

    def test_balance_score_between_0_and_1(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        score = r.json()["weekly_balance_score"]
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_sleep_blocks_present(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        categories = [b["category"] for b in r.json()["blocks"]]
        assert any(c == "sleep" for c in categories)

    def test_meal_blocks_present(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        categories = [b["category"] for b in r.json()["blocks"]]
        assert any(c == "meal" for c in categories)

    def test_workout_blocks_present(self, client):
        r = client.post("/plans/generate", json=plan_payload())
        categories = [b["category"] for b in r.json()["blocks"]]
        assert any(c == "workout" for c in categories)

    def test_study_blocks_present_when_tasks_exist(self, client):
        client.post("/tasks/", json=task_payload(title="COMP 232", estimated_minutes=120))
        r = client.post("/plans/generate", json=plan_payload())
        categories = [b["category"] for b in r.json()["blocks"]]
        assert any(c.startswith("study:") for c in categories)

    def test_generate_with_zero_workouts(self, client):
        r = client.post("/plans/generate", json=plan_payload(workouts=0))
        assert r.status_code == 201
        categories = [b["category"] for b in r.json()["blocks"]]
        assert not any(c == "workout" for c in categories)

    def test_generate_with_custom_block_minutes(self, client):
        r = client.post("/plans/generate", json=plan_payload(block_minutes=30))
        assert r.status_code == 201

    def test_invalid_sleep_rejected(self, client):
        r = client.post("/plans/generate", json=plan_payload(sleep=0))
        assert r.status_code == 422

    def test_negative_workouts_rejected(self, client):
        r = client.post("/plans/generate", json=plan_payload(workouts=-1))
        assert r.status_code == 422

    def test_zero_block_minutes_rejected(self, client):
        r = client.post("/plans/generate", json=plan_payload(block_minutes=0))
        assert r.status_code == 422

    def test_each_generated_plan_gets_unique_id(self, client):
        id1 = client.post("/plans/generate", json=plan_payload()).json()["id"]
        id2 = client.post("/plans/generate", json=plan_payload()).json()["id"]
        assert id1 != id2


class TestListPlans:
    def test_empty_list_on_fresh_db(self, client):
        r = client.get("/plans/")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_summary_after_generation(self, client):
        client.post("/plans/generate", json=plan_payload())
        r = client.get("/plans/")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_summary_does_not_include_blocks(self, client):
        client.post("/plans/generate", json=plan_payload())
        r = client.get("/plans/")
        for plan in r.json():
            assert "blocks" not in plan

    def test_multiple_plans_all_listed(self, client):
        client.post("/plans/generate", json=plan_payload())
        client.post("/plans/generate", json=plan_payload())
        r = client.get("/plans/")
        assert len(r.json()) == 2


class TestRetrievePlan:
    def test_retrieve_existing_plan(self, client):
        created = client.post("/plans/generate", json=plan_payload()).json()
        r = client.get(f"/plans/{created['id']}")
        assert r.status_code == 200

    def test_retrieve_includes_blocks(self, client):
        created = client.post("/plans/generate", json=plan_payload()).json()
        r = client.get(f"/plans/{created['id']}")
        assert "blocks" in r.json()
        assert len(r.json()["blocks"]) > 0

    def test_retrieve_nonexistent_returns_404(self, client):
        r = client.get("/plans/99999")
        assert r.status_code == 404

    def test_retrieved_id_matches_created(self, client):
        created = client.post("/plans/generate", json=plan_payload()).json()
        r = client.get(f"/plans/{created['id']}")
        assert r.json()["id"] == created["id"]