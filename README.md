# SehatBook — Pakistan Doctor Booking System

Real Pakistani doctors, AI booking assistant, zero cost.

## What it does
- Shows real scraped doctors from Marham.pk across Pakistan.
- AI chatbot powered by Google Gemini helps book appointments.
- Full booking system with confirmation codes.

## How to get free Gemini API key
Go to [Google AI Studio](https://aistudio.google.com/app/apikey) → sign in → Get API Key → Create → Copy.

## How to run (4 steps)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Add your Gemini API key to `.env` file:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. Setup database:
   ```bash
   python database.py
   ```
4. Start backend server:
   ```bash
   uvicorn backend:app --reload --port 4444
   ```
5. Open `index.html` in your browser.

## Project Files
- `index.html`: The complete frontend with Home, Find Doctors, AI Assistant, and My Booking tabs.
- `backend.py`: FastAPI backend connecting the database and AI agent to the frontend.
- `agent.py`: Google Gemini AI agent logic with tools for searching and booking.
- `database.py`: Script to setup SQLite database and import scraped doctor data.
- `sehatbook.db`: SQLite database file storing doctors, slots, and appointments.
- `requirements.txt`: List of Python dependencies.
- `.env`: Configuration file for API keys.
- `scrape_*.py`: Scripts used to scrape doctor data from the web.
- `*.csv`: Raw data files containing scraped doctor information.
