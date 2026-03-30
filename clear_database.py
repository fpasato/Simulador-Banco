import sqlite3

def clear_all_tables():
    conn = sqlite3.connect("database.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Disable foreign key constraints temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    # Clear each table
    for table in tables:
        table_name = table[0]
        if table_name != 'sqlite_sequence':  # Skip sqlite system table
            print(f"Limpando tabela: {table_name}")
            cursor.execute(f"DELETE FROM {table_name}")
    
    # Re-enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Reset autoincrement counters
    cursor.execute("DELETE FROM sqlite_sequence")
    
    conn.commit()
    conn.close()
    print("Todas as tabelas foram limpas com sucesso!")

if __name__ == "__main__":
    clear_all_tables()
