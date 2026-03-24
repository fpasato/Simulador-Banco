import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Limpa todas as tabelas exceto investimentos
tabelas_para_limpar = [
    "contas", 
    "usuarios",
    "carteira_investimentos", 
    "investimentos_temporarios", 
    "historico_precos",
    "faturas", 
    "transacoes_conta", 
    "cartoes", 
    "transacoes_pix",
    "chaves_pix"
]

for tabela in tabelas_para_limpar:
    try:
        cursor.execute(f"DELETE FROM {tabela}")
        print(f"✅ Tabela {tabela} limpa")
    except sqlite3.OperationalError as e:
        print(f"⚠️  Tabela {tabela} não existe: {e}")

conn.commit()
conn.close()

print("🎯 Limpeza concluída! Apenas 'investimentos' foi preservada.")
