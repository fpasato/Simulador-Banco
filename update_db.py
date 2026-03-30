import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()


cursor.execute("""delete
);
""")

conn.commit()
conn.close()