import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(investimentos)")
colunas = cursor.fetchall()
print(colunas)


# Atualiza registros que possam estar NULL (caso existam)
cursor.execute("UPDATE investimentos SET tipo = 'fundo' WHERE tipo IS NULL")
cursor.execute("UPDATE investimentos SET setor = 'geral' WHERE setor IS NULL")


conn.commit()
conn.close()

print("🎯 Limpeza concluída! Apenas 'investimentos' foi preservada.")
 
 
 
 