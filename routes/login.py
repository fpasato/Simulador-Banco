from flask import Blueprint, session, redirect, render_template, request, url_for
import re
import random
from utils.validators import get_db
from werkzeug.security import check_password_hash

login_bp = Blueprint("login", __name__, url_prefix="/login")

from flask import Blueprint, session, redirect, render_template, request, url_for
import random
from utils.validators import get_db
from werkzeug.security import check_password_hash

login_bp = Blueprint("login", __name__, url_prefix="/login")

@login_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template(
                "login/index.html",
                popup_message="Preencha todos os campos",
                popup_type="error"
            )

        conn = get_db()
        cursor = conn.cursor()

        with conn:
            cursor.execute("""
                SELECT id, nome_completo, cpf, email, senha 
                FROM usuarios 
                WHERE email = ?
            """, (email,))
            account = cursor.fetchone()

            if not account:
                return render_template(
                    "login/index.html",
                    popup_message="Email não encontrado",
                    popup_type="error"
                )

            if not check_password_hash(account[4], password):
                return render_template(
                    "login/index.html",
                    popup_message="Senha incorreta",
                    popup_type="error"
                )

            # Buscar conta existente (incluindo first_login_bonus)
            cursor.execute("""
                SELECT id, numero_conta, saldo, first_login_bonus 
                FROM contas 
                WHERE usuario_id = ?
            """, (account[0],))
            conta_result = cursor.fetchone()

            # Se não houver conta, criar uma nova (first_login_bonus será 0 por padrão)
            if conta_result is None:
                numero_conta = str(random.randint(100000, 999999))
                cursor.execute(
                    "INSERT INTO contas (usuario_id, numero_conta, saldo) VALUES (?, ?, ?)",
                    (account[0], numero_conta, 0.0)
                )
                conn.commit()
                # Recuperar a conta recém-criada (agora com first_login_bonus = 0)
                cursor.execute("""
                    SELECT id, numero_conta, saldo, first_login_bonus 
                    FROM contas 
                    WHERE usuario_id = ?
                """, (account[0],))
                conta_result = cursor.fetchone()
                first_login_bonus = 0
            else:
                first_login_bonus = conta_result[3] if conta_result[3] is not None else 0

            # Processar resultado de emprego (se houver)
            resultado = session.pop("resultado_emprego", None)
            if resultado:
                salario = resultado.get("salario")
                if salario:
                    try:
                        cursor.execute("""
                            UPDATE contas
                            SET salario = ?
                            WHERE id = ?
                        """, (salario, conta_result[0]))
                        conn.commit()
                    except Exception as e:
                        print("Erro ao atualizar salário:", e)

            # Garantir salário mínimo
            try:
                cursor.execute("""
                    UPDATE contas
                    SET salario = 1518
                    WHERE id = ? AND (salario IS NULL OR salario <= 0)
                """, (conta_result[0],))
                conn.commit()
            except Exception as e:
                print("Erro ao definir salário mínimo:", e)

            # Conceder bônus de primeiro login (se ainda não recebeu)
            bonus_message = None
            if not first_login_bonus:
                try:
                    # Adiciona 2000 ao saldo e marca como recebido
                    cursor.execute("""
                        UPDATE contas
                        SET saldo = saldo + 2000, first_login_bonus = 1
                        WHERE id = ?
                    """, (conta_result[0],))
                    conn.commit()
                    # Saldo atualizado para a sessão
                    novo_saldo = conta_result[2] + 2000
                    bonus_message = "Parabéns! Você ganhou R$ 2.000 de bônus de primeiro acesso!"
                except Exception as e:
                    novo_saldo = conta_result[2]
            else:
                novo_saldo = conta_result[2]

            # Atualizar sessão do usuário
            session['user_info'] = {
                'user_id': account[0],
                'user_name': account[1].split()[0],
                'user_full_name': account[1],
                'cpf': account[2],
                'email': account[3],
                'conta_id': conta_result[0],
                'numero_conta': conta_result[1],
                'saldo': novo_saldo
            }

            if bonus_message:
                session['bonus_message'] = bonus_message
                session['bonus_type'] = "success"   # para o popup

            # Registrar chaves PIX padrão (se necessário)
            from utils.services.banco.pix import register_default_keys
            register_default_keys(
                session['user_info']['conta_id'],
                session['user_info']['cpf'],
                session['user_info']['email']
            )

        return redirect(url_for("home.home"))

    return render_template("login/index.html")