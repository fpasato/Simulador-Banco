
import os
import sqlite3
from flask import session


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)  # 20 segundos de timeout
    conn.row_factory = sqlite3.Row
    # Ativa o modo WAL
    conn.execute("PRAGMA journal_mode=WAL")
    return conn



def get_account_by_number(numero_conta):
    conn = get_db()
    cursor = conn.cursor()
    
    with conn:
        cursor.execute("""
            SELECT c.id, u.nome_completo, u.cpf, c.saldo, c.numero_conta 
            FROM contas c 
            JOIN usuarios u ON c.usuario_id = u.id 
            WHERE c.numero_conta = ?
        """, (numero_conta,))
        resultado = cursor.fetchone()
    
    if resultado is None:
        return False
    

    conta = {
        'id': resultado[0], 
        'nome_completo': resultado[1],
        'cpf': resultado[2],
        'saldo': resultado[3], 
        'numero_conta': resultado[4]
    }
    
    return conta 




def get_account_by_id(id):
    conn = get_db()
    cursor = conn.cursor()
    
    with conn:
        cursor.execute("""
            SELECT c.id, u.nome_completo, u.cpf, c.saldo, c.numero_conta 
            FROM contas c 
            JOIN usuarios u ON c.usuario_id = u.id 
            WHERE c.id = ?
        """, (id,))
        resultado = cursor.fetchone()
    
    if resultado is None:
        return False
    
    # Se encontrou, retorna os dados da conta
    conta = {
        'id': resultado[0], 
        'nome_completo': resultado[1],
        'cpf': resultado[2],
        'saldo': resultado[3], 
        'numero_conta': resultado[4]
    }
    
    return conta 






def account_already_exists(numero_conta):
    
    conn = get_db()
    cursor = conn.cursor()
    with conn:
        cursor.execute("SELECT 1 FROM contas WHERE numero_conta=? LIMIT 1", (numero_conta,))
        resultado = cursor.fetchone() 
    return resultado is not None

def cpf_exists(cpf):
    conn = get_db()
    cursor = conn.cursor()
    
    with conn:
        cursor.execute("SELECT 1 FROM usuarios WHERE cpf=? LIMIT 1", (cpf,))
        resultado = cursor.fetchone()
    
    return resultado is not None


def verifica_cpf(cpf):
    
    if len(cpf) != 11:
        return False
    
    # verifica d1
    soma, indice_digito = 0, 0
    for n in range(10, 1, -1): 
        soma += int(cpf[indice_digito]) * n
        indice_digito +=1
    d1 = 0 if soma % 11 < 2 else 11 - (soma % 11)

    # verifica d2
    soma, indice_digito = 0, 0
    for n in range(11, 2, -1):
        soma += int(cpf[indice_digito]) * n
        indice_digito +=1
    soma += d1 * 2
    
    d2 = 0 if soma % 11 < 2 else 11- (soma % 11)

    if d1 == int(cpf[-2]) and d2 == int(cpf[-1]):
        return True
    else:
        return False


def email_exists(email):
    conn = get_db()
    cursor = conn.cursor()
    
    with conn:
        cursor.execute("SELECT 1 FROM usuarios WHERE email=? LIMIT 1", (email,))
        resultado = cursor.fetchone()
    
    return resultado is not None


def check_session():
    return 'user_info' in session