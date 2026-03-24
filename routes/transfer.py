from flask import Blueprint, request, session, render_template
from flask import redirect, url_for
from utils.validators import get_account_by_number, get_db
from utils.services.banco.transferencia import confirmarTransferencia

transfer_bp = Blueprint("transfer", __name__, url_prefix="/transfer")

@transfer_bp.route("/", methods=["GET", "POST"])
def transfer():

    conta_usuario = session['user_info']['conta_id']
    
    # Processa mensagens da sessão
    popup_message = session.pop('popup_message', None)
    popup_type = session.pop('popup_type', None)
    
    if request.method == "GET":
        return render_template(
            "transfer/index.html",
            nome_usuario=session['user_info']['user_name'],
            conta_usuario=conta_usuario,  
            conta_destino_info=None,
            popup_message=popup_message,
            popup_type=popup_type
        )

    elif request.method == "POST":
        
        acao = request.form.get("acao")
        
        #se a ação for buscar conta destino
        if acao == "buscar":
            conta_destino_num = request.form.get("conta-destino")
            conta = get_account_by_number(conta_destino_num)
            
            # se a conta não existir
            if not conta:
                return render_template(
                    "transfer/index.html",
                    popup_message="Conta destino não encontrada",
                    popup_type="error", 
                    conta_destino_info=None
                )
            # se a conta for igual a conta do usuário
            if conta['numero_conta'] == session['user_info']['numero_conta']:
                return render_template(
                    "transfer/index.html",
                    popup_message="Não é possível transferir para a própria conta",
                    popup_type="error",
                    conta_destino_info=None
                )
            
            # se a conta existir e for diferente da conta do usuário
            conta_destino_info = {
                "nome": conta['nome_completo'],
                "numero_conta": conta['numero_conta'],
                "agencia": "0010",
                "saldo": conta['saldo']  
            }
            
            return render_template(
                "transfer/index.html",
                nome_usuario=session['user_info']['user_name'],
                conta_usuario=conta_usuario, 
                conta_destino_info=conta_destino_info
            )
        
    return redirect(url_for("transfer.transfer"))


@transfer_bp.route("/transferir", methods=["POST"])
def transferir():
    
    if 'user_info' not in session:
        return redirect("/login")

    conta_usuario = session['user_info']['conta_id']
    conta_destino_num = request.form.get("conta-destino-final")
    valor_str = request.form.get("valor")

    if not valor_str:
        return render_template(
            "transfer/index.html",
            popup_message="Valor não informado",
            popup_type="error",
            conta_destino_info=None
        )

    # valida número
    if not valor_str.replace('.', '').isdigit():
        return render_template(
            "transfer/index.html",
            popup_message="Valor inválido",
            popup_type="error",
            conta_destino_info=None
        )

    valor = float(valor_str)

    conta_destino = get_account_by_number(conta_destino_num)

    if not conta_destino:
        return render_template(
            "transfer/index.html",
            popup_message="Conta destino não encontrada",
            popup_type="error",
            conta_destino_info=None
        )

    if conta_destino['id'] == conta_usuario:
        return render_template(
            "transfer/index.html",
            popup_message="Não pode transferir para si mesmo",
            popup_type="error",
            conta_destino_info=None
        )

    resultado = confirmarTransferencia(conta_usuario, conta_destino['id'], valor)

    if resultado["success"]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_usuario,))
        novo_saldo = cursor.fetchone()[0]
        conn.close()

        session['user_info']['saldo'] = novo_saldo

        session['popup_message'] = "Transferência realizada com sucesso!"
        session['popup_type'] = "success"

        return redirect(url_for("transfer.transfer"))

    else:
        return render_template(
            "transfer/index.html",
            popup_message=resultado["message"],
            popup_type="error",
            conta_destino_info=conta_destino
        )