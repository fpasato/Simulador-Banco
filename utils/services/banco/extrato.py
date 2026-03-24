import sqlite3
from utils.validators import get_db

def get_transacoes(conta_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            t.*,
            c.numero_conta
        FROM transacoes_conta t
        JOIN contas c ON t.conta_id = c.id
        WHERE t.conta_id = ?
        ORDER BY t.data DESC
    """, (conta_id,))
    return cursor.fetchall()