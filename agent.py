import google.generativeai as genai
import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

BASE_URL = "http://localhost:4444"

SYSTEM_PROMPT = """
You are SehatBot, a Pakistani doctor appointment booking assistant.
Personality: Warm, helpful, professional. Use "Ji zaroor!" or "Shukriya!"
occasionally. Always respond in English unless user writes in Urdu.
Your job: Help patients find doctors and book appointments in Pakistan.
Symptom to specialist mapping:

chest pain, heart, cardiac → Cardiologist
skin, rash, acne, hair loss → Dermatologist
child, baby, kids, fever in child → Pediatrician
women, pregnancy, periods, gynec → Gynecologist
brain, headache, seizure, stroke → Neurologist
bones, joints, knee, back pain, spine → Orthopedic Surgeon
depression, anxiety, mental health → Psychiatrist
teeth, dental, tooth pain → Dentist
eye, vision, glasses → Eye Specialist
ear, nose, throat, ENT → ENT Specialist
general, fever, cough, cold → General Physician

WORKFLOW - follow this exact order:

If city not mentioned: ask "Which city are you in?"
If medical concern not mentioned: ask "What is your health concern?"
Call search_doctors to find matching doctors
Show the results and ask "Which doctor would you like to book?"
Call get_slots for the chosen doctor (use the ID number shown)
Ask for patient name and phone number
Confirm details: "Shall I book Dr.X on Date at Time for Rs.X for Name?"
Call book_now with all the info
Share the confirmation code and say to save it

IMPORTANT RULES:

NEVER guess doctor IDs — always use IDs from search_doctors results
NEVER guess slot IDs — always use slot IDs from get_slots results
NEVER book without patient name AND phone number
Always show fees before booking
If patient asks to check or cancel appointment, ask for confirmation code

TOOL USAGE — when you need data, write EXACTLY this format on its own line:
TOOL: search_doctors(city="Lahore", specialization="Cardiologist")
TOOL: get_slots(doctor_id=5)
TOOL: book_now(patient_name="Ali", patient_phone="0300-1234567", doctor_id=5, slot_id=12)
TOOL: get_my_appointment(confirmation_code="PKAB1234")
TOOL: cancel_my_appointment(confirmation_code="PKAB1234")
After writing a TOOL line, STOP and wait for the result.
When you receive TOOL_RESULT, continue the conversation using that data.
"""

# --- Helper Functions ---

def local_fallback(user_message):
    """
    Simple keyword-based fallback when AI is rate limited.
    Detects city and specialization keywords and calls search_doctors.
    """
    user_message = user_message.lower()
    
    # 1. Detect City
    cities = ['lahore', 'karachi', 'islamabad', 'peshawar', 'rawalpindi', 'multan', 'faisalabad', 'quetta', 'sialkot', 'gujranwala']
    found_city = None
    for city in cities:
        if city in user_message:
            found_city = city.title()
            break
            
    # 2. Detect Specialty
    specialties = {
        'heart': 'Cardiologist', 'cardio': 'Cardiologist',
        'skin': 'Dermatologist', 'derma': 'Dermatologist', 'rash': 'Dermatologist',
        'child': 'Pediatrician', 'baby': 'Pediatrician', 'kid': 'Pediatrician',
        'women': 'Gynecologist', 'lady': 'Gynecologist', 'pregnancy': 'Gynecologist',
        'brain': 'Neurologist', 'headache': 'Neurologist',
        'bone': 'Orthopedic Surgeon', 'joint': 'Orthopedic Surgeon',
        'mind': 'Psychiatrist', 'depression': 'Psychiatrist',
        'teeth': 'Dentist', 'dental': 'Dentist',
        'eye': 'Eye Specialist',
        'ear': 'ENT Specialist', 'nose': 'ENT Specialist', 'throat': 'ENT Specialist',
        'general': 'General Physician', 'fever': 'General Physician'
    }
    
    found_spec = None
    for keyword, spec in specialties.items():
        if keyword in user_message:
            found_spec = spec
            break
            
    # 3. Construct Search
    if found_city or found_spec:
        result = search_doctors(city=found_city, specialization=found_spec)
        return f"⚠️ AI is currently busy (Rate Limit), but here are some results based on keywords:\n\n{result}\n\nTo book, please wait a minute and try again."
    
    return "⚠️ AI is currently busy (Rate Limit). Please try again in a minute."

def search_doctors(city=None, specialization=None, search=None):
    params = {}
    if city: params['city'] = city
    if specialization: params['specialization'] = specialization
    if search: params['search'] = search
    
    try:
        response = requests.get(f"{BASE_URL}/doctors", params=params)
        data = response.json()
        doctors = data.get("doctors", [])
        
        if not doctors:
            return "No doctors found matching criteria."
            
        result = f"🏥 Found {len(doctors)} doctors (showing top 5):\n"
        for i, doc in enumerate(doctors[:5], 1):
            result += f"{i}. Dr. {doc['name']} | {doc['specialization']} | {doc['hospital']}, {doc['city']} | Fee: Rs.{doc['fee_pkr']} | ⭐{doc['rating']} (ID: {doc['id']})\n"
        return result
    except Exception as e:
        return f"Error searching doctors: {str(e)}"

def get_slots(doctor_id):
    try:
        response = requests.get(f"{BASE_URL}/doctors/{doctor_id}/slots")
        if response.status_code != 200:
            return "Could not fetch slots. Please check doctor ID."
            
        data = response.json()
        slots = data.get("slots", {})
        
        if not slots:
            return "No available slots found for this doctor."
            
        result = f"📅 Available slots:\n"
        count = 0
        for date, time_list in slots.items():
            times = ", ".join([f"{t['time']}(#{t['id']})" for t in time_list])
            result += f"{date}: {times}\n"
            count += 1
            if count >= 3: break
        return result
    except Exception as e:
        return f"Error getting slots: {str(e)}"

