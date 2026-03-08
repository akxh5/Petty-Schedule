import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
import os

from app.main import app
from app.database import Base, get_db
from app.models import ConstraintType

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_full_scheduling_cycle():
    # 1. Add 12 professors
    professors = []
    for i in range(1, 13):
        response = client.post("/api/professors", json={"name": f"Dr Test {i}", "code": f"DR{i:02d}"})
        assert response.status_code == 200
        professors.append(response.json())

    # 2. Add 3 duty locations (to have 84 slots, which makes min_duties=7)
    locations_names = ["Ground Floor", "1st Floor", "2nd Floor"]
    locations = []
    for name in locations_names:
        response = client.post("/api/locations", json={"name": name})
        assert response.status_code == 200
        locations.append(response.json())

    # 3. Configure settings
    start_date = date(2026, 2, 1)
    end_date = date(2026, 2, 28)
    setting_payload = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "count_sundays": True
    }
    response = client.post("/api/settings", json=setting_payload)
    assert response.status_code == 200
    setting = response.json()

    # 4. Add Constraints
    # Dr Test 1 → cannot work Monday
    client.post("/api/constraints", json={
        "professor_id": professors[0]["id"],
        "type": ConstraintType.DAY_UNAVAILABLE,
        "value": {"dayOfWeek": "Monday"}
    })
    # Dr Test 2 → prefers Friday
    client.post("/api/constraints", json={
        "professor_id": professors[1]["id"],
        "type": ConstraintType.DAY_PREFERRED,
        "value": {"dayOfWeek": "Friday"}
    })
    # Dr Test 3 → max 2 duties per week (8 total in Feb)
    client.post("/api/constraints", json={
        "professor_id": professors[2]["id"],
        "type": ConstraintType.MAX_WEEKLY,
        "value": {"limit": 2}
    })
    # Dr Test 4 → restricted from 2nd floor
    floor_2_id = next(l["id"] for l in locations if l["name"] == "2nd Floor")
    client.post("/api/constraints", json={
        "professor_id": professors[3]["id"],
        "type": ConstraintType.LOCATION_RESTRICTED,
        "value": {"location_id": floor_2_id}
    })

    # Step 3 — Generate Schedule
    response = client.post(f"/api/generate-roster?setting_id={setting['id']}")
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200

    # Retrieve roster
    response = client.get("/api/roster")
    assert response.status_code == 200
    roster = response.json()

    # Step 4 — Verify Correctness
    # 1. Every slot (date + location) has exactly one professor assigned.
    # Total days = 28. Total locations = 3. Total slots = 84.
    assert len(roster) == 84

    slots = {}
    for entry in roster:
        key = (entry["date"], entry["location_id"])
        assert key not in slots, f"Duplicate assignment for {key}"
        slots[key] = entry["professor_id"]

    # 2. No professor is assigned to more than one location on the same day.
    prof_days = {}
    for entry in roster:
        key = (entry["professor_id"], entry["date"])
        assert key not in prof_days, f"Professor {entry['professor_id']} assigned twice on {entry['date']}"
        prof_days[key] = entry["location_id"]

    # 3. All DAY_UNAVAILABLE constraints are respected.
    for entry in roster:
        if entry["professor_id"] == professors[0]["id"]:
            d = date.fromisoformat(entry["date"])
            assert d.strftime("%A") != "Monday"

    # 4. LOCATION_RESTRICTED constraints are respected.
    for entry in roster:
        if entry["professor_id"] == professors[3]["id"]:
            assert entry["location_id"] != floor_2_id

    # 5. Fairness distribution: 84 / 12 = 7. Expected 7 duties per prof.
    prof_counts = {}
    for entry in roster:
        p_id = entry["professor_id"]
        prof_counts[p_id] = prof_counts.get(p_id, 0) + 1

    for p_id, count in prof_counts.items():
        assert count == 7

def test_sunday_constraint():
    p1 = client.post("/api/professors", json={"name": "P1", "code": "P1"}).json()
    p2 = client.post("/api/professors", json={"name": "P2", "code": "P2"}).json()
    l1 = client.post("/api/locations", json={"name": "L1"}).json()
    
    start_date = date(2026, 2, 1) # Sunday
    end_date = date(2026, 2, 7) # Saturday
    setting = client.post("/api/settings", json={
        "start_date": str(start_date),
        "end_date": str(end_date),
        "count_sundays": False
    }).json()
    
    response = client.post(f"/api/generate-roster?setting_id={setting['id']}")
    assert response.status_code == 200
    
    roster = client.get("/api/roster").json()
    for entry in roster:
        d = date.fromisoformat(entry["date"])
        assert d.weekday() != 6

def test_export_endpoints():
    client.post("/api/professors", json={"name": "P1", "code": "P1"})
    client.post("/api/locations", json={"name": "L1"})
    setting = client.post("/api/settings", json={
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "count_sundays": True
    }).json()
    client.post(f"/api/generate-roster?setting_id={setting['id']}")
    
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    
    response = client.get("/api/export/pdf")
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
