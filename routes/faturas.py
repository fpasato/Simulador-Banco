
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from utils.validators import check_session, get_db
from utils.services.banco.faturas import get_faturas, pagar_fatura, registrar_transacao, deletar_fatura, get_valor_fatura, limitar_faturas_pagas, limitar_faturas_pendentes

faturas_bp = Blueprint("faturas", __name__, url_prefix="/faturas")

@faturas_bp.route('/')
def index():
    if not check_session():
        return redirect(url_for('login.login'))
    
    conta_id = session['user_info']['conta_id']
    
    # Atualiza o saldo na sessão
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        session['user_info']['saldo'] = float(resultado[0])
    
    faturas = get_faturas(conta_id)
    return render_template('faturas/index.html', faturas=faturas)



from flask import request, jsonify

@faturas_bp.route('/pagar-todas', methods=['POST'])
def pagar_todas_faturas():
    if not check_session():
        return jsonify({"error": "Não autorizado"}), 401
    
    conta_id = session['user_info']['conta_id']
    
    # Abre a conexão MESTRE
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 1. Busca todas as faturas pendentes
        cursor.execute("SELECT id, valor FROM faturas WHERE conta_id = ? AND status = 'pendente'", (conta_id,))
        faturas_pendentes = cursor.fetchall()
        
        if not faturas_pendentes:
            return jsonify({"error": "Não há faturas pendentes"}), 400
        
        # 2. Calcula valor total
        valor_total = sum(fatura[1] for fatura in faturas_pendentes)
        
        # 3. Verifica saldo
        cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,))
        saldo_atual = float(cursor.fetchone()[0])
        
        if saldo_atual < valor_total:
            return jsonify({"error": f"Saldo insuficiente. Total: R$ {valor_total:.2f}, Saldo: R$ {saldo_atual:.2f}"}), 400
        
        # 4. Processa pagamento de todas as faturas
        novo_saldo = saldo_atual - valor_total
        cursor.execute("UPDATE contas SET saldo = ? WHERE id = ?", (novo_saldo, conta_id))
        
        # 5. Marca todas como pagas e registra transações
        for fatura_id, valor in faturas_pendentes:
            pagar_fatura(fatura_id, conn=conn)
            registrar_transacao(conta_id, valor, 'debito', 'Pagamento de fatura', conn=conn)
            # mantém a fatura no banco como 'pago'
            # depois, aplica o limite de faturas pagas
            limitar_faturas_pagas(conta_id, conn=conn)
        
        # 6. Commita tudo
        conn.commit()
        
        # 7. Atualiza sessão
        session['user_info']['saldo'] = novo_saldo
        
        return jsonify({
            "success": True, 
            "novo_saldo": novo_saldo,
            "faturas_pagas": len(faturas_pendentes),
            "valor_total": valor_total
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@faturas_bp.route('/pagar', methods=['POST'])
def processar_pagamento():
    fatura_id = request.form.get('fatura_id')
    conta_id = session['user_info']['conta_id']
    
    # Abre a conexão MESTRE
    conn = get_db()
    cursor = conn.cursor()

    try:
        # 1. Busca dados (usando a conexão mestre)
        fatura = get_valor_fatura(fatura_id, conta_id) # Note: ajuste essa função também para aceitar conn
        if not fatura:
            return jsonify({"error": "Fatura não encontrada"}), 404
        
        valor_fatura = float(fatura[0])
        
        cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,))
        saldo_atual = float(cursor.fetchone()[0])

        if saldo_atual < valor_fatura:
            return jsonify({"error": "Saldo insuficiente"}), 400

        # 2. Executa as operações USANDO A MESMA CONEXÃO
        # Atualiza saldo manualmente
        novo_saldo = saldo_atual - valor_fatura
        cursor.execute("UPDATE contas SET saldo = ? WHERE id = ?", (novo_saldo, conta_id))

        # Chama suas funções passando a conexão aberta
        pagar_fatura(fatura_id, conn=conn)
        registrar_transacao(conta_id, valor_fatura, 'debito', 'Pagamento de fatura', conn=conn)
        deletar_fatura(fatura_id, conn=conn)

        limitar_faturas_pagas(conta_id, conn=conn) 

        # 3. Commita TUDO de uma vez só no final
        conn.commit()
        
        # Atualiza sessão
        session['user_info']['saldo'] = novo_saldo
        
        return jsonify({"success": True, "novo_saldo": novo_saldo})

    except Exception as e:
        conn.rollback() # Se qualquer função der erro, nada é alterado
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close() # Fecha a conexão mestre