<div align="center">

<img src="screenshots/1_home.png" width="100%" alt="SehatBook"/>

# 🩺 SehatBook — Pakistan Doctor Booking System

[![](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![](https://img.shields.io/badge/Gemini_AI-Free-4285F4?style=flat-square&logo=google)](https://aistudio.google.com)
[![](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Real Pakistani doctors · AI booking · 100% Free**

https://sehatbook.onrender.com · [📖 API Docs](http://localhost:4444/docs) · https://github.com/syedmusadiqhussain/Hospital-Appointment-System

</div>

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center">
      <img src="screenshots/1_home.png" width="100%" alt="Home"/>
      <br/><b>🏠 Home</b>
      <br/><sub>Search doctors by city · Live stats</sub>
    </td>
    <td align="center">
      <img src="screenshots/2_doctors.png" width="100%" alt="Doctors"/>
      <br/><b>👨‍⚕️ Find Doctors</b>
      <br/><sub>245+ real verified Pakistani doctors</sub>
    </td>
    <td align="center">
      <img src="screenshots/3_chat.png" width="100%" alt="AI Chat"/>
      <br/><b>🤖 AI Assistant</b>
      <br/><sub>SehatBot — English & Urdu support</sub>
    </td>
  </tr>
</table>

---

## ✨ What It Does

- 🔍 **Find Doctors** — 245+ real doctors scraped from Marham.pk across 12 Pakistani cities
- 📅 **Book Instantly** — Pick date & time, get a confirmation code in seconds
- 🤖 **AI Chat** — SehatBot powered by Google Gemini helps you find & book the right doctor
- 💬 **Urdu Support** — Chat in English or Urdu
- 📋 **Manage Bookings** — Check or cancel any appointment with your code
- 💰 **100% Free** — No paid APIs, no credit card needed

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/syedmusadiqhussain/Hospital-Appointment-System.git
cd Hospital-Appointment-System

# Install
pip install -r requirements.txt

# Add free Gemini API key (get at aistudio.google.com)
echo GEMINI_API_KEY=your-key-here > .env

# Load doctors into database
python database.py

# Start server
uvicorn backend:app --host 0.0.0.0 --port 8000

# Open browser → http://localhost:8000
```

---

## 🏗️ Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | HTML5 · CSS3 · JavaScript |
| Backend | Python · FastAPI · Uvicorn |
| Database | SQLite |
| AI | Google Gemini 2.0 Flash (Free) |
| Data | Scraped from Marham.pk |

---

## 🌆 Cities Covered

`Lahore` `Karachi` `Islamabad` `Peshawar` `Rawalpindi` `Quetta` `Multan` `Faisalabad` `Hyderabad` `Sialkot` `Gujranwala` `Abbottabad`

---

## 📁 Project Structure

```
Hospital-Appointment-System/
├── backend.py          ← FastAPI server
├── database.py         ← SQLite + CSV loader
├── agent.py            ← Gemini AI agent
├── index.html          ← Frontend website
├── sehatbook.db        ← Auto-generated database
├── requirements.txt
├── .env.example
└── screenshots/
    ├── 1_home.png
    ├── 2_doctors.png
    ├── 3_chat.png
```

---

<div align="center">
Made with ❤️ for Pakistan 🇵🇰 by <a href="https://github.com/syedmusadiqhussain">Syed Musadiq Hussain</a>
<br/><br/>
<b>⭐ Star this repo if it helped you!</b>
</div>
