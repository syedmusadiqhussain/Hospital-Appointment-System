import sqlite3
import random
import string
import os
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

app = FastAPI(title="SehatBook API", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "sehatbook.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Models
class BookingRequest(BaseModel):
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = ""
    doctor_id: int
    slot_id: int
    reason: Optional[str] = "General consultation"

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM doctors").fetchone()['c']
    conn.close()
    return {
        "message": "SehatBook API Running",
        "version": "2.0",
        "status": "ok",
        "total_doctors": count
    }

@app.get("/stats")
def get_stats():
    conn = get_db_connection()
    total_doctors = conn.execute("SELECT COUNT(*) as c FROM doctors").fetchone()['c']
    total_cities = conn.execute("SELECT COUNT(DISTINCT city) as c FROM doctors").fetchone()['c']
    total_specializations = conn.execute("SELECT COUNT(DISTINCT specialization) as c FROM doctors").fetchone()['c']
    total_appointments = conn.execute("SELECT COUNT(*) as c FROM appointments WHERE status='confirmed'").fetchone()['c']
    total_available_slots = conn.execute("SELECT COUNT(*) as c FROM slots WHERE is_booked=0").fetchone()['c']
    conn.close()
    
    return {
        "total_doctors": total_doctors,
        "total_cities": total_cities,
        "total_specializations": total_specializations,
        "total_appointments": total_appointments,
        "total_available_slots": total_available_slots
    }

@app.get("/cities")
def get_cities():
    conn = get_db_connection()
    rows = conn.execute("SELECT DISTINCT city FROM doctors ORDER BY city").fetchall()
    conn.close()
    return {"cities": [row['city'] for row in rows]}

@app.get("/specializations")
def get_specializations():
    conn = get_db_connection()
    rows = conn.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization").fetchall()
    conn.close()
    return {"specializations": [row['specialization'] for row in rows]}

@app.get("/doctors")
def search_doctors(
    city: Optional[str] = None,
    specialization: Optional[str] = None,
    search: Optional[str] = None,
    min_fee: Optional[int] = None,
    max_fee: Optional[int] = None
):
    conn = get_db_connection()
    query = "SELECT * FROM doctors WHERE 1=1"
    params = []
    
    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")
    if specialization:
        query += " AND specialization LIKE ?"
        params.append(f"%{specialization}%")
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
        
    doctors = conn.execute(query, params).fetchall()
    
    results = []
    for doc in doctors:
        d = dict(doc)
        # Get available slots count
        slots_count = conn.execute("SELECT COUNT(*) as c FROM slots WHERE doctor_id=? AND is_booked=0", (d['id'],)).fetchone()['c']
        d['available_slots_count'] = slots_count
        results.append(d)
        
    conn.close()
    return {"doctors": results, "total": len(results)}

@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    conn = get_db_connection()
    doctor = conn.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    
    if not doctor:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    # Next 10 available slots
    slots = conn.execute("""
        SELECT * FROM slots 
        WHERE doctor_id=? AND is_booked=0 AND slot_date >= date('now')
        ORDER BY slot_date, slot_time 
        LIMIT 10
    """, (doctor_id,)).fetchall()
    
    # Group by date
    grouped_slots = {}
    for slot in slots:
        date = slot['slot_date']
        if date not in grouped_slots:
            grouped_slots[date] = []
        grouped_slots[date].append({"id": slot['id'], "time": slot['slot_time']})
        
    result = dict(doctor)
    result['next_slots'] = grouped_slots
    
    conn.close()
    return result

@app.get("/doctors/{doctor_id}/slots")
def get_doctor_slots(doctor_id: int):
    conn = get_db_connection()
    # Next 14 days
    slots = conn.execute("""
        SELECT * FROM slots 
        WHERE doctor_id=? AND is_booked=0 AND slot_date >= date('now')
        ORDER BY slot_date, slot_time
    """, (doctor_id,)).fetchall()
    
    grouped_slots = {}
    for slot in slots:
        date = slot['slot_date']
        if date not in grouped_slots:
            grouped_slots[date] = []
        grouped_slots[date].append({"id": slot['id'], "time": slot['slot_time']})
        
    conn.close()
    return {"slots": grouped_slots}

@app.post("/book")
def book_appointment(req: BookingRequest):
    conn = get_db_connection()
    
    # Check slot
    slot = conn.execute("SELECT * FROM slots WHERE id=?", (req.slot_id,)).fetchone()
    if not slot:
        conn.close()
        raise HTTPException(status_code=404, detail="Slot not found")
        
    if slot['is_booked']:
        conn.close()
        raise HTTPException(status_code=400, detail="This slot is already taken")
        
    if slot['doctor_id'] != req.doctor_id:
        conn.close()
        raise HTTPException(status_code=400, detail="Slot does not belong to this doctor")

    # Generate Code
    code = "PK" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Insert
    try:
        cursor = conn.execute("""
            INSERT INTO appointments (confirmation_code, patient_name, patient_phone, patient_email, doctor_id, slot_id, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, req.patient_name, req.patient_phone, req.patient_email, req.doctor_id, req.slot_id, req.reason))
        
        # Update slot
        conn.execute("UPDATE slots SET is_booked=1 WHERE id=?", (req.slot_id,))
        conn.commit()
        
        # Get details for response
        doctor = conn.execute("SELECT * FROM doctors WHERE id=?", (req.doctor_id,)).fetchone()
        
        response_data = {
            "success": True,
            "confirmation_code": code,
            "doctor_name": doctor['name'],
            "specialization": doctor['specialization'],
            "hospital": doctor['hospital'],
            "fee": doctor['fee_pkr'],
            "slot_date": slot['slot_date'],
            "slot_time": slot['slot_time']
        }
        
        conn.close()
        return response_data
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/appointment/{confirmation_code}")
def get_appointment(confirmation_code: str):
    conn = get_db_connection()
    
    query = """
        SELECT a.*, d.name as doctor_name, d.specialization, d.hospital, d.fee_pkr, s.slot_date, s.slot_time
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN slots s ON a.slot_id = s.id
        WHERE a.confirmation_code = ?
    """
    
    appt = conn.execute(query, (confirmation_code,)).fetchone()
    conn.close()
    
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    return dict(appt)

@app.delete("/appointment/{confirmation_code}")
def cancel_appointment(confirmation_code: str):
    conn = get_db_connection()
    
    appt = conn.execute("SELECT * FROM appointments WHERE confirmation_code=?", (confirmation_code,)).fetchone()
    
    if not appt:
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Cancel
    conn.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appt['id'],))
    # Free slot
    conn.execute("UPDATE slots SET is_booked=0 WHERE id=?", (appt['slot_id'],))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Appointment cancelled successfully"}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    # Placeholder for now
    try:
        from agent import run_agent
        response_text, updated_history = run_agent(req.message, req.history)
        return {"response": response_text, "history": updated_history}
    except ImportError:
        return {"response": "AI chat coming soon (Agent not implemented yet)", "history": req.history}
    except Exception as e:
         return {"response": f"Error: {str(e)}", "history": req.history}

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("PORT", 4444))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
