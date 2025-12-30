import sqlite3
import pandas as pd
import chromadb
from embeddings import OllamaEmbeddingFunction
import os
from dotenv import load_dotenv

# LangChain / LangGraph Imports
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from reactive_intelligence import ReactiveIntelligence
from event_monitor import EventMonitor
import warnings

load_dotenv()

DB_PATH = 'd:/Hugo/hugo.db'
CHROMA_PATH = 'd:/Hugo/chroma_db'

# --- Global Clients ---
# Initialize ChromaDB Client ONCE to prevent locking/crash issues
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")
    chroma_client = None

# --- Tool Definitions ---

@tool
def calculate_build_capacity(model_name: str) -> str:
    """
    Calculates how many units of a specific scooter model can be built based on current inventory.
    Args:
        model_name: The model version to check, e.g., "S1 V1", "S2 V2", "S3 V1". 
                    Try to match exact model names from the conversation.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        curr = conn.cursor()
        
        # 1. Identify parts for this model
        # The 'used_in_models' column contains values like "S1_V1;S2_V1"
        # We need to format the input model name to match this format (e.g. "S1 V1" -> "S1_V1")
        formatted_model = model_name.replace(" ", "_")
        
        query_parts = f"SELECT part_id, part_name FROM material_master WHERE used_in_models LIKE '%{formatted_model}%'"
        df_parts = pd.read_sql_query(query_parts, conn)
        
        if df_parts.empty:
            conn.close()
            return f"No parts found for model '{model_name}'. Please check the model name (e.g., 'S1 V1')."
        
        # 2. Check stock for each part
        part_ids = tuple(df_parts['part_id'].tolist())
        # specific handling for single item tuple
        if len(part_ids) == 1:
            query_stock = f"SELECT part_id, quantity_available FROM stock_levels WHERE part_id = '{part_ids[0]}'"
        else:
            query_stock = f"SELECT part_id, quantity_available FROM stock_levels WHERE part_id IN {part_ids}"
            
        df_stock = pd.read_sql_query(query_stock, conn)
        
        # Merge to get a complete view
        df_combined = pd.merge(df_parts, df_stock, on='part_id', how='left')
        df_combined['quantity_available'] = df_combined['quantity_available'].fillna(0)
        
        # 3. Calculate metrics
        # Assuming 1 unit of each part is needed per scooter (simplified BOM)
        # In a real scenario, we'd have a quantity_per_model table.
        min_stock = df_combined['quantity_available'].min()
        bottlenecks = df_combined[df_combined['quantity_available'] == min_stock]
        
        conn.close()
        
        bottleneck_info = ", ".join([f"{row['part_name']} ({row['part_id']})" for _, row in bottlenecks.iterrows()])
        
        return (f"Build Capacity for {model_name}: {int(min_stock)} units.\n"
                f"Limiting Factor(s) (Bottlenecks): {bottleneck_info}\n"
                f"Total parts required per unit: {len(df_combined)}")

    except Exception as e:
        return f"Error calculating capacity: {e}"

@tool
def check_parts_status(part_identifier: str) -> str:
    """
    Checks the status of a specific part (stock vs reorder point, pending orders).
    Args:
        part_identifier: The Part ID (e.g. "P300") or Part Name (e.g. "Motor").
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Try finding by ID first
        query = f"""
        SELECT m.part_id, m.part_name, s.quantity_available, d.min_stock_level, d.reorder_quantity
        FROM material_master m
        JOIN stock_levels s ON m.part_id = s.part_id
        LEFT JOIN dispatch_parameters d ON m.part_id = d.part_id
        WHERE m.part_id = '{part_identifier}' OR m.part_name LIKE '%{part_identifier}%'
        """
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            conn.close()
            return f"Part '{part_identifier}' not found."
            
        part_id = df.iloc[0]['part_id']
        
        # Check inbound orders for this part
        query_orders = f"SELECT quantity_ordered, expected_delivery_date, status FROM material_orders WHERE part_id = '{part_id}' AND status != 'delivered'"
        df_orders = pd.read_sql_query(query_orders, conn)
        
        conn.close()
        
        # Format output
        row = df.iloc[0]
        status = "OK"
        if row['quantity_available'] < row['min_stock_level']:
            status = "BELOW REORDER POINT ⚠️"
            
        inbound_info = "No pending orders."
        if not df_orders.empty:
            inbound_info = df_orders.to_markdown(index=False)
            
        return (f"Status for {row['part_name']} ({row['part_id']}):\n"
                f"Stock: {row['quantity_available']}\n"
                f"Min Level: {row['min_stock_level']}\n"
                f"Condition: {status}\n\n"
                f"Inbound Orders:\n{inbound_info}")
        
    except Exception as e:
        return f"Error checking part status: {e}"

