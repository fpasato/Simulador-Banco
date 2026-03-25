from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify
import sqlite3
import time
from collections import defaultdict

from utils.services.banco.investimento import (
    carregar_carteira, load_all_investiments,
    history_prices, buy_investment, notificacoes_pendentes, notificacoes_lock,
    processar_investimentos_expirados
)
from utils.validators import get_db

investimento_bp = Blueprint('investimento', __name__)
from collections import defaultdict

@investimento_bp.route("/investimento")
def investimento():
    if 'user_info' not in session:
        return redirect(url_for('auth.login'))
    conta_id = session['user_info']['conta_id']
    popup_message = session.pop('popup_message', None)
    popup_type = session.pop('popup_type', None)

    # Carrega todos os investimentos ativos
    investimentos_data = load_all_investiments()
    investimentos_disponiveis = investimentos_data['investimentos']
    print("TOTAL ATIVOS:", len(investimentos_disponiveis))

    # Agrupa por tipo -> setor
    investimentos_por_tipo = defaultdict(lambda: defaultdict(list))
    for ativo in investimentos_disponiveis:
        tipo = ativo.get('tipo', 'outros')
        setor = ativo.get('setor', 'geral')
        investimentos_por_tipo[tipo][setor].append(ativo)

    # (Opcional) imprime para debug no terminal
    for tipo, setores in investimentos_por_tipo.items():
        for setor, ativos in setores.items():
            print(f"{tipo} / {setor}: {len(ativos)} ativos")

    # Converte para dicionário normal (mais fácil de iterar no template)
    investimentos_por_tipo = {k: dict(v) for k, v in investimentos_por_tipo.items()}

    # Restante do código (carteira, saldo, etc.)
    carteira_data = carregar_carteira(conta_id)
    conn = get_db()
    conn.row_factory = sqlite3.Row
    conta = conn.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,)).fetchone()
    saldo_atual = conta['saldo'] if conta else 0
    conn.close()

    if not carteira_data or not carteira_data.get('investimentos'):
        carteira = []
        valor_carteira = 0
    else:
        carteira = carteira_data['investimentos']
        valor_carteira = sum(item['saldo'] for item in carteira) if carteira else 0

    return render_template(
        "investimento/index.html",
        carteira=carteira,
        investimentos_disponiveis=investimentos_disponiveis,   # opcional
        investimentos_por_tipo=investimentos_por_tipo,        # ESSENCIAL
        valor_carteira=valor_carteira,
        saldo=saldo_atual,
        session=session,
        popup_message=popup_message,
        popup_type=popup_type
    )

@investimento_bp.route("/investimento/historico/<int:investimento_id>")
def historico(investimento_id):
    try:
        history = history_prices(investimento_id)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@investimento_bp.route("/investimento/comprar", methods=["POST"])
def comprar():
    if 'user_info' not in session:
        return redirect(url_for('auth.login'))

    conta_id = session['user_info']['conta_id']
    investimento_id = request.form.get('investimento_id')
    quantidade = float(request.form.get('quantidade', 1))
    tempo_em_mili = int(request.form.get('tempo', 60000))

    print(f"DEBUG: Compra - conta_id={conta_id}, investimento_id={investimento_id}, quantidade={quantidade}, tempo={tempo_em_mili}")

    success = buy_investment(conta_id, investimento_id, quantidade, tempo_em_mili)

    if success:
        session['popup_message'] = "Compra realizada com sucesso!"
        session['popup_type'] = "success"
    else:
        # Verificar o motivo exato
        conn = get_db()
        ativo = conn.execute("SELECT id, nome, ativo FROM investimentos WHERE id = ?", (investimento_id,)).fetchone()
        conn.close()
        if not ativo:
            print("DEBUG: Ativo não encontrado no banco")
            session['popup_message'] = f"Investimento {investimento_id} não encontrado."
        elif ativo['ativo'] != 1:
            print(f"DEBUG: Ativo {investimento_id} está inativo")
            session['popup_message'] = "Investimento não está disponível para compra."
        else:
            session['popup_message'] = "Saldo insuficiente."
        session['popup_type'] = "error"

    return redirect(url_for('investimento.investimento'))


