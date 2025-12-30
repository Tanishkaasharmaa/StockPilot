import sqlite3
import pandas as pd
import os

DB_PATH = 'd:/Hugo/hugo.db'
DATA_DIR = 'd:/Hugo/Data'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Material Master Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS material_master (
        part_id TEXT PRIMARY KEY,
        part_name TEXT,
        part_type TEXT,
        used_in_models TEXT,
        dimensions TEXT,
        weight REAL,
        blocked_parts TEXT,
        successor_parts TEXT,
        comment TEXT
    )
    ''')

    # Stock Levels Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_levels (
        part_id TEXT PRIMARY KEY,
        part_name TEXT,
        location TEXT,
        quantity_available INTEGER,
        FOREIGN KEY (part_id) REFERENCES material_master (part_id)
    )
    ''')
    
    # Material Orders (Inbound)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS material_orders (
        order_id TEXT PRIMARY KEY,
        part_id TEXT,
        quantity_ordered INTEGER,
        order_date TEXT,
        expected_delivery_date TEXT,
        supplier_id TEXT,
        status TEXT,
        actual_delivered_at TEXT,
        FOREIGN KEY (part_id) REFERENCES material_master (part_id)
    )
    ''')

    # Sales Orders (Outbound)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales_orders (
        sales_order_id TEXT PRIMARY KEY,
        model TEXT,
        version TEXT,
        quantity INTEGER,
        order_type TEXT,
        requested_date TEXT,
        created_at TEXT,
        accepted_request_date TEXT
    )
    ''')
    
    # Suppliers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id TEXT,
        part_id TEXT,
        price_per_unit REAL,
        lead_time_days INTEGER,
        min_order_qty INTEGER,
        reliability_rating REAL,
        PRIMARY KEY (supplier_id, part_id),
        FOREIGN KEY (part_id) REFERENCES material_master (part_id)
    )
    ''')

    # Dispatch Parameters
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dispatch_parameters (
        part_id TEXT PRIMARY KEY,
        min_stock_level INTEGER,
        reorder_quantity INTEGER,
        reorder_interval_days INTEGER,
        FOREIGN KEY (part_id) REFERENCES material_master (part_id)
    )
    ''')
    
    # Bill of Materials (BOM)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_bom (
        model_id TEXT,
        part_id TEXT,
        quantity_per_unit INTEGER,
        PRIMARY KEY (model_id, part_id),
        FOREIGN KEY (part_id) REFERENCES material_master (part_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized.")

def load_data():
    conn = get_db_connection()
    
    # Mapping CSV files to table names
    files_tables = {
        'material_master.csv': 'material_master',
        'stock_levels.csv': 'stock_levels',
        'material_orders.csv': 'material_orders',
        'sales_orders.csv': 'sales_orders',
        'suppliers.csv': 'suppliers',
        'dispatch_parameters.csv': 'dispatch_parameters'
    }
    
    for filename, table_name in files_tables.items():
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                # Ensure date columns are strings (Pandas might treat them as objects, which is fine, but good to ensure)
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"Loaded {len(df)} rows into {table_name}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        else:
            print(f"File not found: {filename}")
            
    conn.commit()
    conn.close()
    print("Data loading complete.")

if __name__ == "__main__":
    init_db()
    load_data()
