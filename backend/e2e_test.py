import time
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import ConstraintType

# Set up test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_e2e.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def run_e2e_test():
    print("Starting E2E Validation Test...")
    results = {}
    
    # STEP 1: Reset Environment
    print("[1/10] Resetting environment...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    results["reset"] = "PASSED"

    # STEP 2: Create Test Dataset
    print("[2/10] Creating test dataset...")
    prof_names = [
        "Dr Alpha", "Dr Beta", "Dr Gamma", "Dr Delta",
        "Dr Epsilon", "Dr Zeta", "Dr Eta", "Dr Theta",
        "Dr Iota", "Dr Kappa", "Dr Lambda", "Dr Mu"
    ]
    professors = {}
    for i, name in enumerate(prof_names):
        res = client.post("/api/professors", json={"name": name, "code": f"P{i:02d}"})
        assert res.status_code == 200
        professors[name] = res.json()

    loc_names = ["Ground Floor", "First Floor", "Second Floor", "Third Floor", "Hostel Block"]
    locations = {}
    for name in loc_names:
        res = client.post("/api/locations", json={"name": name})
        assert res.status_code == 200
        locations[name] = res.json()
    results["dataset"] = "PASSED"

    # STEP 3: Configure Settings
    print("[3/10] Configuring settings...")
    start_date = date(2026, 4, 1)
    end_date = date(2026, 4, 30)
    res = client.post("/api/settings", json={
        "start_date": str(start_date),
        "end_date": str(end_date),
        "count_sundays": True
    })
    assert res.status_code == 200
    setting = res.json()
    results["settings"] = "PASSED"

    # STEP 4: Add Constraints
    print("[4/10] Adding realistic constraints...")
    constraints = [
        {"prof": "Dr Alpha", "type": ConstraintType.DAY_UNAVAILABLE, "value": {"dayOfWeek": "Monday"}},
        {"prof": "Dr Beta", "type": ConstraintType.DAY_PREFERRED, "value": {"dayOfWeek": "Friday"}},
        {"prof": "Dr Gamma", "type": ConstraintType.LOCATION_RESTRICTED, "value": {"location_id": locations["Third Floor"]["id"]}},
        {"prof": "Dr Delta", "type": ConstraintType.MAX_WEEKLY, "value": {"limit": 3}},
        {"prof": "Dr Zeta", "type": ConstraintType.DAY_UNAVAILABLE, "value": {"dayOfWeek": "Sunday"}}
    ]
    for c in constraints:
        res = client.post("/api/constraints", json={
            "professor_id": professors[c["prof"]]["id"],
            "type": c["type"],
            "value": c["value"]
        })
        assert res.status_code == 200
    results["constraints"] = "PASSED"

    # STEP 5: Generate Schedule
    print("[5/10] Generating schedule...")
    start_time = time.time()
    res = client.post(f"/api/generate-roster?setting_id={setting['id']}")
    solve_time = time.time() - start_time
    assert res.status_code == 200, f"Failed to generate: {res.text}"
    results["generation"] = "PASSED"
    results["solve_time"] = solve_time

    # STEP 6: Verify Correctness
    print("[6/10] Verifying correctness...")
    res = client.get("/api/roster")
    assert res.status_code == 200
    roster = res.json()

    # Verify 1: Exactly one assignment per slot
    slots = {}
    for a in roster:
        key = (a["date"], a["location_id"])
        assert key not in slots, "Duplicate assignment for slot"
        slots[key] = a["professor_id"]
    
    # Verify 2: No professor twice on same date
    prof_days = {}
    for a in roster:
        key = (a["professor_id"], a["date"])
        assert key not in prof_days, "Professor double booked"
        prof_days[key] = a["location_id"]

    # Verify 3, 4: Constraints respected
    for a in roster:
        d = date.fromisoformat(a["date"])
        if a["professor_id"] == professors["Dr Alpha"]["id"]:
            assert d.strftime("%A") != "Monday"
        if a["professor_id"] == professors["Dr Zeta"]["id"]:
            assert d.strftime("%A") != "Sunday"
        if a["professor_id"] == professors["Dr Gamma"]["id"]:
            assert a["location_id"] != locations["Third Floor"]["id"]

    # Verify 5, 6: Fairness
    prof_counts = {}
    for a in roster:
        prof_counts[a["professor_id"]] = prof_counts.get(a["professor_id"], 0) + 1
    
    for p_id, count in prof_counts.items():
        assert 12 <= count <= 13, f"Fairness violation: Prof {p_id} has {count} duties"
    
    results["correctness"] = "PASSED"
    results["fairness"] = prof_counts

    # STEP 7: Verify Frontend Compatibility
    print("[7/10] Verifying frontend compatibility...")
    for a in roster:
        assert "date" in a
        assert "location_id" in a
        assert "professor_id" in a
    results["frontend_compat"] = "PASSED"

    # STEP 8: Export Testing
    print("[8/10] Export testing...")
    res_csv = client.get("/api/export/csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    
    res_pdf = client.get("/api/export/pdf")
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    results["export"] = "PASSED"

    # STEP 9: Final Integrity Check
    print("[9/10] Final integrity check...")
    expected_assignments = 30 * 5  # 30 days * 5 locations
    assert len(roster) == expected_assignments, f"Expected {expected_assignments}, got {len(roster)}"
    results["integrity"] = "PASSED"

    # STEP 10: Output Test Report
    print("\n" + "="*40)
    print("E2E TEST REPORT")
    print("="*40)
    for k, v in results.items():
        if k == "fairness":
            print("Fairness Distribution:")
            for p_name, p_data in professors.items():
                print(f"  - {p_name}: {v.get(p_data['id'], 0)} duties")
        elif k == "solve_time":
            print(f"Solver Runtime: {v:.3f} seconds")
        else:
            print(f"{k.capitalize()}: {v}")
    
    print("="*40)
    print("All tests passed successfully.")

if __name__ == "__main__":
    run_e2e_test()
