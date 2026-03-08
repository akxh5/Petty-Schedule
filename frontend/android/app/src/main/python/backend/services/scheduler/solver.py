from datetime import timedelta
from typing import List, Dict, Any
from uuid import UUID

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from ... import models

class SchedulingError(Exception):
    pass

def check_feasibility(db: Session, setting_id: UUID) -> dict:
    import math
    setting = db.query(models.DutySetting).filter(models.DutySetting.id == setting_id).first()
    if not setting:
        return {"is_feasible": False, "reasons": [{"error": "Setting not found"}], "warnings": []}

    start_date = setting.start_date
    end_date = setting.end_date
    num_days = (end_date - start_date).days + 1
    
    valid_dates = []
    for d in range(num_days):
        current_date = start_date + timedelta(days=d)
        if not setting.count_sundays and current_date.weekday() == 6:
            continue
        valid_dates.append(current_date)
        
    locations = db.query(models.Location).all()
    professors = db.query(models.Professor).all()
    constraints = db.query(models.Constraint).all()
    
    warnings = []
    reasons = []

    if not locations or not professors:
        return {"is_feasible": False, "reasons": [], "warnings": ["Missing locations or professors"]}

    num_profs = len(professors)
    num_locs = len(locations)
    total_slots = len(valid_dates) * num_locs
    
    if num_profs < num_locs:
        reasons.append({
            "error": "Not enough professors to cover all locations.",
            "details": f"Require at least {num_locs} profs, got {num_profs}"
        })

    min_duties_per_prof = total_slots // num_profs if num_profs > 0 else 0
    
    prof_constraints = {p.id: [] for p in professors}
    for c in constraints:
        if c.professor_id in prof_constraints:
            prof_constraints[c.professor_id].append(c)

    prof_valid_dates = {p.id: valid_dates.copy() for p in professors}
    
    for p in professors:
        pcs = prof_constraints[p.id]
        weekly_limit = 7
        for c in pcs:
            if c.type == models.ConstraintType.MAX_WEEKLY:
                weekly_limit = min(weekly_limit, int(c.value.get("limit", 7)))
                
        unavailable_reasons = []
        for c in pcs:
            if c.type == models.ConstraintType.DAY_UNAVAILABLE:
                day_name = c.value.get("dayOfWeek")
                unavailable_reasons.append(f"DAY_UNAVAILABLE: {day_name}")
                prof_valid_dates[p.id] = [d for d in prof_valid_dates[p.id] if d.strftime("%A") != day_name]

        max_possible_due_to_days = len(prof_valid_dates[p.id])
        num_weeks = math.ceil(num_days / 7)
        max_possible_due_to_weeks = weekly_limit * num_weeks
        
        max_possible = min(max_possible_due_to_days, max_possible_due_to_weeks)
        
        if max_possible < min_duties_per_prof:
            constraint_names = ", ".join(unavailable_reasons)
            if weekly_limit < 7:
                constraint_names += f" (MAX_WEEKLY: {weekly_limit})"
            reasons.append({
                "professor": p.name,
                "required_assignments": min_duties_per_prof,
                "max_possible_assignments": max_possible,
                "constraint": constraint_names if constraint_names else "Multiple Conflicting Constraints"
            })
            
    for current_date in valid_dates:
        available_profs = 0
        for p in professors:
            if current_date in prof_valid_dates[p.id]:
                available_profs += 1
        if available_profs < num_locs:
            reasons.append({
                "error": f"No available professors for {current_date.strftime('%A')}.",
                "details": f"Needs {num_locs}, but only {available_profs} available on {current_date.strftime('%Y-%m-%d')}."
            })
            
    if reasons:
        warnings.append("Configuration may be infeasible.")

    return {
        "is_feasible": len(reasons) == 0,
        "reasons": reasons,
        "warnings": warnings
    }

