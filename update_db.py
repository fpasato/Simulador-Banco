import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Pega todas as tabelas exceto 'investimentos'
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='investimentos';")
tables = cursor.fetchall()

# Desabilita chaves estrangeiras temporariamente
cursor.execute("PRAGMA foreign_keys = OFF")

# Deleta dados de todas as tabelas exceto investimentos
for table in tables:
    table_name = table[0]
    print(f"Limpando tabela: {table_name}")
    cursor.execute(f"DELETE FROM {table_name}")

# Reabilita chaves estrangeiras
cursor.execute("PRAGMA foreign_keys = ON")

# Reseta autoincrement
cursor.execute("DELETE FROM sqlite_sequence")

conn.commit()
conn.close()
print("Dados limpos! Tabela investimentos foi preservada.")