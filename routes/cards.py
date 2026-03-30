from flask import Blueprint, render_template, redirect, session, request
from utils.services.banco.cartoes import create_card, get_card, calcular_fatura
from utils.validators import check_session

cards_bp = Blueprint("cards", __name__, url_prefix="/cards")

@cards_bp.route("/")
def cards():
    if not check_session():
        return redirect("/login")
  
    user_info = session.get('user_info', {})
    
    titular = user_info.get('user_full_name', 'USUÁRIO')
    titular_upper = titular.upper()
    
    numero_conta = session['user_info']['numero_conta']
    
    cartao_credito = get_card(numero_conta, "credito")
    cartao_debito = get_card(numero_conta, "debito")

    # 🔥 NOVA LÓGICA (SEM TABELA FATURAS)
    if cartao_credito:
        limite = cartao_credito["limite"]
        valor = calcular_fatura(cartao_credito["id"])

        percentual = int((valor / limite) * 100) if limite else 0
        disponivel = f"{limite - valor:.2f}"

        fatura_data = {
            "valor": valor,
            "percentual": percentual,
            "disponivel": disponivel
        }
    else:
        fatura_data = None

    return render_template(
        "cards/index.html",
        cartao_credito=cartao_credito,
        cartao_debito=cartao_debito,
        titular=titular_upper,
        numero_conta=numero_conta,
        fatura=fatura_data
    )
    
    
@cards_bp.route("/createcards", methods=["GET", "POST"])
def createcards():
    if not check_session():
        return redirect("/login")


    numero_conta = session['user_info']['numero_conta']
    tipo = request.form.get("tipo") or request.args.get("tipo")

    if tipo not in ["credito", "debito"]:
        return "Tipo inválido", 400

    # impede duplicado
    if get_card(numero_conta, tipo):
        return redirect("/cards")

    create_card(numero_conta, tipo)

    return redirect("/cards")