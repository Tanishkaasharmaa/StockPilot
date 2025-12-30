import sqlite3
import pandas as pd
import chromadb
import os
from dotenv import load_dotenv

# LangChain / LangGraph Imports
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
import warnings

# Internal Imports (Updated to absolute from src root)
from core.reactive_intelligence import ReactiveIntelligence
from core.event_monitor import EventMonitor
from database.embeddings import OllamaEmbeddingFunction
from utils.simple_store import SimpleVectorStore

# Load .env from config directory
# Up two levels from src/core/agent.py -> src/ -> d:/Hugo/ -> config/
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(base_dir, 'config', '.env')
load_dotenv(env_path)

DB_PATH = os.path.join(base_dir, 'data', 'hugo.db')
CHROMA_PATH = os.path.join(base_dir, 'data', 'chroma_db')

# --- Global Clients ---
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")
    chroma_client = None

# --- Tool Definitions ---

@tool
def calculate_build_capacity(model_name: str) -> str:
    """Calculates how many units of a specific scooter model can be built based on current inventory."""
    try:
        conn = sqlite3.connect(DB_PATH)
        formatted_model = model_name.replace(" ", "_")
        query_parts = f"SELECT part_id, part_name FROM material_master WHERE used_in_models LIKE '%{formatted_model}%'"
        df_parts = pd.read_sql_query(query_parts, conn)
        if df_parts.empty:
            conn.close()
            return f"No parts found for model '{model_name}'."
        part_ids = tuple(df_parts['part_id'].tolist())
        query_stock = f"SELECT part_id, quantity_available FROM stock_levels WHERE part_id = '{part_ids[0]}'" if len(part_ids) == 1 else f"SELECT part_id, quantity_available FROM stock_levels WHERE part_id IN {part_ids}"
        df_stock = pd.read_sql_query(query_stock, conn)
        df_combined = pd.merge(df_parts, df_stock, on='part_id', how='left').fillna(0)
        min_stock = df_combined['quantity_available'].min()
        bottlenecks = df_combined[df_combined['quantity_available'] == min_stock]
        conn.close()
        bottleneck_info = ", ".join([f"{row['part_name']} ({row['part_id']})" for _, row in bottlenecks.iterrows()])
        return f"Build Capacity for {model_name}: {int(min_stock)} units.\nLimiting Factor(s): {bottleneck_info}"
    except Exception as e:
        return f"Error: {e}"

@tool
def check_parts_status(part_identifier: str) -> str:
    """Checks the status of a specific part."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT m.part_id, m.part_name, s.quantity_available, d.min_stock_level FROM material_master m JOIN stock_levels s ON m.part_id = s.part_id LEFT JOIN dispatch_parameters d ON m.part_id = d.part_id WHERE m.part_id = '{part_identifier}' OR m.part_name LIKE '%{part_identifier}%'"
        df = pd.read_sql_query(query, conn)
        if df.empty:
            conn.close()
            return f"Part '{part_identifier}' not found."
        part_id = df.iloc[0]['part_id']
        query_orders = f"SELECT * FROM material_orders WHERE part_id = '{part_id}' AND status != 'delivered'"
        df_orders = pd.read_sql_query(query_orders, conn)
        conn.close()
        row = df.iloc[0]
        status = "OK" if row['quantity_available'] >= row['min_stock_level'] else "BELOW REORDER POINT ⚠️"
        return f"Status for {row['part_name']}: {row['quantity_available']} (Min: {row['min_stock_level']}) - {status}"
    except Exception as e:
        return f"Error: {e}"

@tool
def check_all_stock_status() -> str:
    """Checks the entire inventory for low stock parts."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT m.part_id, m.part_name, s.quantity_available, d.min_stock_level FROM material_master m JOIN stock_levels s ON m.part_id = s.part_id JOIN dispatch_parameters d ON m.part_id = d.part_id WHERE s.quantity_available < d.min_stock_level"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_markdown(index=False) if not df.empty else "All stock levels are fine."
    except Exception as e:
        return f"Error: {e}"

@tool
def compare_suppliers(part_identifier: str) -> str:
    """Compares suppliers for a specific part."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT * FROM suppliers WHERE part_id = (SELECT part_id FROM material_master WHERE part_id = '{part_identifier}' OR part_name LIKE '%{part_identifier}%' LIMIT 1)"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_markdown(index=False) if not df.empty else "No suppliers found."
    except Exception as e:
        return f"Error: {e}"

@tool
def search_documents(search_query: str) -> str:
    """Searches through documents."""
    try:
        import ollama
        db = SimpleVectorStore()
        model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        emb = ollama.embeddings(model=model, prompt=search_query)['embedding']
        results = db.query(emb, n_results=3)
        output = ""
        for i, doc in enumerate(results['documents'][0]):
            output += f"-- {results['metadatas'][0][i]['source']} --\n{doc}\n\n"
        return output if output else "No results."
    except Exception as e:
        return f"Error: {e}"

@tool
def analyze_risks() -> str:
    """Analyzes supply chain risks."""
    try:
        ri = ReactiveIntelligence(DB_PATH)
        risks = [r for r in ri.get_risk_analysis() if r['risk_score'] > 65]
        return pd.DataFrame(risks).to_markdown(index=False) if risks else "No major risks."
    except Exception as e:
        return f"Error: {e}"

@tool
def analyze_demand_surge(model_name: str, increase_percentage: int) -> str:
    """Simulates a demand surge."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT b.part_id, m.part_name, b.quantity_per_unit, s.quantity_available FROM product_bom b JOIN material_master m ON b.part_id = m.part_id LEFT JOIN stock_levels s ON b.part_id = s.part_id WHERE b.model_id = '{model_name}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty: return "Model not found."
        new_demand = 100 * (1 + increase_percentage/100)
        df['shortage'] = (df['quantity_per_unit'] * new_demand) - df['quantity_available']
        bottlenecks = df[df['shortage'] > 0]
        return bottlenecks.to_markdown(index=False) if not bottlenecks.empty else "No shortages expected."
    except Exception as e:
        return f"Error: {e}"

@tool
def fetch_unacknowledged_events() -> str:
    """Fetches unacknowledged events."""
    try:
        monitor = EventMonitor(DB_PATH)
        events = monitor.get_unacknowledged_events()
        return pd.DataFrame(events).to_markdown(index=False) if events else "No alerts."
    except Exception as e:
        return f"Error: {e}"

@tool
def acknowledge_event(event_id: str) -> str:
    """Acknowledges an event."""
    try:
        monitor = EventMonitor(DB_PATH)
        return f"Event {event_id} acknowledged." if monitor.acknowledge_event(event_id) else "Event not found."
    except Exception as e:
        return f"Error: {e}"

class HugoAgent:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.llm = ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.2"), temperature=0)
        self.tools = [calculate_build_capacity, check_parts_status, check_all_stock_status, compare_suppliers, search_documents, fetch_unacknowledged_events, acknowledge_event, analyze_demand_surge]
        self.graph = create_react_agent(self.llm, self.tools)
        self.system_prompt = "You are Hugo, the Strategic Procurement AI."

    def run(self, user_input, history=None):
        try:
            messages = [SystemMessage(content=self.system_prompt)]
            if history: messages.extend(history)
            messages.append(HumanMessage(content=user_input))
            return self.graph.invoke({"messages": messages})['messages'][-1].content
        except Exception as e:
            return f"Error: {e}"
