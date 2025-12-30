import sqlite3
import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(base_dir, 'data', 'hugo.db')
# Try both data/Data and data/
DATA_DIR_PRIMARY = os.path.join(base_dir, 'data', 'Data')
DATA_DIR_SECONDARY = os.path.join(base_dir, 'data')

def get_data_path(filename):
    p1 = os.path.join(DATA_DIR_PRIMARY, filename)
    if os.path.exists(p1): return p1
    return os.path.join(DATA_DIR_SECONDARY, filename)

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS material_master (part_id TEXT PRIMARY KEY, part_name TEXT, part_type TEXT, used_in_models TEXT, dimensions TEXT, weight REAL, blocked_parts TEXT, successor_parts TEXT, comment TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS stock_levels (part_id TEXT PRIMARY KEY, part_name TEXT, location TEXT, quantity_available INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS material_orders (order_id TEXT PRIMARY KEY, part_id TEXT, quantity_ordered INTEGER, order_date TEXT, expected_delivery_date TEXT, supplier_id TEXT, status TEXT, actual_delivered_at TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS sales_orders (sales_order_id TEXT PRIMARY KEY, model TEXT, version TEXT, quantity INTEGER, order_type TEXT, requested_date TEXT, created_at TEXT, accepted_request_date TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS suppliers (supplier_id TEXT, part_id TEXT, price_per_unit REAL, lead_time_days INTEGER, min_order_qty INTEGER, reliability_rating REAL, PRIMARY KEY (supplier_id, part_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS dispatch_parameters (part_id TEXT PRIMARY KEY, min_stock_level INTEGER, reorder_quantity INTEGER, reorder_interval_days INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS product_bom (model_id TEXT, part_id TEXT, quantity_per_unit INTEGER, PRIMARY KEY (model_id, part_id))')
    conn.commit()
    conn.close()

def load_data():
    conn = get_db_connection()
    files_tables = {
        'material_master.csv': 'material_master',
        'stock_levels.csv': 'stock_levels',
        'material_orders.csv': 'material_orders',
        'sales_orders.csv': 'sales_orders',
        'suppliers.csv': 'suppliers',
        'dispatch_parameters.csv': 'dispatch_parameters'
    }
    for filename, table_name in files_tables.items():
        file_path = get_data_path(filename)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    load_data()
