from flask import Blueprint, render_template, session, redirect, url_for, request
from utils.validators import get_db
from utils.services.pix.functions import (
    get_all_keys, 
    get_key_by_value,
    create_random_key, 
    register_key, 
    delete_key_by_id,
    mask_cpf
)

pix_bp = Blueprint("pix", __name__, url_prefix="/pix")

# O before_request agora é menos necessário, mas podemos mantê-lo por segurança
@pix_bp.before_request
def redirect_pix_subroutes():
    subroutes = ['/pix/generate_random_key', '/pix/register_key']
    if request.method == 'GET' and request.path in subroutes:
        return redirect(url_for('pix.pix'))

@pix_bp.route("/", methods=["GET"])
def pix():
    if 'user_info' not in session:
        return redirect("/login")
    
    popup_message = session.pop('popup_message', None)
    popup_type = session.pop('popup_type', None)

    
    keys = get_all_keys(session['user_info']['conta_id'])
    
    # Se não houver chaves e não houver outra mensagem na sessão, define o aviso
    if not keys and not popup_message:
        popup_message = "Nenhuma chave encontrada"
        popup_type = "error"
    
    # Se não houver dados do destinatário na sessão, limpa a aba ativa (volta para padrão)
    if not session.get('destinatario_nome'):
        session.pop('active_tab', None)

    
    return render_template(
        "pix/index.html", 
        keys=keys,
        popup_message=popup_message,
        popup_type=popup_type
    )
    
@pix_bp.route("/generate_random_key", methods=["POST"])
def generate_random_key():
    if 'user_info' not in session:
        return {"success": False}, 401

    key = create_random_key()
    session['temp_key'] = key["chave"]

    return {
        "success": True,
        "chave": key["chave"]
    }

@pix_bp.route("/register_key", methods=["GET", "POST"])
def register_key_route():
    if request.method == "GET":
        return redirect(url_for('pix.pix'))
    
    if 'user_info' not in session:
        return redirect("/login")
    
    if 'temp_key' not in session:
        session['popup_message'] = "Nenhuma chave temporária encontrada"
        session['popup_type'] = "error"
        return redirect(url_for('pix.pix'))

    conta_id = session['user_info']['conta_id']
    key = session['temp_key']
    
    result = register_key(key, conta_id)
    
    if result["success"]:
        session.pop('temp_key', None)
        session['popup_message'] = f"Chave {key} registrada!"
        session['popup_type'] = "success"
    else:
        session['popup_message'] = "Erro ao registrar chave"
        session['popup_type'] = "error"

    # REDIRECIONA para a index.
    return redirect(url_for('pix.pix'))

@pix_bp.route("/exclude-key/<int:key_id>", methods=["GET"])
def exclude_key(key_id):
    if 'user_info' not in session:
        return redirect("/login")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT tipo FROM chaves_pix WHERE id = ?", (key_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        session['popup_message'] = "Chave não encontrada"
        session['popup_type'] = "error"
        return redirect(url_for('pix.pix'))
    
    if row[0] in ["cpf", "email"]:
        session['popup_message'] = "Não é possível excluir CPF ou Email"
        session['popup_type'] = "error"
        return redirect(url_for('pix.pix'))
    
    # Deleta a chave
    result = delete_key_by_id(key_id)
    
    if result["success"]:
        session['popup_message'] = "Chave excluída com sucesso!"
        session['popup_type'] = "success"
        session['active_tab'] = 'chaves' 
    else:
        session['popup_message'] = "Erro ao excluir chave"
        session['popup_type'] = "error"
        session['active_tab'] = 'chaves'  
        
    return redirect(url_for('pix.pix'))



