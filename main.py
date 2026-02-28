from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import engine, get_db
from agent import DoctorAgent

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hospital Appointment System API")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hospital Appointment System API. Go to /static/index.html to see the UI."}

@app.post("/chat", response_model=schemas.ChatResponse)
def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    agent = DoctorAgent(db)
    result = agent.process_query(request.query)
    return result

@app.get("/doctors", response_model=List[schemas.Doctor])
def get_doctors(
    city: Optional[str] = None,
    specialty: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Doctor)
    if city:
        query = query.filter(models.Doctor.city.ilike(f"%{city}%"))
    if specialty:
        # Match against category or specialization
        query = query.filter(
            (models.Doctor.category.ilike(f"%{specialty}%")) | 
            (models.Doctor.specialization.ilike(f"%{specialty}%"))
        )
    return query.offset(skip).limit(limit).all()

@app.get("/doctors/{doctor_id}", response_model=schemas.Doctor)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.get("/cities", response_model=List[str])
def get_cities(db: Session = Depends(get_db)):
    # Get distinct cities
    cities = db.query(models.Doctor.city).distinct().all()
    # cities is a list of tuples like [('Lahore',), ('Karachi',)]
    return [city[0] for city in cities if city[0]]

@app.get("/specialties", response_model=List[str])
def get_specialties(db: Session = Depends(get_db)):
    # Get distinct categories/specialties
    # We'll use category as the primary filter
    categories = db.query(models.Doctor.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]

@app.post("/appointments")
def create_appointment(appointment: schemas.AppointmentCreate):
    # In a real app, we would save this to a database table
    # For now, just mock the success
    return {
        "message": "Appointment booked successfully",
        "details": appointment
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