def generate_schedule(db: Session, setting_id: UUID):
    # Retrieve configuration and relevant state
    setting = db.query(models.DutySetting).filter(models.DutySetting.id == setting_id).first()
    if not setting:
        raise SchedulingError("Duty setting not found")

    start_date = setting.start_date
    end_date = setting.end_date
    num_days = (end_date - start_date).days + 1
    
    valid_days = []
    for d in range(num_days):
        current_date = start_date + timedelta(days=d)
        if not setting.count_sundays and current_date.weekday() == 6:
            continue
        valid_days.append(d)
    
    locations = db.query(models.Location).all()
    professors = db.query(models.Professor).all()
    constraints = db.query(models.Constraint).all()

    if not professors:
        raise SchedulingError("No professors available to schedule.")
    if not locations:
        raise SchedulingError("No locations available to schedule.")

    num_profs = len(professors)
    num_locs = len(locations)
    total_slots = len(valid_days) * num_locs
    
    # Fairness boundaries
    min_duties_per_prof = total_slots // num_profs
    max_duties_per_prof = min_duties_per_prof + 1 if total_slots % num_profs != 0 else min_duties_per_prof
    
    # Organize constraints by professor
    prof_constraints = {p.id: [] for p in professors}
    for c in constraints:
        if c.professor_id in prof_constraints:
            prof_constraints[c.professor_id].append(c)

    # Initialize CP-SAT model
    model = cp_model.CpModel()
    
    # Create duty boolean variables
    # duty[(p, d, l)] = 1 if Professor p works on day d at location l
    duty = {}
    for p_idx, prof in enumerate(professors):
        for d in valid_days:
            for l_idx, loc in enumerate(locations):
                duty[(p_idx, d, l_idx)] = model.NewBoolVar(f"duty_p{p_idx}_d{d}_l{l_idx}")
                
    # Constraints application
    
    # 1. Exact fulfillment (1 prof per slot)
    for d in valid_days:
        for l_idx in range(num_locs):
            model.AddExactlyOne([duty[(p_idx, d, l_idx)] for p_idx in range(num_profs)])
            
    # 2. Same Day Restriction (Prof can only work 1 location per day)
    for p_idx in range(num_profs):
        for d in valid_days:
            model.AddAtMostOne([duty[(p_idx, d, l_idx)] for l_idx in range(num_locs)])

    # 3. Apply explicit Constraints
    objective_terms = []
    
    for p_idx, prof in enumerate(professors):
        pcs = prof_constraints.get(prof.id, [])
        for c in pcs:
            if c.type == models.ConstraintType.DAY_UNAVAILABLE:
                day_name = c.value.get("dayOfWeek") # e.g. "Monday"
                for d in valid_days:
                    current_date = start_date + timedelta(days=d)
                    if current_date.strftime("%A") == day_name:
                        for l_idx in range(num_locs):
                            model.Add(duty[(p_idx, d, l_idx)] == 0)

            elif c.type == models.ConstraintType.LOCATION_RESTRICTED:
                restricted_loc_id = c.value.get("location_id")
                # Find loc idx
                r_l_idx = next((i for i, l in enumerate(locations) if l.id == restricted_loc_id), -1)
                if r_l_idx != -1:
                    # Enforce cannot work at this location
                    for d in valid_days:
                        model.Add(duty[(p_idx, d, r_l_idx)] == 0)
                        
            elif c.type == models.ConstraintType.DAY_PREFERRED:
                day_name = c.value.get("dayOfWeek")
                for d in valid_days:
                    current_date = start_date + timedelta(days=d)
                    if current_date.strftime("%A") == day_name:
                        for l_idx in range(num_locs):
                            # Bonus points for assigning on preferred day
                            objective_terms.append(duty[(p_idx, d, l_idx)] * 10)
                            
            elif c.type == models.ConstraintType.MAX_WEEKLY:
                limit = int(c.value.get("limit", 7))
                # Simple rolling window limit (every 7 days)
                for start_d in range(0, num_days, 7):
                    window = min(7, num_days - start_d)
                    window_days = [d for d in range(start_d, start_d + window) if d in valid_days]
                    if window_days:
                        model.Add(
                            sum(duty[(p_idx, d, l_idx)] for d in window_days for l_idx in range(num_locs)) <= limit
                        )

    # 4. Fairness Target
    for p_idx in range(num_profs):
        total_duties_for_prof = sum(duty[(p_idx, d, l_idx)] for d in valid_days for l_idx in range(num_locs))
        model.Add(total_duties_for_prof >= min_duties_per_prof)
        model.Add(total_duties_for_prof <= max_duties_per_prof)
        
    # 5. Consecutive Days Limit (Optional built-in: avoid 2 days in a row)
    for p_idx in range(num_profs):
        for i in range(len(valid_days) - 1):
            d1 = valid_days[i]
            d2 = valid_days[i+1]
            # Only apply strict consecutive rule if they are truly adjacent days
            if d2 - d1 == 1:
                sum_d1 = sum(duty[(p_idx, d1, l_idx)] for l_idx in range(num_locs))
                sum_d2 = sum(duty[(p_idx, d2, l_idx)] for l_idx in range(num_locs))
                # P can work max 1 out of any 2 consecutive days
                model.Add(sum_d1 + sum_d2 <= 1)
            
    # Maximize preferences
    model.Maximize(sum(objective_terms))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Clear existing schedule for this date range to avoid clashes/re-runs
        db.query(models.RosterAssignment).filter(
            models.RosterAssignment.date >= start_date,
            models.RosterAssignment.date <= end_date
        ).delete()
        
        assignments = []
        for p_idx, prof in enumerate(professors):
            for d in valid_days:
                for l_idx, loc in enumerate(locations):
                    if solver.Value(duty[(p_idx, d, l_idx)]) == 1:
                        assign_date = start_date + timedelta(days=d)
                        assignments.append(models.RosterAssignment(
                            professor_id=prof.id,
                            location_id=loc.id,
                            date=assign_date
                        ))
                        
        db.bulk_save_objects(assignments)
        db.commit()
        return {"status": "success", "message": "Schedule generated optimally", "total_assignments": len(assignments)}
    elif status == cp_model.INFEASIBLE:
        diag = check_feasibility(db, setting_id)
        if not diag["is_feasible"]:
            import json
            raise SchedulingError(json.dumps({
                "error": "schedule_infeasible",
                "reason": "insufficient_available_days",
                "details": diag["reasons"]
            }))
        else:
            raise SchedulingError("No schedule can be found that satisfies all hard constraints and fairness targets.")
    else:
        raise SchedulingError(f"Solver stopped with status: {solver.StatusName(status)}")
