import sqlite3
from utils.validators import get_db

import pytz
from datetime import datetime, timezone

def get_transacoes(conta_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, c.numero_conta
        FROM transacoes_conta t
        JOIN contas c ON t.conta_id = c.id
        WHERE t.conta_id = ?
        ORDER BY t.data DESC
    """, (conta_id,))
    transacoes = cursor.fetchall()
    conn.close()

    brasil_tz = pytz.timezone('America/Sao_Paulo')
    transacoes_dict = []
    for trans in transacoes:
        trans_dict = dict(trans)
        # Converte a string ISO armazenada (UTC) para datetime com timezone
        dt_utc = datetime.fromisoformat(trans_dict['data'])
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone(brasil_tz)
        trans_dict['data_local'] = dt_local.strftime('%Y/%m/%d %H:%M:%S')
        transacoes_dict.append(trans_dict)
    return transacoes_dict