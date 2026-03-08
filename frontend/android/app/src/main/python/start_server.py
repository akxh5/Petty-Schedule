import uvicorn
import os
import threading
from backend.main import app
import traceback

def verify_ortools():
    try:
        print("Testing OR-Tools import...")
        from ortools.sat.python import cp_model
        print("Import successful. Testing solver...")
        model = cp_model.CpModel()
        var = model.NewBoolVar("test_var")
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        print(f"Solver test successful, status: {status}")
    except Exception as e:
        print("Error verifying OR-Tools:")
        traceback.print_exc()

def start_fastapi():
    print("Starting FastAPI server...")
    verify_ortools()
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    start_fastapi()
