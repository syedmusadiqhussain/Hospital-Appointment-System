from pydantic import BaseModel
from typing import Optional, List, Any

class DoctorBase(BaseModel):
    name: str
    specialization: Optional[str] = None
    hospital: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    consultation_fee: Optional[str] = None
    wait_time: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None

class Doctor(DoctorBase):
    id: int

    class Config:
        orm_mode = True

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_name: str
    patient_phone: str
    appointment_time: str
    notes: Optional[str] = None

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    message: str
    data: List[Doctor] = []
