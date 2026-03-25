import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()


cursor.execute("""CREATE TABLE IF NOT EXISTS controle_tasks (
    nome TEXT PRIMARY KEY,
    ultima_execucao REAL NOT NULL,
    criado_em REAL NOT NULL
);
""")

conn.commit()
conn.close()