@investimento_bp.route("/investimento/vender", methods=["POST"])
def vender():
    if 'user_info' not in session:
        return redirect(url_for('auth.login'))
    
    conta_id = session['user_info']['conta_id']
    investimento_id = request.form.get('investimento_id')
    quantidade = int(request.form.get('quantidade', 1))
    
    # 1. Buscar o investimento e verificar se pertence ao usuário
    conn = get_db()
    conn.row_factory = sqlite3.Row
    
    # Verifica se é um investimento permanente (carteira_investimentos)
    item = conn.execute("""
        SELECT ci.quantidade, ci.preco_medio, i.valor_cota
        FROM carteira_investimentos ci
        JOIN investimentos i ON i.id = ci.investimento_id
        WHERE ci.conta_id = ? AND ci.investimento_id = ?
    """, (conta_id, investimento_id)).fetchone()
    
    if not item:
        # Pode ser um investimento temporário? Se sim, bloqueie venda antecipada
        temporario = conn.execute("""
            SELECT quantidade, preco_medio, tempo_inicio, duracao, i.valor_cota
            FROM investimentos_temporarios it
            JOIN investimentos i ON i.id = it.investimento_id
            WHERE it.conta_id = ? AND it.investimento_id = ?
        """, (conta_id, investimento_id)).fetchone()
        
        if temporario:
            # Verifica se ainda não expirou (não pode vender antes do prazo)
            agora = int(time.time() * 1000)
            if (temporario['tempo_inicio'] + temporario['duracao']) > agora:
                session['popup_message'] = "Investimentos com prazo não podem ser vendidos antes do vencimento."
                session['popup_type'] = "error"
                conn.close()
                return redirect(url_for('investimento.investimento'))
            else:
                # Já expirou, mas ainda não foi processado? Permite venda manual? Melhor evitar.
                session['popup_message'] = "Este investimento já expirou e será liquidado automaticamente."
                session['popup_type'] = "info"
                conn.close()
                return redirect(url_for('investimento.investimento'))
        else:
            session['popup_message'] = "Investimento não encontrado na sua carteira."
            session['popup_type'] = "error"
            conn.close()
            return redirect(url_for('investimento.investimento'))
    
    # 2. Validar quantidade
    if quantidade <= 0 or quantidade > item['quantidade']:
        session['popup_message'] = "Quantidade inválida."
        session['popup_type'] = "error"
        conn.close()
        return redirect(url_for('investimento.investimento'))
    
    # 3. Calcular valor da venda e atualizar saldo
    valor_venda = quantidade * item['valor_cota']
    conn.execute("UPDATE contas SET saldo = saldo + ? WHERE id = ?", (valor_venda, conta_id))
    
    # 4. Atualizar carteira: remover quantidade ou deletar se zerar
    nova_quantidade = item['quantidade'] - quantidade
    if nova_quantidade == 0:
        conn.execute("DELETE FROM carteira_investimentos WHERE conta_id = ? AND investimento_id = ?",
                     (conta_id, investimento_id))
    else:
        conn.execute("UPDATE carteira_investimentos SET quantidade = ? WHERE conta_id = ? AND investimento_id = ?",
                     (nova_quantidade, conta_id, investimento_id))
    
    conn.commit()
    conn.close()
    
    session['popup_message'] = f"Venda de {quantidade} cota(s) realizada com sucesso!"
    session['popup_type'] = "success"
    return redirect(url_for('investimento.investimento'))



@investimento_bp.route("/investimento/atualizar-precos")
def atualizar_precos():
    if 'user_info' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    try:
        conta_id = session['user_info'].get('conta_id')
        if not conta_id:
            return jsonify({'error': 'Conta não encontrada'}), 401
        processar_investimentos_expirados()
        conn = get_db()
        conn.row_factory = sqlite3.Row
        conta = conn.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,)).fetchone()
        saldo_atual = conta['saldo'] if conta else 0
        conn.close()
        carteira_data = carregar_carteira(conta_id)
        carteira = carteira_data['investimentos'] if carteira_data else []
        investimentos_data = load_all_investiments()
        investimentos_disponiveis = investimentos_data['investimentos']
        with notificacoes_lock:
            notificacoes = notificacoes_pendentes.pop(conta_id, [])
            
        from datetime import datetime
        server_time = int(time.time() * 1000)  # em ms
        
        
        return jsonify({
            'saldo': saldo_atual,
            'carteira': carteira,
            'ativos_disponiveis': investimentos_disponiveis,
            'notificacoes': notificacoes,
            'server_time': server_time
        })
    except Exception as e:
        print(f"Erro na API de preços: {e}")
        return jsonify({'error': str(e)}), 500

