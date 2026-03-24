from flask import Blueprint, session, redirect, render_template, request, url_for
import re
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

            # Buscar conta existente
            cursor.execute(
                "SELECT id, numero_conta, saldo FROM contas WHERE usuario_id = ?",
                (account[0],)
            )
            conta_result = cursor.fetchone()

            # Se não houver conta, criar uma nova
            if conta_result is None:
                numero_conta = str(random.randint(100000, 999999))
                cursor.execute(
                    "INSERT INTO contas (usuario_id, numero_conta, saldo) VALUES (?, ?, ?)",
                    (account[0], numero_conta, 0.0)
                )
                conn.commit()
                # Recuperar a conta recém-criada
                cursor.execute(
                    "SELECT id, numero_conta, saldo FROM contas WHERE usuario_id = ?",
                    (account[0],)
                )
                conta_result = cursor.fetchone()

            # Agora conta_result é garantidamente não-None
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

            # Garantir salário mínimo (se a coluna existir)
            try:
                cursor.execute("""
                    UPDATE contas
                    SET salario = 1518
                    WHERE id = ? AND (salario IS NULL OR salario <= 0)
                """, (conta_result[0],))
                conn.commit()
            except Exception as e:
                print("Erro ao definir salário mínimo:", e)

            # Session
            session['user_info'] = {
                'user_id': account[0],
                'user_name': account[1].split()[0],
                'user_full_name': account[1],
                'cpf': account[2],
                'email': account[3],
                'conta_id': conta_result[0],     
                'numero_conta': conta_result[1],
                'saldo': conta_result[2]
            }
                        
            from utils.services.pix.functions import register_default_keys

            # Dentro da rota de login, após obter os dados do usuário:
            register_default_keys(
                session['user_info']['conta_id'],
                session['user_info']['cpf'],
                session['user_info']['email']
            )

        return redirect(url_for("home.home"))

    return render_template("login/index.html")