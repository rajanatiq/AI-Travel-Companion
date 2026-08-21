# Wanderlust AI - Backend (FastAPI + SQL Server)

This is the backend service for Wanderlust AI, built with FastAPI, SQLAlchemy, and Python. It manages user authentication, database operations, and integrates with the Google Gemini API to generate dynamic, intelligent trip itineraries.

## ? Features
- **FastAPI Framework:** High-performance async API.
- **AI Integration:** Uses Gemini 1.5 Flash to generate verified travel spots concurrently.
- **Robust API-Free Fallback System:** Integrates live Wikipedia Search API and dynamic realistic place generation to ensure a 100% success rate globally for trip generation, even if the primary AI API is rate-limited or fails.
- **SQL Server Database:** Microsoft SQL Server with pyodbc for robust relational data storage.
- **JWT Auth:** Secure user registration and login.
- **Trip & Budget Management:** CRUD endpoints for trips, itinerary items, and expenses.

## ??? Prerequisites
- Python 3.9+
- Microsoft SQL Server (e.g., SQLEXPRESS)
- ODBC Driver 18 for SQL Server

## ?? Installation & Setup

1. **Clone or Navigate to the directory:**
   `ash
   cd "C:\Users\mq202\PycharmProjects\AI Travel Companion"
   `

2. **Create and Activate a Virtual Environment:**
   `ash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   `

3. **Install Dependencies:**
   `ash
   pip install -r requirements.txt
   `

4. **Environment Variables:**
   Ensure you have a .env file in the root of the backend directory. You must include your Gemini API key:
   `env
   GEMINI_API_KEY=your_gemini_key_here
   DATABASE_URL=mssql+pyodbc://localhost\SQLEXPRESS/AITravelCompanionDB?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
   SECRET_KEY=your-secret-key
   `

5. **Database Initialization:**
   Run the provided SQL scripts in SQL Server Management Studio to create the tables (users, preferences, trips, itinerary_items, expenses, ratings, etc.) inside the AITravelCompanionDB database.

## ?? How to Run

Start the FastAPI server using the main.py entrypoint:
`ash
python main.py
`

The server will start at http://localhost:8000. 
- Interactive API Docs (Swagger): http://localhost:8000/docs
- ReDoc Docs: http://localhost:8000/redoc

## ?? API Structure
- /api/v1/auth/* - User login/registration/profile.
- /api/v1/trips/* - Manage trips and AI generation.
- /api/v1/expenses/* - Budgeting and expense tracking.
- /api/v1/places/* - City autocomplete and cache.
