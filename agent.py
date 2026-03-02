import google.generativeai as genai
import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or "paste-your" in api_key:
    print("Warning: GEMINI_API_KEY not found or invalid in .env")
    # We will not exit here to allow importing, but run_agent will fail
else:
    genai.configure(api_key=api_key)

BASE_URL = "http://localhost:4444"
MODEL_NAME = "gemini-flash-latest"

# --- TOOL FUNCTIONS ---

def search_doctors(city=None, specialization=None, search=None):
    params = {}
    if city: params['city'] = city
    if specialization: params['specialization'] = specialization
    if search: params['search'] = search
    
    try:
        response = requests.get(f"{BASE_URL}/doctors", params=params)
        if response.status_code == 200:
            data = response.json()
            doctors = data.get("doctors", [])
            if not doctors:
                return "No doctors found matching your criteria."
            
            result = f"Found {len(doctors)} doctors (showing top 5):\n"
            for i, doc in enumerate(doctors[:5], 1):
                result += f"{i}. Dr. {doc['name']} — {doc['specialization']} — {doc['hospital']} — {doc['city']} — Fee: Rs.{doc['fee_pkr']} — Rating: {doc['rating']}\n"
            return result
        else:
            return f"Error searching doctors: {response.text}"
    except Exception as e:
        return f"Error connecting to backend: {e}"

def get_available_slots(doctor_id):
    try:
        response = requests.get(f"{BASE_URL}/doctors/{doctor_id}/slots")
        if response.status_code == 200:
            data = response.json()
            slots = data.get("slots", {})
            if not slots:
                return "No available slots found for this doctor."
            
            result = f"Available slots for Doctor ID {doctor_id}:\n"
            count = 0
            for date, time_list in slots.items():
                if count >= 3: break
                times = ", ".join([t['time'] for t in time_list])
                result += f"{date}: {times}\n"
                count += 1
            return result
        else:
            return f"Error getting slots: {response.text}"
    except Exception as e:
        return f"Error connecting to backend: {e}"

def book_appointment(patient_name, patient_phone, doctor_id, slot_id, reason="General consultation", patient_email=""):
    payload = {
        "patient_name": patient_name,
        "patient_phone": patient_phone,
        "doctor_id": int(doctor_id),
        "slot_id": int(slot_id),
        "reason": reason,
        "patient_email": patient_email
    }
    
    try:
        response = requests.post(f"{BASE_URL}/book", json=payload)
        if response.status_code == 200:
            data = response.json()
            return f"""APPOINTMENT CONFIRMED!
Confirmation Code: {data['confirmation_code']}
Doctor: Dr. {data['doctor_name']}
Hospital: {data['hospital']}
Date: {data['slot_date']} at {data['slot_time']}
Fee: Rs. {data['fee']}
SAVE YOUR CODE: {data['confirmation_code']}"""
        else:
            return f"Error booking appointment: {response.text}"
    except Exception as e:
        return f"Error connecting to backend: {e}"

def get_appointment_info(confirmation_code):
    try:
        response = requests.get(f"{BASE_URL}/appointment/{confirmation_code}")
        if response.status_code == 200:
            data = response.json()
            return f"""Appointment Details:
Status: {data['status']}
Patient: {data['patient_name']}
Doctor: Dr. {data['doctor_name']} ({data['specialization']})
Hospital: {data['hospital']}
Date: {data['slot_date']} at {data['slot_time']}
Reason: {data['reason']}"""
        else:
            return "Appointment not found or invalid code."
    except Exception as e:
        return f"Error connecting to backend: {e}"

def cancel_appointment(confirmation_code):
    try:
        response = requests.delete(f"{BASE_URL}/appointment/{confirmation_code}")
        if response.status_code == 200:
            return "Appointment cancelled successfully."
        else:
            return f"Error cancelling appointment: {response.text}"
    except Exception as e:
        return f"Error connecting to backend: {e}"

# --- MAIN AGENT ---

