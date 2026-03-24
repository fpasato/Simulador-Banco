from utils.validators import get_db


def confirmarTransferencia(conta_origem_id, conta_destino_id, valor):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verifica saldo da conta de origem
    cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_origem_id,))
    saldo_origem = cursor.fetchone()[0]
    
    if saldo_origem < valor:
        conn.close()
        return {
            "success": False,
            "message": "Saldo insuficiente"
        }
    
    try:
        with conn:
            # Saída da conta de origem
            cursor.execute("""
                UPDATE contas 
                SET saldo = saldo - ?
                WHERE id = ?
            """, (valor, conta_origem_id))
            
            # Registra transação de saída
            cursor.execute("""
                INSERT INTO transacoes_conta (conta_id, tipo, valor, descricao)
                VALUES (?, 'saida', ?, 'Transferência enviada')
            """, (conta_origem_id, valor))
            
            # Entrada na conta de destino
            cursor.execute("""
                UPDATE contas 
                SET saldo = saldo + ?
                WHERE id = ?
            """, (valor, conta_destino_id))
            
            # Registra transação de entrada
            cursor.execute("""
                INSERT INTO transacoes_conta (conta_id, tipo, valor, descricao)
                VALUES (?, 'entrada', ?, 'Transferência recebida')
            """, (conta_destino_id, valor))
        
        return {
            "success": True,
            "message": "Transferência realizada com sucesso"
        }
        
    except Exception as e:
        print("ERRO REAL:", e)
        return {
            "success": False,
            "message": "Erro na transferência"
        }
    finally:
        conn.close()