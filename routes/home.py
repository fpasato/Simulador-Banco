from flask import Blueprint, session, redirect, render_template, url_for, jsonify
from utils.validators import check_session, get_db

home_bp = Blueprint("home", __name__, url_prefix="/home")

@home_bp.route("/")
def home():
    if not check_session():
        return redirect(url_for("login.login"))
    
    # Captura mensagem de bônus e tipo (se houver)
    bonus_message = session.pop('bonus_message', None)
    bonus_type = session.pop('bonus_type', None)
    
    resultado = session.pop("resultado_emprego", None)
    
    user_info = session.get("user_info", {})
    nome_usuario = user_info.get("user_name", "Usuário")
    
    if resultado and resultado.get("salario"):
        conta_id = user_info.get("conta_id")
        
        if conta_id:
            salario_novo = resultado["salario"]
            conn = get_db()
            cursor = conn.cursor()
            # Atualiza a coluna salario da conta
            cursor.execute("UPDATE contas SET salario = ? WHERE id = ?", (salario_novo, conta_id))
            conn.commit()
            # Atualiza também na sessão para manter consistência
            user_info["salario"] = salario_novo
            session["user_info"] = user_info
            conn.close()
    
    return render_template(
        "home/index.html",
        nome_usuario=nome_usuario,
        resultado=resultado,
        popup_message=bonus_message,   
        popup_type=bonus_type          
    )
        
    
@home_bp.route("/verificar-salario")
def verificar_salario():
    try:
        if not check_session():
            return jsonify({"status": "erro"})

        conta_id = session["user_info"]["conta_id"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, valor FROM transacoes_conta
            WHERE conta_id = ? AND descricao = 'Salário automático'
            ORDER BY id DESC LIMIT 1
        """, (conta_id,))

        ultima = cursor.fetchone()

        if not ultima:
            return jsonify({"novo": False})

        ultimo_id, valor = ultima

        ultimo_visto = session.get("ultimo_salario_id")

        if not ultimo_visto:
            session["ultimo_salario_id"] = ultimo_id
            return jsonify({"novo": True, "valor": valor})

        # NOVO SALÁRIO
        if ultimo_visto != ultimo_id:
            session["ultimo_salario_id"] = ultimo_id
            return jsonify({"novo": True, "valor": valor})

        return jsonify({"novo": False})

    except Exception as e:
        print("ERRO verificar_salario:", e)
        return jsonify({"novo": False})


@home_bp.route("/recarregar-saldo")
def recarregar_saldo():
    if not check_session():
        return jsonify({"status": "erro"})
    
    conta_id = session["user_info"]["conta_id"]
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,))
    resultado = cursor.fetchone()
    
    if resultado:
        session["user_info"]["saldo"] = resultado[0]
        return jsonify({"saldo": resultado[0]})
    
    return jsonify({"status": "erro"})


@home_bp.route("/get-saldo")
def get_saldo():
    if not check_session():
        return jsonify({"status": "erro"})
    
    conta_id = session["user_info"]["conta_id"]
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 🔥 BUSCA DIRETO DO BANCO (não da sessão)
    cursor.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        return jsonify({"saldo": float(resultado[0])})  # Garante que vem como número
    
    return jsonify({"status": "erro"})