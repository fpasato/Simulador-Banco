from utils.validators import get_db, cpf_exists, account_already_exists, verifica_cpf, email_exists
import re
import time
import random
from werkzeug.security import generate_password_hash


def gerar_numero_conta():
    tempo = int(time.time())
    aleatorio = random.randint(100,999)

    numero = str(tempo)[-5:] + str(aleatorio)
    return numero


    
def create_user(nome_completo, cpf, email, senha):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome_completo, cpf, email, senha) VALUES (?, ?, ?, ?)",
        (nome_completo, cpf, email, senha)
    )
    db.commit()
    return cursor.lastrowid  # Retorna o ID do usuário criado
    
def create_account(numero_conta, usuario_id):
    db = get_db()
    db.execute(
        "INSERT INTO contas (numero_conta, usuario_id) VALUES (?, ?)",
        (numero_conta, usuario_id)
    )
    db.commit()
    
    

def register_account(form_data):
    """
    Recebe form_data do Flask (request.form) e tenta criar a conta.
    Retorna dict: {"success": bool, "message": str, "numero_conta": str (opcional)}
    """
    nome = form_data.get("name").capitalize()
    cpf = re.sub(r"\D", "", form_data.get("cpf"))
    senha = form_data.get("password")
    email = form_data.get("email")
    confirmar_senha = form_data.get("confirm_password")
    numero_conta = gerar_numero_conta()   
    while account_already_exists(numero_conta):
        numero_conta = gerar_numero_conta()
    
    # verifica se o nome contem numeros
    if any(char.isdigit() for char in nome):
        return {"success": False, "message": "O nome não pode conter números"}
    
    # Verifica se as senhas são iguais
    if senha != confirmar_senha:
        return {"success": False, "message": "As senhas não conferem"}
    
    # Verifica se o CPF é válido
    if not verifica_cpf(cpf):
        return {"success": False, "message": "CPF inválido"}
    
    # Verifica se o CPF já está cadastrado
    if cpf_exists(cpf):
        return {"success": False, "message": "CPF já cadastrado"}
    
    # Verifica se o número da conta já está cadastrado
    if account_already_exists(numero_conta):
        return {"success": False, "message": "Conta já cadastrada"}
    
    # Verifica se o email já está cadastrado
    if email_exists(email):
        return {"success": False, "message": "Email já cadastrado"}
    
    
    senha_hash = generate_password_hash(senha)
    usuario_id = create_user(nome, cpf, email, senha_hash)
    create_account(numero_conta, usuario_id)

    return {"success": True, "message": "Conta criada! Faça seu login.", "numero_conta": numero_conta}

