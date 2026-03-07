import os
import io
import csv
from typing import List
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

from . import models, schemas, database
from .services.scheduler import solver

# Ensure DB tables are created
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Faculty Duty Scheduler API")

# Add CORS Middleware
from fastapi.middleware.cors import CORSMiddleware
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        frontend_url
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

router = APIRouter(redirect_slashes=False)

# --- Professors ---
@router.post("/professors", response_model=schemas.Professor)
def create_professor(prof: schemas.ProfessorCreate, db: Session = Depends(database.get_db)):
    db_prof = models.Professor(**prof.model_dump())
    db.add(db_prof)
    db.commit()
    db.refresh(db_prof)
    return db_prof

@router.get("/professors", response_model=List[schemas.ProfessorWithDetails])
def read_professors(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Professor).offset(skip).limit(limit).all()

@router.delete("/professors/{professor_id}")
def delete_professor(professor_id: str, db: Session = Depends(database.get_db)):
    db_prof = db.query(models.Professor).filter(models.Professor.id == professor_id).first()
    if not db_prof:
        raise HTTPException(status_code=404, detail="Professor not found")
    db.delete(db_prof)
    db.commit()
    return {"status": "success"}

# --- Locations ---
@router.post("/locations", response_model=schemas.Location)
def create_location(loc: schemas.LocationCreate, db: Session = Depends(database.get_db)):
    db_loc = models.Location(**loc.model_dump())
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc

@router.get("/locations", response_model=List[schemas.Location])
def read_locations(db: Session = Depends(database.get_db)):
    return db.query(models.Location).all()

@router.delete("/locations/{location_id}")
def delete_location(location_id: str, db: Session = Depends(database.get_db)):
    db_loc = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not db_loc:
        raise HTTPException(status_code=404, detail="Location not found")
    db.delete(db_loc)
    db.commit()
    return {"status": "success"}

# --- Constraints ---
@router.post("/constraints", response_model=schemas.Constraint)
def create_constraint(constraint: schemas.ConstraintCreate, db: Session = Depends(database.get_db)):
    if constraint.type in (models.ConstraintType.DAY_UNAVAILABLE, models.ConstraintType.DAY_PREFERRED):
        day_of_week = constraint.value.get("dayOfWeek")
        if day_of_week:
            conflict_type = models.ConstraintType.DAY_PREFERRED if constraint.type == models.ConstraintType.DAY_UNAVAILABLE else models.ConstraintType.DAY_UNAVAILABLE
            existing = db.query(models.Constraint).filter(
                models.Constraint.professor_id == constraint.professor_id,
                models.Constraint.type == conflict_type
            ).all()
            for ec in existing:
                if ec.value.get("dayOfWeek") == day_of_week:
                    raise HTTPException(status_code=400, detail="Conflicting constraint already exists for this professor and day.")

    db_constraint = models.Constraint(**constraint.model_dump())
    db.add(db_constraint)
    db.commit()
    db.refresh(db_constraint)
    return db_constraint

@router.get("/constraints", response_model=List[schemas.Constraint])
def read_constraints(db: Session = Depends(database.get_db)):
    return db.query(models.Constraint).all()

@router.delete("/constraints/{constraint_id}")
def delete_constraint(constraint_id: str, db: Session = Depends(database.get_db)):
    db_constraint = db.query(models.Constraint).filter(models.Constraint.id == constraint_id).first()
    if not db_constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    db.delete(db_constraint)
    db.commit()
    return {"status": "success"}

# --- Settings ---
@router.post("/settings", response_model=schemas.DutySetting)
def create_setting(setting: schemas.DutySettingCreate, db: Session = Depends(database.get_db)):
    db_setting = models.DutySetting(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.get("/settings", response_model=List[schemas.DutySetting])
def read_settings(db: Session = Depends(database.get_db)):
    return db.query(models.DutySetting).all()

# --- Schedule Assignments ---
@router.get("/roster", response_model=List[schemas.RosterAssignment])
def get_roster(db: Session = Depends(database.get_db)):
    return db.query(models.RosterAssignment).order_by(models.RosterAssignment.date.asc()).all()

@router.get("/roster/diagnostics")
def get_diagnostics(setting_id: str, db: Session = Depends(database.get_db)):
    try:
        return solver.check_feasibility(db, setting_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-roster")
def build_roster(setting_id: str, db: Session = Depends(database.get_db)):
    try:
        result = solver.generate_schedule(db, setting_id)
        return result
    except solver.SchedulingError as e:
        import json
        try:
            err_data = json.loads(str(e))
            raise HTTPException(status_code=400, detail=err_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal scheduling error: {str(e)}")

@router.get("/export/csv")
def export_csv(db: Session = Depends(database.get_db)):
    assignments = db.query(models.RosterAssignment).order_by(models.RosterAssignment.date.asc()).all()
    locations = db.query(models.Location).all()
    professors = db.query(models.Professor).all()
    prof_map = {p.id: p.name for p in professors}
    
    grouped = {}
    for a in assignments:
        if a.date not in grouped:
            grouped[a.date] = {}
        grouped[a.date][a.location_id] = prof_map.get(a.professor_id, "Unknown")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = ["Date"] + [loc.name for loc in locations]
    
    current_week = None
    import math
    
    for d in sorted(grouped.keys()):
        week_num = math.ceil(d.day / 7)
        if current_week != week_num:
            if current_week is not None:
                writer.writerow([]) # Empty row space
            writer.writerow([f"Week {week_num}"])
            writer.writerow(headers)
            current_week = week_num
            
        row = [str(d)]
        for loc in locations:
            row.append(grouped[d].get(loc.id, "-"))
        writer.writerow(row)
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=roster.csv"}
    )

@router.get("/export/pdf")
def export_pdf(db: Session = Depends(database.get_db)):
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    
    assignments = db.query(models.RosterAssignment).order_by(models.RosterAssignment.date.asc()).all()
    locations = db.query(models.Location).all()
    professors = db.query(models.Professor).all()
    prof_map = {p.id: p.name for p in professors}
    
    grouped = {}
    for a in assignments:
        if a.date not in grouped:
            grouped[a.date] = {}
        grouped[a.date][a.location_id] = prof_map.get(a.professor_id, "Unknown")
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    import math
    current_week = None
    current_table_data = []
    
    headers = ["Date"] + [loc.name for loc in locations]
    
    def flush_table():
        if len(current_table_data) > 1:
            table = Table(current_table_data)
            style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ])
            table.setStyle(style)
            elements.append(table)
            elements.append(Spacer(1, 20))
            current_table_data.clear()

    for d in sorted(grouped.keys()):
        week_num = math.ceil(d.day / 7)
        if current_week != week_num:
            flush_table()
            elements.append(Paragraph(f"<b>Week {week_num}</b>", styles['Heading2']))
            current_table_data.append(headers)
            current_week = week_num
            
        row = [str(d)]
        for loc in locations:
            row.append(grouped[d].get(loc.id, "-"))
        current_table_data.append(row)
        
    flush_table()
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=roster.pdf"}
    )

app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Faculty Duty Scheduler Engine Online"}
