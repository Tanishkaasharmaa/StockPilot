# Hugo: Strategic Procurement & Operations Intelligence

Hugo is an AI-powered Supply Chain Co-Pilot designed to provide real-time monitoring and strategic insights for operations and procurement.

## 🚀 Features

- **Conversational Intelligence**: Ask complex supply chain questions in plain English.
- **Reactive Intelligence**: Automated alerts for low stock, delayed orders, and production bottlenecks.
- **Event Monitor**: 24/7 background monitoring of operational events.
- **Premium Dashboard**: A modern, interactive UI built with Streamlit.
- **Dynamic RAG**: Knowledge retrieval from technical manuals and dispatch documents using ChromaDB.

## 🛠️ Tech Stack

- **Core**: Python 3.10+
- **LLM Orchestration**: LangGraph, LangChain
- **UI**: Streamlit
- **Database**: SQLite3 (Operational Data), ChromaDB (Vector Search)
- **Local LLMs**: Ollama / Gemini API

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd Hugo
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ollama Setup**:
   Ensure [Ollama](https://ollama.ai/) is installed and running locally. Pull the required model:
   ```bash
   ollama pull llama3 # or the model you are using
   ```

5. **Configure Environment Variables**:
   Create a `config/.env` file (Hugo will also check the project root) for any additional settings:
   ```env
   # No API keys required for local Ollama usage
   # Add other optional variables here...
   ```

## 🚦 Usage

Run the Streamlit application:
```bash
streamlit run src/app.py
```

## 📂 Project Structure

- `src/`: Core logic and application entry point.
- `data/`: Storage for internal databases and operational data.
- `docs/`: Technical documentation and manuals.
- `config/`: Configuration files and environment variables.

---
© 2025 Voltway Ops AI Team