def _obter_detalhes_item(conta_id, tipo, id_param, investimento_id_param):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    try:
        conta = conn.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,)).fetchone()
        saldo_conta = conta["saldo"] if conta else 0
        valor_carteira_total = conn.execute("""
            SELECT COALESCE(SUM(ci.quantidade * i.valor_cota), 0) AS valor_total
            FROM carteira_investimentos ci
            JOIN investimentos i ON i.id = ci.investimento_id
            WHERE ci.conta_id = ?
        """, (conta_id,)).fetchone()["valor_total"]
        if tipo == 'temporario':
            item = conn.execute("""
                SELECT it.id, it.investimento_id, it.quantidade, it.preco_medio,
                    it.tempo_inicio, it.duracao,
                    i.nome, i.valor_cota as preco_atual, i.risco, i.descricao
                FROM investimentos_temporarios it
                JOIN investimentos i ON i.id = it.investimento_id
                WHERE it.id = ? AND it.conta_id = ?
            """, (id_param, conta_id)).fetchone()
            if not item:
                return None
            item_dict = dict(item)
            # expira_em em segundos para o frontend
            expira_em = (item_dict['tempo_inicio'] + item_dict['duracao']) // 1000
            saldo_total = item_dict['quantidade'] * item_dict['preco_atual']
            gasto_total = item_dict['quantidade'] * item_dict['preco_medio']
            lucro_prejuizo = saldo_total - gasto_total
            return {
                'tipo': 'carteira', 'temporario': True,
                'investimento_id': item_dict['investimento_id'], 'nome': item_dict['nome'],
                'quantidade': item_dict['quantidade'], 'preco_medio': item_dict['preco_medio'],
                'preco_atual': item_dict['preco_atual'], 'lucro_prejuizo': lucro_prejuizo,
                'risco': item_dict['risco'], 'descricao': item_dict['descricao'],
                'expira_em': expira_em, 'saldo_conta': saldo_conta,
                'valor_carteira_total': valor_carteira_total
            }
        else:  # normal
            item = conn.execute("""
                SELECT ci.quantidade, ci.preco_medio, i.nome, i.valor_cota as preco_atual, i.risco, i.descricao
                FROM carteira_investimentos ci
                JOIN investimentos i ON i.id = ci.investimento_id
                WHERE ci.conta_id = ? AND ci.investimento_id = ?
            """, (conta_id, investimento_id_param)).fetchone()
            if not item:
                ativo = conn.execute("SELECT id, nome, valor_cota, risco, descricao FROM investimentos WHERE id = ?", (investimento_id_param,)).fetchone()
                if ativo:
                    return {
                        'tipo': 'explorar', 'nome': ativo['nome'], 'preco_atual': ativo['valor_cota'],
                        'risco': ativo['risco'], 'descricao': ativo['descricao'],
                        'saldo_conta': saldo_conta, 'valor_carteira_total': valor_carteira_total
                    }
                else:
                    return None
            saldo_total = item['quantidade'] * item['preco_atual']
            gasto_total = item['preco_medio'] * item['quantidade']
            lucro_prejuizo = saldo_total - gasto_total
            return {
                'tipo': 'carteira', 'temporario': False,
                'investimento_id': investimento_id_param, 'nome': item['nome'],
                'quantidade': item['quantidade'], 'preco_medio': item['preco_medio'],
                'preco_atual': item['preco_atual'], 'lucro_prejuizo': lucro_prejuizo,
                'risco': item['risco'], 'descricao': item['descricao'],
                'saldo_conta': saldo_conta, 'valor_carteira_total': valor_carteira_total
            }
    finally:
        conn.close()

@investimento_bp.route("/investimento/detalhes-item")
def detalhes_item():
    if 'user_info' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    conta_id = session['user_info']['conta_id']
    tipo = request.args.get('tipo')
    id_param = request.args.get('id')
    investimento_id_param = request.args.get('investimento_id')
    if not tipo or not id_param or not investimento_id_param:
        return jsonify({'error': 'Parâmetros incompletos'}), 400
    dados = _obter_detalhes_item(conta_id, tipo, id_param, investimento_id_param)
    if not dados:
        return jsonify({'error': 'Item não encontrado'}), 404
    return jsonify(dados)

@investimento_bp.route("/investimento/detalhes/<int:investimento_id>")
def detalhes_investimento(investimento_id):
    if 'user_info' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    conta_id = session['user_info']['conta_id']
    dados = _obter_detalhes_item(conta_id, 'normal', str(investimento_id), str(investimento_id))
    if not dados:
        return jsonify({'error': 'Investimento não encontrado'}), 404
    return jsonify(dados)