def book_now(patient_name, patient_phone, doctor_id, slot_id, reason="General consultation", patient_email=""):
    payload = {
        "patient_name": patient_name,
        "patient_phone": patient_phone,
        "patient_email": patient_email,
        "doctor_id": int(doctor_id),
        "slot_id": int(slot_id),
        "reason": reason
    }
    
    try:
        response = requests.post(f"{BASE_URL}/book", json=payload)
        data = response.json()
        
        if response.status_code != 200:
            return f"Booking failed: {data.get('detail', 'Unknown error')}"
            
        details = data.get("details", {})
        return f"""✅ APPOINTMENT CONFIRMED!
🔑 Code: {data.get('confirmation_code')}  ← SAVE THIS!
👨‍⚕️ {details.get('doctor_name')} — {details.get('specialization')}
🏥 {details.get('hospital')}
📅 {details.get('slot_date')} at {details.get('slot_time')}
💰 Fee: Rs. {details.get('fee_pkr')}"""
    except Exception as e:
        return f"Error booking appointment: {str(e)}"

def get_my_appointment(confirmation_code):
    try:
        response = requests.get(f"{BASE_URL}/appointment/{confirmation_code}")
        if response.status_code != 200:
            return "Appointment not found."
            
        data = response.json()
        return f"""Appointment Details:
Code: {data.get('confirmation_code')}
Patient: {data.get('patient_name')}
Doctor: {data.get('doctor_name')} ({data.get('specialization')})
Hospital: {data.get('hospital')}
Time: {data.get('slot_date')} at {data.get('slot_time')}
Status: {data.get('status')}"""
    except Exception as e:
        return f"Error fetching appointment: {str(e)}"

def cancel_my_appointment(confirmation_code):
    try:
        response = requests.delete(f"{BASE_URL}/appointment/{confirmation_code}")
        if response.status_code != 200:
            return "Could not cancel appointment. Check code."
            
        return "Success: Appointment cancelled successfully."
    except Exception as e:
        return f"Error cancelling appointment: {str(e)}"

# --- Tool Execution ---

def execute_tool(tool_call_text):
    # Extract function name and args
    # Pattern: TOOL: func_name(arg1="val", arg2=123)
    match = re.search(r"TOOL:\s*(\w+)\((.*)\)", tool_call_text)
    if not match:
        return "Error: Invalid tool format"
    
    func_name = match.group(1)
    args_str = match.group(2)
    
    # Available tools
    tools = {
        "search_doctors": search_doctors,
        "get_slots": get_slots,
        "book_now": book_now,
        "get_my_appointment": get_my_appointment,
        "cancel_my_appointment": cancel_my_appointment
    }
    
    if func_name not in tools:
        return f"Error: Unknown tool {func_name}"
    
    try:
        # Safe evaluation of arguments
        # We wrap the call in a lambda or just eval the whole expression with restricted globals
        # But `eval` with strings like 'city="Lahore"' is tricky because it's not a dict, it's kwargs syntax.
        # So we eval `func(kwargs)` directly.
        
        # Construct the full call string to eval
        # e.g. "search_doctors(city='Lahore')"
        # We need to ensure the function is in the local scope for eval
        local_scope = tools.copy()
        
        # Execute
        result = eval(f"{func_name}({args_str})", {"__builtins__": {}}, local_scope)
        return str(result)
        
    except Exception as e:
        return f"Error executing tool: {str(e)}"

import time

# --- Main Agent Function ---

def run_agent(user_message: str, history: list) -> tuple:
    if not os.getenv("GEMINI_API_KEY"):
         return "⚠️ Please add your GEMINI_API_KEY to the .env file.", history

    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        # Convert history
        gemini_history = []
        for msg in history:
            role = "model" if msg["role"] in ["assistant", "model"] else "user"
            gemini_history.append({"role": role, "parts": [msg["content"]]})
            
        chat = model.start_chat(history=gemini_history)
        
        # Send user message with retry logic for 429
        max_retries = 3
        retry_delay = 5 # seconds
        
        response = None
        for attempt in range(max_retries):
            try:
                response = chat.send_message(user_message)
                break
            except Exception as e:
                if "429" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        # Fallback instead of just error message
                        return local_fallback(user_message), history
                else:
                    raise e
        
        if not response:
             # Fallback to local logic if AI completely fails
             return local_fallback(user_message), history

        response_text = response.text
        
        # Loop to handle tool calls (max 3 turns to prevent infinite loops)
        for _ in range(3):
            if "TOOL:" in response_text:
                # Extract tool call line
                lines = response_text.split('\n')
                tool_lines = [l for l in lines if l.strip().startswith("TOOL:")]
                
                if not tool_lines:
                    break
                    
                tool_call = tool_lines[0].strip()
                
                # Execute tool
                tool_result = execute_tool(tool_call)
                
                # Send result back to model with retry
                for attempt in range(max_retries):
                    try:
                        response = chat.send_message(f"TOOL_RESULT: {tool_result}")
                        break
                    except Exception as e:
                        if "429" in str(e):
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                            else:
                                return "⚠️ I am receiving too many requests right now. Please wait 30 seconds and try again.", history
                        else:
                            raise e
                            
                response_text = response.text
            else:
                break
        
        # Update history
        history.append({"role": "user", "content": user_message})
        history.append({"role": "model", "content": response_text})
        
        return response_text, history
        
    except Exception as e:
        return f"AI Error: {str(e)}", history

if __name__ == "__main__":
    # Test
    print("Testing Agent...")
    res, hist = run_agent("I need a heart doctor in Peshawar", [])
    print("Response:", res)
