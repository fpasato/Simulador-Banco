from sqlite3 import Date
from utils.validators import get_db
from utils.services.versaldo.functions import get_balance

import random
import time


def create_card(conta_id, tipo):

    if check_card(conta_id):
        return {"success": False, "message": "Cartão já existe"}
    
    # data_validade a 5 anos
    validade = time.strftime("%m/%y", time.localtime(time.time() + 5 * 365 * 24 * 60 * 60))
    cvv = f"{random.randint(0, 999):03d}"
    numero_cartao = gera_numero_cartao()
    tipo = tipo   

    
    if tipo == "credito":
        limite = 3000
        
    elif tipo == "debito":
        limite = None
    
    # Verifica se o cartão já existe
    while check_card(numero_cartao):
        numero_cartao = gera_numero_cartao()

    conn = get_db()
    cursor = conn.cursor()
    
    with conn:
        cursor.execute("INSERT INTO cartoes (conta_id, numero_cartao,validade,cvv,limite, tipo) VALUES (?, ?, ?, ?, ?, ?)", (conta_id, numero_cartao, validade, cvv, limite, tipo))
    return {"success": True, "message": "Cartão criado com sucesso"}

    

def check_card(numero_cartao):
    conn = get_db()
    cursor = conn.cursor()

    with conn:
        cursor.execute("SELECT * FROM cartoes WHERE numero_cartao = ? AND tipo IN ('credito', 'debito')", (numero_cartao,))
    
    result = cursor.fetchall()
    
    # se cartão existir, retorna True
    if result:
        return True
    return False

    
def get_card(numero_conta, tipo):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cartoes WHERE tipo = ? AND conta_id = ?",
        (tipo, numero_conta)
    )

    card = cursor.fetchone()
    
    if card:
        card_dict = dict(card)
        numero_completo = card_dict['numero_cartao']

        if card_dict["tipo"] == "debito":
            card_dict["limite"] = get_balance(card_dict["conta_id"])

        if numero_completo:
            ultimos = numero_completo[-3:]
            card_dict['numero_formatado'] = f"**** **** {ultimos}"
        else:
            card_dict['numero_formatado'] = ""

        return card_dict
    
    return None


def delete_card():
    pass


# Gera número de cartão com 11 dígitos
def gera_numero_cartao():
    numero = ''.join([str(random.randint(0, 9)) for _ in range(11)])
    return numero



def calcular_fatura(cartao_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT SUM(valor) FROM transacoes_cartao
        WHERE cartao_id = ? AND pago = 0
    """, (cartao_id,))

    total = cursor.fetchone()[0] or 0

    return total


def limpar_cartoes():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM cartoes ",
        (numero_conta,)
    )
    conn.commit()
    