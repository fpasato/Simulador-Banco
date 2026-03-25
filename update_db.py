import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS investimentos_temporarios")

cursor.execute("""
    CREATE TABLE investimentos_temporarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conta_id INTEGER NOT NULL,
        investimento_id INTEGER NOT NULL,
        quantidade REAL NOT NULL,
        preco_medio REAL NOT NULL,
        tempo_inicio INTEGER NOT NULL,
        duracao INTEGER NOT NULL,
        FOREIGN KEY (conta_id) REFERENCES contas(id) ON DELETE CASCADE,
        FOREIGN KEY (investimento_id) REFERENCES investimentos(id) ON DELETE CASCADE
    )
""")

conn.commit()
conn.close()