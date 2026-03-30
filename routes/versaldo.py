from flask import Blueprint, session, redirect, render_template
from utils.validators import check_session
from utils.validators import get_account_by_number





versaldo_bp = Blueprint("versaldo", __name__, url_prefix="/saldo")

@versaldo_bp.route("/")
def versaldo():
    if not check_session():
        return redirect("/login")
    
    numero_conta = session['user_info']['numero_conta']
    user = get_account_by_number(numero_conta)
    
    return render_template("versaldo/index.html", conta_usuario=user, nome_titular=user['nome_completo'])
    

