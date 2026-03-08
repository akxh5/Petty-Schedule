from datetime import date
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app import models
from app.services.scheduler.solver import generate_schedule

def seed_and_test():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 1. Add 9 Professors
    profs_data = [
        {"name": "Dr Sharma", "code": "P1"},
        {"name": "Dr Gupta", "code": "P2"},
        {"name": "Dr Singh", "code": "P3"},
        {"name": "Dr Verma", "code": "P4"},
        {"name": "Dr Reddy", "code": "P5"},
        {"name": "Dr Rao", "code": "P6"},
        {"name": "Dr Patel", "code": "P7"},
        {"name": "Dr Kumar", "code": "P8"},
        {"name": "Dr Nair", "code": "P9"},
    ]
    profs = []
    for pd in profs_data:
        p = models.Professor(**pd)
        db.add(p)
        profs.append(p)
        
    # 2. Add 3 Locations
    locs_data = ["Ground Floor Mess", "1st Floor Mess", "2nd & 3rd Floor Mess"]
    locs = []
    for ld in locs_data:
        l = models.Location(name=ld)
        db.add(l)
        locs.append(l)
        
    db.commit()
    
    # 3. Add Settings (Feb 1 2026 to Feb 28 2026) -> 28 days -> 84 slots
    s = models.DutySetting(start_date=date(2026, 2, 1), end_date=date(2026, 2, 28))
    db.add(s)
    db.commit()
    
    # 4. Add Constraints
    # Sharma Cannot work Monday
    c1 = models.Constraint(professor_id=profs[0].id, type=models.ConstraintType.DAY_UNAVAILABLE, value={"dayOfWeek": "Monday"})
    # Gupta prefers Friday
    c2 = models.Constraint(professor_id=profs[1].id, type=models.ConstraintType.DAY_PREFERRED, value={"dayOfWeek": "Friday"})
    
    db.add(c1)
    db.add(c2)
    db.commit()
    
    print("Seed Complete. Testing OR-Tools generation...")
    
    try:
        res = generate_schedule(db, s.id)
        print(res)
        
        # Verify Fairness
        assignments = db.query(models.RosterAssignment).all()
        counts = {}
        for a in assignments:
            counts[a.professor_id] = counts.get(a.professor_id, 0) + 1
            
        print("Duty Distribution:")
        for p in profs:
            print(f"{p.name}: {counts.get(p.id, 0)} duties")
    except Exception as e:
        print("Err:", str(e))
        
if __name__ == "__main__":
    seed_and_test()
