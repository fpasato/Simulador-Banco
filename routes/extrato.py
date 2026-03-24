from flask import Blueprint, render_template, session, redirect, url_for
from utils.services.banco.extrato import get_transacoes

extrato_bp = Blueprint('extrato', __name__, url_prefix='/extrato')

@extrato_bp.route('/')
def extrato():
    # Verifica se o usuário está logado
    if 'user_info' not in session:
        return redirect(url_for('login.login'))  # ajuste para sua rota de login

    conta_id = session['user_info']['conta_id']   # ID da conta do usuário
    transacoes = get_transacoes(conta_id)         # passa o ID correto
    return render_template('extrato/index.html', transacoes=transacoes)