@pix_bp.route("/transferir", methods=["GET", "POST"])
def transferir():
    if request.form.get("action") == "verificar":
        chave_destino = request.form.get("chave_destino")
        valor = request.form.get("valor")

        result = get_key_by_value(chave_destino)

        if result["success"]:
            
            #verifica se a chave é da mesma conta
            if result["data"]["conta_id"] == session['user_info']['conta_id']:
                session['popup_message'] = "Não é possível transferir para a mesma conta"
                session['popup_type'] = "error"
                session['active_tab'] = 'transferir'
                return redirect(url_for('pix.pix'))
            
            session['destinatario_nome'] = result["data"]["nome"]
            session['destinatario_cpf'] = mask_cpf(result["data"]["cpf"])
            session['destinatario_conta_id'] = result["data"]["conta_id"]
            session['destinatario_chave'] = chave_destino
            session['destinatario_tipo_chave'] = result["data"]["tipo_chave"] 
            session['destinatario_valor'] = valor
            session['active_tab'] = 'transferir'
            return redirect(url_for('pix.pix'))
        else:
            session['popup_message'] = "Chave não encontrada"
            session['popup_type'] = "error"
            session['active_tab'] = 'transferir'
            return redirect(url_for('pix.pix'))
        
    elif request.form.get("action") == "pagar":
        conta_origem = session['user_info']['conta_id']
        conta_destino = session.get('destinatario_conta_id')
        valor = float(session.get('destinatario_valor', 0))
        chave_destino = session.get('destinatario_chave')
        tipo_chave_destino = session.get('destinatario_tipo_chave')

        # Validações
        if not conta_destino or not chave_destino or not tipo_chave_destino:
            session['popup_message'] = "Dados da transferência incompletos. Refaaça a consulta."
            session['popup_type'] = "error"
            session['active_tab'] = 'transferir'
            return redirect(url_for('pix.pix'))

        if conta_origem == conta_destino:
            session['popup_message'] = "Você não pode transferir para si mesmo"
            session['popup_type'] = "error"
            session['active_tab'] = 'transferir'
            return redirect(url_for('pix.pix'))

        conn = get_db()
        cursor = conn.cursor()

        try:
            # LOG: verificar chaves da conta de origem
            cursor.execute("SELECT chave FROM chaves_pix WHERE conta_id = ?", (conta_origem,))
            chaves_origem = cursor.fetchall()
            print(f"DEBUG: Chaves encontradas para conta {conta_origem}: {chaves_origem}")  # <- importante
            if not chaves_origem:
                raise Exception("Você não possui nenhuma chave Pix cadastrada para realizar transferências.")
            chave_origem = chaves_origem[0][0]  # primeira chave

            cursor.execute("BEGIN")
            
            
            # Verifica saldo
            cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_origem,))
            saldo = cursor.fetchone()[0]
            if saldo < valor:
                raise Exception("Saldo insuficiente")

            # Atualiza saldos
            cursor.execute("UPDATE contas SET saldo = saldo - ? WHERE id = ?", (valor, conta_origem))
            cursor.execute("UPDATE contas SET saldo = saldo + ? WHERE id = ?", (valor, conta_destino))

            # Registra transação na conta de origem (débito)
            cursor.execute("""
                INSERT INTO transacoes_conta (conta_id, valor, tipo, descricao)
                VALUES (?, ?, ?, ?)
            """, (conta_origem, -valor, 'pix_enviado', f'Transferência via Pix para {chave_destino}'))
            transacao_origem_id = cursor.lastrowid

            # Registra transação na conta de destino (crédito)
            cursor.execute("""
                INSERT INTO transacoes_conta (conta_id, valor, tipo, descricao)
                VALUES (?, ?, ?, ?)
            """, (conta_destino, valor, 'pix_recebido', f'Recebido via Pix de {chave_origem}'))
            transacao_destino_id = cursor.lastrowid  # não usado diretamente, mas pode ser útil

            # Registra detalhes do Pix (vinculado à transação de origem)
            cursor.execute("""
                INSERT INTO transacoes_pix (transacao_id, chave_origem, chave_destino, tipo_chave, descricao)
                VALUES (?, ?, ?, ?, ?)
            """, (transacao_origem_id, chave_origem, chave_destino, tipo_chave_destino, f'Pix no valor de R$ {valor:.2f}'))

            conn.commit()

            # Limpa sessão (dados do destinatário)
            session.pop('destinatario_nome', None)
            session.pop('destinatario_cpf', None)
            session.pop('destinatario_chave', None)
            session.pop('destinatario_tipo_chave', None)
            session.pop('destinatario_valor', None)
            session.pop('destinatario_conta_id', None)

            # Atualiza saldo na sessão
            cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_origem,))
            novo_saldo = cursor.fetchone()[0]
            session['user_info']['saldo'] = novo_saldo

            session['popup_message'] = "Transferência realizada com sucesso!"
            session['popup_type'] = "success"
            session['active_tab'] = 'transferir'

        except Exception as e:
            conn.rollback()
            session['popup_message'] = str(e) if str(e) else "Erro ao realizar transferência"
            session['popup_type'] = "error"
        finally:
            conn.close()

        return redirect(url_for('pix.pix'))
        
        
@pix_bp.route("/cancelar", methods=["POST"])
def cancelar_transferencia():
    session.pop('destinatario_nome', None)
    session.pop('destinatario_cpf', None)
    session.pop('destinatario_chave', None)
    session.pop('destinatario_valor', None)
    session.pop('destinatario_conta_id', None)

    session['active_tab'] = 'transferir'

    return redirect(url_for('pix.pix'))