@tool
def check_all_stock_status() -> str:
    """
    Checks the entire inventory and returns a list of ALL parts that are below their minimum stock level.
    Use this when the user asks broad questions like "Which parts are low?" or "Inventory health check".
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
        SELECT m.part_id, m.part_name, s.quantity_available, d.min_stock_level
        FROM material_master m
        JOIN stock_levels s ON m.part_id = s.part_id
        LEFT JOIN dispatch_parameters d ON m.part_id = d.part_id
        WHERE s.quantity_available < d.min_stock_level
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return "Good news! All parts are above minimum stock levels."
            
        return f"CRITICAL STOCK ALERT - The following parts are below minimum levels:\n\n" + df.to_markdown(index=False)
    except Exception as e:
        return f"Error checking all stock: {e}"

@tool
def compare_suppliers(part_identifier: str) -> str:
    """
    Compares suppliers for a specific part based on price, reliability, and lead time.
    Args:
        part_identifier: The Part ID or the simplest keyword for the part name (e.g. use "Controller" instead of "Controller units").
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Resolve Part ID
        if not part_identifier.startswith("P"):
            # Simple lookup
            res = pd.read_sql_query(f"SELECT part_id FROM material_master WHERE part_name LIKE '%{part_identifier}%' LIMIT 1", conn)
            if res.empty:
                return f"Part '{part_identifier}' not found."
            part_id = res.iloc[0]['part_id']
        else:
            part_id = part_identifier

        query = f"""
        SELECT supplier_id, price_per_unit, lead_time_days, reliability_rating
        FROM suppliers
        WHERE part_id = '{part_id}'
        ORDER BY price_per_unit ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return f"No suppliers found for part {part_id}."
            
        return f"Supplier Comparison for {part_id}:\n" + df.to_markdown(index=False)
        
    except Exception as e:
        return f"Error comparing suppliers: {e}"

@tool
def search_documents(search_query: str) -> str:
    """
    Searches through unstructured documents like Emails and PDF Specifications.
    Use this when asking about delivery delays, supplier communications, or technical details.
    """
    try:
        print(f"Searching docs: {search_query}")
        
        # 1. Generate Embedding
        import ollama
        from simple_store import SimpleVectorStore

        # Initialize Simple Store (Loads from JSON)
        db = SimpleVectorStore()
        
        try:
            # Use the same model as in embeddings.py
            model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
            emb_response = ollama.embeddings(
                model=model,
                prompt=search_query
            )
            query_embedding = emb_response['embedding']
        except Exception as e:
            return f"Error generating embedding: {e}"

        # 2. Query Simple Store
        results = db.query(query_embedding, n_results=3)
        
        output = ""
        if not results['documents'][0]:
            return "No relevant documents found."
            
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            output += f"-- Source: {meta['source']} ({meta['type']}) --\n{doc}\n\n"
        return output
    except Exception as e:
        return f"Search Error: {e}"

@tool
def analyze_risks() -> str:
    """
    Performs a comprehensive supply chain risk analysis for all parts.
    Returns a list of high-risk parts with their risk scores and contributing factors.
    Use this for "What are our biggest risks?" or "Analyze our supply chain health".
    """
    try:
        ri = ReactiveIntelligence(DB_PATH)
        risks = ri.get_risk_analysis()
        
        # Only show the most critical risks to avoid overwhelming the agent
        high_risks = [r for r in risks if r['risk_score'] > 65]
        
        if not high_risks:
            return "Good news! No critical supply chain risks identified."
            
        data = []
        for r in high_risks:
            data.append({
                'Part': f"{r['part_name']} ({r['part_id']})",
                'Score': r['risk_score'],
                'Level': r['risk_level'],
                'Primary Drivers': ", ".join([k.title() for k, v in r['factors'].items() if v > 15])
            })
            
        df = pd.DataFrame(data)
        return "⚠️ CRITICAL SUPPLY CHAIN RISKS\n\n" + df.to_markdown(index=False)
    except Exception as e:
        return f"Risk Analysis Error: {e}"

@tool
def analyze_demand_surge(model_name: str, increase_percentage: int) -> str:
    """
    Simulates a demand surge for a specific scooter model to identify bottlenecks.
    Args:
        model_name: The model to simulate (e.g., "S1 V1", "S2 V2").
        increase_percentage: The percentage increase in demand (e.g., 20, 50, 100).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # 1. Calculate new demand
        # First get current planned production (simplified: assume 100 units/mo base if no data)
        base_demand = 100 
        new_demand = int(base_demand * (1 + increase_percentage/100))
        
        # 2. Get BOM and Stock
        query = f"""
        SELECT b.part_id, m.part_name, b.quantity_per_unit, s.quantity_available, m.lead_time_days
        FROM product_bom b
        JOIN material_master m ON b.part_id = m.part_id
        LEFT JOIN stock_levels s ON b.part_id = s.part_id
        WHERE b.model_id = '{model_name}'
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            conn = sqlite3.connect(DB_PATH) # Reconnect if needed (was closed above)
            valid = pd.read_sql_query("SELECT DISTINCT model_id FROM product_bom", conn)['model_id'].tolist()
            conn.close()
            return f"Model '{model_name}' not found. Available models: {', '.join(valid)}. Please ask user to clarify."
            
        # 3. Calculate Requirements vs Stock
        df['req_per_scooter'] = df['quantity_per_unit']
        df['total_needed'] = df['req_per_scooter'] * new_demand
        df['shortage'] = df['total_needed'] - df['quantity_available']
        df['status'] = df['shortage'].apply(lambda x: 'OK' if x <= 0 else 'SHORTAGE')
        
        # 4. Filter for bottlenecks
        bottlenecks = df[df['status'] == 'SHORTAGE'].copy()
        
        output = f"📊 DEMAND SIMULATION: {increase_percentage}% increase for {model_name}\n"
        output += f"New Production Target: {new_demand} units\n\n"
        
        if bottlenecks.empty:
            output += "✅ No bottlenecks found! Inventory can support this surge."
        else:
            output += f"⚠️ FOUND {len(bottlenecks)} BOTTLENECKS:\n"
            bottlenecks = bottlenecks.sort_values('shortage', ascending=False)
            output += bottlenecks[['part_name', 'total_needed', 'quantity_available', 'shortage']].to_markdown(index=False)
            
        return output

    except Exception as e:
        return f"Simulation Error: {e}"

@tool
def fetch_unacknowledged_events() -> str:
    """
    Fetches a list of all supply chain alerts that haven't been dealt with yet.
    Returns event IDs, timestamps, type, and details.
    Always call this if you are told there are 'unacknowledged alerts'.
    """
    try:
        monitor = EventMonitor(DB_PATH)
        events = monitor.get_unacknowledged_events()
        if not events:
            return "No unacknowledged events found."
        
        df = pd.DataFrame(events)
        # Only show important columns for the LLM
        return "⚠️ UNACKNOWLEDGED EVENTS:\n\n" + df[['event_id', 'type', 'severity', 'details']].to_markdown(index=False)
    except Exception as e:
        return f"Error fetching events: {e}"

@tool
def acknowledge_event(event_id: str) -> str:
    """
    Marks a specific event as acknowledged/resolved. 
    Call this ONLY after you have analyzed the issue and drafted a solution or email.
    Args:
        event_id: The unique ID of the event (e.g. 'EVT-123456...').
    """
    try:
        monitor = EventMonitor(DB_PATH)
        if monitor.acknowledge_event(event_id):
            return f"Event {event_id} has been successfully acknowledged and cleared from the monitor."
        else:
            return f"Error: Could not find event with ID {event_id}."
    except Exception as e:
        return f"Error acknowledging event: {e}"


# --- Agent Class ---

class HugoAgent:
    def __init__(self):
        # Database connection for the Sidebar stats (direct access)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        
        # Initialize LLM
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.llm = ChatOllama(
            model=model_name,
            temperature=0
        )
        
        # Create the Graph (ReAct Agent) with STRATEGIC TOOLS
        self.tools = [
            calculate_build_capacity, 
            check_parts_status, 
            check_all_stock_status, 
            compare_suppliers, 
            search_documents, 
            fetch_unacknowledged_events,
            acknowledge_event,
            analyze_demand_surge
        ]
        
        system_prompt = '''You are Hugo, the Strategic Procurement AI for Voltway.
        
        Your Mission:
        - Analyze operations with precision.
        - Proactively identify bottlenecks and risks.
        - Provide actionable recommendations.
        
        CRITICAL RULES:
        1. ALWAYS USE TOOLS: You MUST call the appropriate tool for every query. NEVER guess or estimate.
        2. USE TOOL RESULTS EXACTLY: Copy the numbers and data from tool outputs VERBATIM. Do NOT modify, round, or estimate.
        3. NO HALLUCINATION: If a tool returns a risk score of 82.5, you MUST say 82.5, not 82 or 83.
        4. BUILD CAPACITY RESTRICTION: You can ONLY calculate build capacity for scooter MODELS. Never for parts.
        5. SEARCH RELEVANCE: Only use information from search_documents that matches the SPECIFIC Part ID mentioned.
        6. SHOW YOUR WORK: Quote specific numbers.
        7. REACTIVE INTELLIGENCE: Proactively search documents for high risks.
        8. NATURAL LANGUAGE: Don't mention tool names.
        9. DECISIVE ACTION: Execute tools immediately if confirmed.
        10. ACKNOWLEDGMENT: Ask to acknowledge events after handling them.
        11. DEMAND SIMULATION: Use analyze_demand_surge for "What if" scenarios.
        12. NO LABOR ESTIMATES: Do NOT assume workdays, hours, or shifts. Capacity is based ONLY on PARTS inventory.
        13. SUPPLIER COMPARISON: If asked for "best supplier", use `compare_suppliers`. Do NOT use `search_documents` for this.
        14. TOOL ARGUMENTS: Do NOT invent arguments. `search_documents` ONLY takes `search_query`.
        '''
        
        self.graph = create_react_agent(self.llm, self.tools)
        self.system_prompt = system_prompt

    def query_database(self, sql):
        # Fallback for sidebar
        try:
            return pd.read_sql_query(sql, self.conn).to_markdown(index=False)
        except:
            return "DB Error"

    def run(self, user_input, history=None):
        """Sends a message to the agent and gets a response, maintaining history."""
        try:
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add history if provided
            if history:
                messages.extend(history)
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            inputs = {"messages": messages}
            
            # Run the graph
            result = self.graph.invoke(inputs)
            
            # The result is the final state. "messages" contains the full history.
            # The last message should be the AI's final answer.
            last_message = result['messages'][-1]
            return last_message.content
            
        except Exception as e:
            return f"Error: {e}"
            
if __name__ == "__main__":
    agent = HugoAgent()
    print(agent.run("How many S1 V1 Motors are in stock?"))