SYSTEM_PROMPT = """
You are SehatBot, a helpful Pakistani doctor appointment booking assistant 
for the SehatBook platform.

You help patients find doctors and book appointments across Pakistan.

Your conversation style:
- Warm and friendly, occasionally say "Ji zaroor!" or "Bilkul!" 
- Always ask for city first if not given
- If patient describes symptoms, suggest the right specialist:
  chest pain or heart = Cardiologist
  skin or rash or acne = Dermatologist  
  child or baby or kids = Pediatrician
  women or pregnancy or periods = Gynecologist
  brain or headache or seizure = Neurologist
  bones or joints or knee = Orthopedic Surgeon
  depression or anxiety or mental = Psychiatrist
  teeth or dental = Dentist
  eye or vision = Eye Specialist
  ear or nose or throat = ENT Specialist
  anything else = General Physician

Your booking workflow:
1. Ask for city if not provided
2. Ask about medical concern
3. Call search_doctors to find matching doctors
4. Show maximum 3 doctors with their fees
5. Ask which doctor they want
6. Call get_available_slots to show times
7. Ask for patient name and phone number
8. Confirm all details before booking
9. Call book_appointment to complete booking
10. Share the confirmation code clearly and say to save it

For appointment lookup or cancellation, ask for confirmation code then 
call the right function.

Always mention fees in Pakistani Rupees before booking.
Never book without getting patient name and phone number first.

When you need to call a function, use exactly this format:
TOOL_CALL: function_name(param1="value", param2="value")

Examples:
TOOL_CALL: search_doctors(city="Lahore", specialization="Cardiologist")
TOOL_CALL: get_available_slots(doctor_id=5)
TOOL_CALL: book_appointment(patient_name="Ali", patient_phone="03001234567", doctor_id=5, slot_id=10)
TOOL_CALL: get_appointment_info(confirmation_code="PK123456")
"""

def run_agent(user_message, history):
    if not api_key or "paste-your" in api_key:
        return "Error: Gemini API Key is missing. Please add it to .env file.", history

    try:
        model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_PROMPT)
        
        # Convert history
        chat_history = []
        for msg in history:
            role = "user" if msg['role'] == "user" else "model"
            chat_history.append({"role": role, "parts": [msg['content']]})
            
        chat = model.start_chat(history=chat_history)
        
        # Send message
        try:
            response = chat.send_message(user_message)
        except Exception as e:
            if "429" in str(e):
                return "I am currently receiving too many requests. Please try again in a few seconds.", history
            raise e

        response_text = response.text
        
        # Check for tool call
        if "TOOL_CALL:" in response_text:
            # Extract tool call
            match = re.search(r'TOOL_CALL: (\w+)\((.*)\)', response_text)
            if match:
                func_name = match.group(1)
                args_str = match.group(2)
                
                # Parse args loosely
                kwargs = {}
                # Regex to find key="value" or key=number
                arg_matches = re.finditer(r'(\w+)=["\']?([^"\',]+)["\']?', args_str)
                for arg in arg_matches:
                    key = arg.group(1)
                    val = arg.group(2)
                    kwargs[key] = val
                
                tool_result = ""
                if func_name == "search_doctors":
                    tool_result = search_doctors(**kwargs)
                elif func_name == "get_available_slots":
                    if 'doctor_id' in kwargs:
                        tool_result = get_available_slots(kwargs['doctor_id'])
                elif func_name == "book_appointment":
                    tool_result = book_appointment(**kwargs)
                elif func_name == "get_appointment_info":
                    if 'confirmation_code' in kwargs:
                        tool_result = get_appointment_info(kwargs['confirmation_code'])
                elif func_name == "cancel_appointment":
                    if 'confirmation_code' in kwargs:
                        tool_result = cancel_appointment(kwargs['confirmation_code'])
                
                # Send result back to model
                final_response = chat.send_message(f"Tool Result: {tool_result}")
                response_text = final_response.text
        
        # Update history
        history.append({"role": "user", "content": user_message})
        history.append({"role": "model", "content": response_text})
        
        return response_text, history

    except Exception as e:
        return f"AI Error: {str(e)}", history

if __name__ == "__main__":
    # Test
    print("Running Agent Test...")
    test_message = "I need a heart doctor in Peshawar"
    resp, hist = run_agent(test_message, [])
    print("TEST RESPONSE:", resp)
    if "doctor" in resp.lower() or "cardiologist" in resp.lower() or "error" in resp.lower():
        print("Test finished (check output above)")
