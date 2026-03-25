import sqlite3
import time
from utils.validators import get_db

def deve_executar_tarefa(nome_tarefa, intervalo_segundos):
    """
    Verifica se a tarefa deve ser executada agora.
    A operação é atômica (evita execução duplicada em múltiplos workers).
    """
    conn = get_db()
    conn.row_factory = sqlite3.Row
    agora = time.time()
    try:
        # Inicia transação com bloqueio (apenas escrita)
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            "SELECT ultima_execucao FROM controle_tasks WHERE nome = ?",
            (nome_tarefa,)
        ).fetchone()

        if row is None:
            # Primeira execução: insere e executa
            conn.execute(
                "INSERT INTO controle_tasks (nome, ultima_execucao, criado_em) VALUES (?, ?, ?)",
                (nome_tarefa, agora, agora)
            )
            conn.commit()
            return True

        ultima = row['ultima_execucao']
        if (agora - ultima) >= intervalo_segundos:
            # Atualiza timestamp e executa
            conn.execute(
                "UPDATE controle_tasks SET ultima_execucao = ? WHERE nome = ?",
                (agora, nome_tarefa)
            )
            conn.commit()
            return True
        else:
            conn.commit()
            return False

    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()