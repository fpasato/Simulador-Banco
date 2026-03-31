import random
import sqlite3

from datetime import datetime, timedelta

def pagar_salarios():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, salario, saldo, ultimo_salario
        FROM contas
    """)

    contas = cursor.fetchall()
    agora = datetime.now()

    for conta_id, salario, saldo, ultimo_salario in contas:
        deve_pagar = False

        if ultimo_salario is None:
            # Nunca recebeu – paga agora
            deve_pagar = True
        else:
            ultima = datetime.fromisoformat(ultimo_salario)
            if agora - ultima >= timedelta(seconds=30):
                deve_pagar = True

        if not deve_pagar:
            continue

        # 💰 Pagar salário inteiro
        novo_saldo = saldo + salario

        cursor.execute("""
            UPDATE contas
            SET saldo = ?, ultimo_salario = ?
            WHERE id = ?
        """, (novo_saldo, agora.isoformat(), conta_id))

        cursor.execute("""
            INSERT INTO transacoes_conta (conta_id, valor, tipo, descricao)
            VALUES (?, ?, 'deposito', 'Salário automático')
        """, (conta_id, salario))

    conn.commit()
    conn.close()


def calcula_pontos(request):
    pontos_total = 0
    
    # Soma todos os valores das respostas
    for i in range(1, 7):
        resposta = request.form.get(f"q{i}")
        if resposta:
            pontos_total += int(resposta)
    
    # classificação pela pontuação total (máximo 18 pontos)
    if pontos_total >= 13:  # 5 ou 6 respostas com valor 2+ = Perfil Lumo
        perfil = "Perfil Lumo"
        salario = random.randint(2600, 3100)
        
    elif pontos_total >= 8:  # 4 ou 5 respostas com valor 2 = Quase Lumo  
        perfil = "Quase Lumo"
        salario = random.randint(1850, 2500)
        
    else:  # Menos de 8 pontos = Fora do padrão Lumo
        perfil = "Fora do padrão Lumo"
        salario = random.randint(1700, 1800)
    
    return perfil, salario, pontos_total