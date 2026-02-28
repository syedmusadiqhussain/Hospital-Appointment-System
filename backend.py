import sqlite3
import random
import string
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SehatBook API", version="2.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "sehatbook.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic Models
class BookRequest(BaseModel):
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = ""
    doctor_id: int
    slot_id: int
    reason: Optional[str] = "General consultation"

class ChatRequest(BaseModel):
    message: str
    history: List[dict]

# --- ENDPOINTS ---

# ENDPOINT 1
@app.get("/")
def read_root():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    total_doctors = cursor.fetchone()["count"]
    conn.close()
    return {
        "message": "SehatBook API Running",
        "version": "2.0",
        "status": "ok",
        "total_doctors": total_doctors
    }

# ENDPOINT 2
@app.get("/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    total_doctors = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(DISTINCT city) as count FROM doctors")
    total_cities = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(DISTINCT specialization) as count FROM doctors")
    total_specializations = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE status = 'confirmed'")
    total_appointments = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM slots WHERE is_booked = 0")
    total_available_slots = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "total_doctors": total_doctors,
        "total_cities": total_cities,
        "total_specializations": total_specializations,
        "total_appointments": total_appointments,
        "total_available_slots": total_available_slots
    }

# ENDPOINT 3
@app.get("/cities")
def get_cities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city FROM doctors ORDER BY city ASC")
    cities = [row["city"] for row in cursor.fetchall() if row["city"]]
    conn.close()
    return {"cities": cities}

# ENDPOINT 4
@app.get("/specializations")
def get_specializations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization ASC")
    specializations = [row["specialization"] for row in cursor.fetchall() if row["specialization"]]
    conn.close()
    return {"specializations": specializations}

# ENDPOINT 5
@app.get("/doctors")
def get_doctors(
    city: Optional[str] = None,
    specialization: Optional[str] = None,
    search: Optional[str] = None,
    min_fee: Optional[int] = None,
    max_fee: Optional[int] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM doctors WHERE 1=1"
    params = []
    
    if city:
        query += " AND city = ?"
        params.append(city)
    
    if specialization:
        query += " AND specialization = ?"
        params.append(specialization)
        
    if search:
        query += " AND (name LIKE ? OR hospital LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")
        
    if min_fee is not None:
        query += " AND fee_pkr >= ?"
        params.append(min_fee)
        
    if max_fee is not None:
        query += " AND fee_pkr <= ?"
        params.append(max_fee)
        
    cursor.execute(query, params)
    doctors_rows = cursor.fetchall()
    
    doctors = []
    for row in doctors_rows:
        doc = dict(row)
        # Get available slots count
        cursor.execute("SELECT COUNT(*) as count FROM slots WHERE doctor_id = ? AND is_booked = 0", (doc["id"],))
        doc["available_slots_count"] = cursor.fetchone()["count"]
        doctors.append(doc)
        
    conn.close()
    return {"doctors": doctors, "total": len(doctors)}

# ENDPOINT 6
@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    doctor = dict(row)
    
    # Get next 10 available slots
    cursor.execute("""
        SELECT * FROM slots 
        WHERE doctor_id = ? AND is_booked = 0 
        ORDER BY slot_date, slot_time 
        LIMIT 10
    """, (doctor_id,))
    
    slots = [dict(s) for s in cursor.fetchall()]
    
    # Group by date
    grouped_slots = {}
    for slot in slots:
        date = slot["slot_date"]
        if date not in grouped_slots:
            grouped_slots[date] = []
        grouped_slots[date].append(slot)
        
    doctor["slots"] = grouped_slots
    
    conn.close()
    return doctor

# ENDPOINT 7
@app.get("/doctors/{doctor_id}/slots")
def get_doctor_slots(doctor_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all available slots for next 14 days (logic handled by DB setup mostly, here just fetching)
    cursor.execute("""
        SELECT * FROM slots 
        WHERE doctor_id = ? AND is_booked = 0 
        ORDER BY slot_date, slot_time
    """, (doctor_id,))
    
    slots = [dict(s) for s in cursor.fetchall()]
    conn.close()
    
    grouped_slots = {}
    for slot in slots:
        date = slot["slot_date"]
        if date not in grouped_slots:
            grouped_slots[date] = []
        grouped_slots[date].append({"id": slot["id"], "time": slot["slot_time"]})
        
    return {"slots": grouped_slots}

# ENDPOINT 8
@app.post("/book")
def book_appointment(req: BookRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate slot
    cursor.execute("SELECT * FROM slots WHERE id = ? AND doctor_id = ?", (req.slot_id, req.doctor_id))
    slot = cursor.fetchone()
    
    if not slot:
        conn.close()
        raise HTTPException(status_code=404, detail="Slot not found")
        
    if slot["is_booked"] == 1:
        conn.close()
        raise HTTPException(status_code=400, detail="This slot is already taken")
        
    # Generate confirmation code
    code = "PK" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Insert appointment
    try:
        cursor.execute("""
            INSERT INTO appointments (confirmation_code, patient_name, patient_phone, patient_email, doctor_id, slot_id, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, req.patient_name, req.patient_phone, req.patient_email, req.doctor_id, req.slot_id, req.reason))
        
        # Mark slot as booked
        cursor.execute("UPDATE slots SET is_booked = 1 WHERE id = ?", (req.slot_id,))
        
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
        
    # Fetch full details
    cursor.execute("""
        SELECT a.*, d.name as doctor_name, d.specialization, d.hospital, d.fee_pkr, s.slot_date, s.slot_time
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN slots s ON a.slot_id = s.id
        WHERE a.confirmation_code = ?
    """, (code,))
    
    details = dict(cursor.fetchone())
    conn.close()
    
    return {
        "success": True,
        "confirmation_code": code,
        "details": details
    }

# ENDPOINT 9
@app.get("/appointment/{confirmation_code}")
def get_appointment(confirmation_code: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, d.name as doctor_name, d.specialization, d.hospital, d.fee_pkr, s.slot_date, s.slot_time
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN slots s ON a.slot_id = s.id
        WHERE a.confirmation_code = ?
    """, (confirmation_code,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    return dict(row)

# ENDPOINT 10
@app.delete("/appointment/{confirmation_code}")
def cancel_appointment(confirmation_code: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM appointments WHERE confirmation_code = ?", (confirmation_code,))
    appt = cursor.fetchone()
    
    if not appt:
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    slot_id = appt["slot_id"]
    
    # Update appointment status
    cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE confirmation_code = ?", (confirmation_code,))
    
    # Free up the slot
    cursor.execute("UPDATE slots SET is_booked = 0 WHERE id = ?", (slot_id,))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Appointment cancelled successfully"}

from agent import run_agent

# ENDPOINT 11
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        response, updated_history = run_agent(req.message, req.history)
        return {"response": response, "history": updated_history}
    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg or "api_key" in error_msg:
            return {
                "response": "⚠️ Please add your GEMINI_API_KEY to the .env file. Get it free at aistudio.google.com",
                "history": req.history
            }
        return {"response": f"AI error: {error_msg}", "history": req.history}

if __name__ == "__main__":
    import uvicorn
    import os
    PORT = int(os.environ.get("PORT", 4444))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
