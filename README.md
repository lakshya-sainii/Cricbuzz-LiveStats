# 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

## 📌 Project Overview

**Cricbuzz LiveStats** is an interactive cricket analytics dashboard developed using Python and Streamlit.

The project integrates cricket data from the **Crickbuzz Official APIs via RapidAPI**, stores structured data in **Microsoft SQL Server**, and provides interactive analytics, SQL-based insights, CRUD operations, and an AI-powered cricket assistant.

The application is designed to transform raw cricket data into meaningful and easy-to-understand insights through a modern interactive dashboard.

---

## 🎯 Project Objectives

The main objectives of this project are:

- Fetch cricket data using REST APIs.
- Store and manage structured cricket data using SQL Server.
- Perform cricket analytics using SQL queries.
- Build an interactive dashboard using Streamlit.
- Implement CRUD operations for database management.
- Provide player, team, match, series, and venue insights.
- Create an AI-powered cricket assistant.
- Support both text and voice interaction.
- Handle API errors and request limits efficiently.
- Secure sensitive credentials using environment variables.

---

## ✨ Key Features

### 🏠 Interactive Dashboard
Provides a central overview of cricket information and analytics through a modern Streamlit interface.

### 🔴 Live Match Information
Displays live cricket information using API data while controlling unnecessary API requests through caching.

### 📊 Player Analytics
Provides player-related statistics and performance insights.

### 🌍 World Cricket Map
Visualizes cricket-related geographical information for available teams and players.

### 🧠 AI Cricket Assistant
An intelligent assistant capable of answering:

- General cricket questions
- Cricket rules and terminology
- Database-related questions
- Player performance questions
- SQL-based analytical questions

The assistant uses **Ollama with Llama 3.2:3B locally**, allowing AI responses without a paid AI API.

### 🎙️ Voice Assistant
The AI Assistant supports:

- Microphone input
- Speech-to-text using Faster-Whisper
- Text-based AI responses
- Browser-based text-to-speech output

### 🗄️ SQL Analytics
The application contains **25 analytical SQL queries** for extracting useful cricket insights from the database.

### ✏️ CRUD Operations
The project supports:

- Create
- Read
- Update
- Delete

operations for managing player records.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application and dashboard |
| Microsoft SQL Server | Database management |
| PyODBC | Python to SQL Server connectivity |
| Pandas | Data processing and analysis |
| Plotly | Interactive data visualization |
| Requests | REST API communication |
| RapidAPI | Cricket API access |
| Crickbuzz Official APIs | Cricket data source |
| Ollama | Local AI model execution |
| Llama 3.2:3B | AI language model |
| Faster-Whisper | Speech-to-text |
| SpeechSynthesis | Browser text-to-speech |
| python-dotenv | Environment variable management |

---

## 🗃️ Database Structure

Database Name:

`CricbuzzLiveStats`

The project uses the following main tables:

- `teams`
- `players`
- `venues`
- `series`
- `matches`
- `player_match_stats`

The database stores structured cricket information collected and processed by the application.

---

## 📊 SQL Analytics

The project includes **25 SQL analytical queries**.

These queries provide insights such as:

- Top run scorers
- Top wicket takers
- Best strike rates
- Boundary statistics
- Six-hitting performance
- All-rounder performance
- Team performance
- Match format distribution
- Series information
- Player performance statistics

---

## 🔌 API Integration

Cricket data is retrieved using:

**Crickbuzz Official APIs via RapidAPI**

API credentials are stored securely inside the `.env` file and are not hard-coded into the application.

API request frequency is controlled using caching and appropriate TTL values to reduce unnecessary requests and help handle API rate limits.

---

## 🤖 AI Assistant Architecture

The AI Assistant combines multiple technologies:

**User Question → Intent Detection → SQL / AI Routing → Response**

For database-related questions:

**User → SQL Intent → SQL Server → Result → Assistant**

For general cricket questions:

**User → Ollama → Llama 3.2:3B → Response**

For voice interaction:

**Microphone → Faster-Whisper → Text → Assistant → SpeechSynthesis**

This allows the assistant to answer both general cricket questions and database-specific analytical questions.

---

## 📁 Project Structure

```text
Cricbuzz_LiveStats/
│
├── api/
│   ├── __init__.py
│   └── crickbuzz_client.py
│
├── assets/
│   ├── landing_video.mp4
│   └── analytics_video.mp4
│
├── database/
│   ├── connection.py
│   ├── crud.py
│   ├── data_loader.py
│   └── queries.sql
│
├── utils/
│   └── error_handler.py
│
├── .env
├── .gitignore
├── app.py
├── config.py
├── README.md
├── requirements.txt
├── scorecard_sample.json
└── test_db.py
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root.

Example:

```env
RAPIDAPI_KEY=YOUR_RAPIDAPI_KEY
RAPIDAPI_HOST=crickbuzz-official-apis.p.rapidapi.com
DB_SERVER=YOUR_SQL_SERVER
DB_NAME=CricbuzzLiveStats
DB_DRIVER=ODBC Driver 17 for SQL Server
```

> Never upload the `.env` file or API keys to a public GitHub repository.

---

## 📦 Installation

### 1. Clone or download the project

Open the project folder in VS Code.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🤖 Ollama Setup

Install Ollama separately on the system.

Download the required model:

```bash
ollama pull llama3.2:3b
```

The project uses:

`llama3.2:3b`

for local AI responses.

---

## ▶️ Run the Application

Make sure:

- SQL Server is running.
- The required database is available.
- `.env` is configured.
- Ollama is installed and available.

Then run:

```bash
streamlit run app.py
```

Streamlit will open the application in the browser.

---

## 🧭 Application Modules

The application contains the following main sections:

1. Dashboard
2. Live Matches
3. Player Analytics
4. World Cricket Map
5. AI Assistant
6. SQL Analytics
7. CRUD
8. Landing Page

---

## ⚠️ Error Handling

The application includes error handling for situations such as:

- API request failures
- HTTP errors
- API rate limits
- Missing data
- Database connection errors
- Invalid user inputs
- AI service errors

API caching is used to reduce repeated requests and improve application efficiency.

---

## 🔒 Security

Sensitive credentials are stored using environment variables.

The `.gitignore` file prevents important local/private files from being committed:

```text
.env
venv/
__pycache__/
*.pyc
```

API keys should never be directly included in source code.

---

## 🚀 Future Improvements

Possible future improvements include:

- Additional real-time cricket analytics
- More advanced player comparison
- Match prediction models
- Improved geographic data coverage
- Additional AI analytics
- Cloud database integration
- Public cloud deployment
- More advanced voice assistant features

---

## 🎓 Project Type

**Internship Project – Cricket Data Analytics & Application Development**

This project demonstrates practical implementation of:

**Python + REST API + SQL + Data Analytics + Streamlit + AI + Voice Technology**

---

## 🏁 Conclusion

Cricbuzz LiveStats combines cricket data, SQL analytics, interactive visualization, database management, and artificial intelligence into a single application.

The project demonstrates an end-to-end workflow from cricket data collection and database storage to analytical insights and AI-powered user interaction.