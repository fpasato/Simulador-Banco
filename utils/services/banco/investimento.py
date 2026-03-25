from datetime import datetime, timedelta
import random
import sqlite3
from utils.validators import get_db
from threading import Lock
import math 

notificacoes_pendentes = {}
notificacoes_lock = Lock()

import time

def carregar_carteira(conta_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row

    agora = int(time.time() * 1000)  # ms
    
    temporarios = conn.execute("""
        SELECT 
            it.id as id,
            it.investimento_id as investimento_id,   -- <-- adicione esta linha
            it.quantidade,
            it.preco_medio,
            i.nome,
            i.valor_cota as preco_atual,
            1 as temporario,
            it.tempo_inicio,
            it.duracao
        FROM investimentos_temporarios it
        JOIN investimentos i ON i.id = it.investimento_id
        WHERE it.conta_id = ?
        AND (it.tempo_inicio + it.duracao) > ?
    """, (conta_id, agora)).fetchall()

    if not temporarios:
        conn.close()
        return {'id_conta': conta_id, 'investimentos': []}

    carteira_lista = []
    for row in temporarios:
        invest = dict(row)

        invest['saldo'] = invest['preco_medio'] * invest['quantidade']
        valor_mercado = invest['quantidade'] * invest['preco_atual']
        invest['lucro_prejuizo'] = valor_mercado - invest['saldo']

        # 🔥 calcula tempo restante já pronto pro frontend
        invest['tempo_restante'] = invest['duracao'] - (agora - invest['tempo_inicio'])

        carteira_lista.append(invest)

    conn.close()
    return {'id_conta': conta_id, 'investimentos': carteira_lista}


def load_investiment(investimento_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    investimento = conn.execute("""
        SELECT id, nome, descricao, valor_cota, risco, ativo
        FROM investimentos
        WHERE id = ? AND ativo = 1
    """, (investimento_id,)).fetchone()
    conn.close()
    if investimento:
        print(f"DEBUG: Investimento encontrado: {dict(investimento)}")
    else:
        print(f"DEBUG: Investimento {investimento_id} não encontrado ou inativo")
    return dict(investimento) if investimento else None

def load_all_investiments():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    investimentos = conn.execute("""
        SELECT id, nome, descricao, valor_cota, risco, ativo, tipo, setor
        FROM investimentos
        WHERE ativo = 1
    """).fetchall()
    conn.close()
    return {'investimentos': [dict(row) for row in investimentos]}


def buy_investment(conta_id, investimento_id, quantidade, tempo):
    conn = get_db()
    conn.row_factory = sqlite3.Row

    conta = conn.execute("SELECT saldo FROM contas WHERE id = ?", (conta_id,)).fetchone()
    if not conta:
        print("DEBUG: Conta não encontrada")
        conn.close()
        return False

    saldo_real = conta['saldo']
    ativo = load_investiment(investimento_id)

    print(f"DEBUG: Conta {conta_id} saldo = {saldo_real}")
    print(f"DEBUG: Investimento {investimento_id} encontrado? {ativo is not None}")

    try:
        quantidade = float(quantidade)
    except (TypeError, ValueError):
        print("DEBUG: Quantidade inválida")
        conn.close()
        return False

    if quantidade < 0.0001:
        print("DEBUG: Quantidade deve ser maior que 0.0001")
        conn.close()
        return False

    if not ativo:
        print("DEBUG: Ativo não encontrado")
        conn.close()
        return False

    valor_total = round(ativo['valor_cota'] * quantidade, 6)
    preco_medio = round(valor_total / quantidade, 6)
    
    if saldo_real < valor_total:
        print(f"DEBUG: Saldo insuficiente: {saldo_real} < {valor_total}")
        conn.close()
        return False

    if tempo:
        tempo_inicio = int(time.time() * 1000)  # ms
        duracao = int(tempo)  
        print(f"DEBUG: buy_investment - tempo = {tempo}, type = {type(tempo)}")
        conn.execute("""
            INSERT INTO investimentos_temporarios 
            (conta_id, investimento_id, quantidade, preco_medio, tempo_inicio, duracao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (conta_id, investimento_id, quantidade, preco_medio, tempo_inicio, duracao))

    conn.execute("UPDATE contas SET saldo = saldo - ? WHERE id = ?", (valor_total, conta_id))
    conn.commit()
    conn.close()
    return True


def history_prices(investimento_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    history = conn.execute("""
        SELECT data, preco
        FROM historico_precos
        WHERE investimento_id = ?
        ORDER BY data ASC
        LIMIT 100
    """, (investimento_id,)).fetchall()
    conn.close()
    return [dict(row) for row in history]

import random
import sqlite3
import threading
from datetime import datetime
from utils.validators import get_db

# Lock para evitar concorrência na atualização de ativos
_atualizar_lock = threading.Lock()


def remover_ativo_para_todos(ativo_id, conn):
    """Remove um ativo da carteira de todos os usuários (temporários e permanentes) sem desativá-lo."""
    # 1. Remove da carteira permanente
    conn.execute("DELETE FROM carteira_investimentos WHERE investimento_id = ?", (ativo_id,))
    # 2. Remove dos investimentos temporários (se existir)
    conn.execute("DELETE FROM investimentos_temporarios WHERE investimento_id = ?", (ativo_id,))
    # NÃO desativar o ativo – comentar ou remover a linha abaixo:
    # conn.execute("UPDATE investimentos SET ativo = 0 WHERE id = ?", (ativo_id,))
    # Opcional: registrar notificações para os usuários afetados
    # (Para simplificar, omitiremos notificações aqui)


def atualizar_ativos():
    with _atualizar_lock:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        try:
            ativos = conn.execute("SELECT id, valor_cota, risco, preco_base FROM investimentos WHERE ativo = 1").fetchall()

            for ativo in ativos:
                valor = ativo["valor_cota"]
                preco_base = ativo["preco_base"]
                risco = ativo["risco"]

                # 1. Volatilidade anualizada (em percentual)
                if risco == "baixo":
                    volatilidade_anual = 0.03   # 3% ao ano
                elif risco == "medio":
                    volatilidade_anual = 0.15   # 15% ao ano
                else:  # alto
                    volatilidade_anual = 0.50   # 50% ao ano (realista para cripto)

                # 2. Conversão para o intervalo (30 segundos)
                intervalo_anos = 30 / (365 * 24 * 3600)  # 30 segundos em anos
                volatilidade_intervalo = volatilidade_anual * (intervalo_anos ** 0.5)

                # Ruído log-normal
                ruido = random.gauss(0, volatilidade_intervalo)

                # 3. Reversão à média com força controlável (ajuste conforme desejar)
                forca_reversao = 0.0015   # força de correção (ajustável)
                reversao = (preco_base - valor) * forca_reversao

                # 4. Variação total (em log)
                variacao_log = ruido + (reversao / valor)   # reversão relativa ao preço atual
                novo_valor = valor * math.exp(variacao_log)

                # 5. Piso dinâmico baseado no preço base (nunca cai abaixo de 20% do base)
                preco_minimo = preco_base * 0.2
                if novo_valor < preco_minimo:
                    novo_valor = preco_minimo

                # 6. Evento extremo (raro) – remove o ativo das carteiras apenas se colapsar abaixo de 10% do base
                if novo_valor < preco_base * 0.1:
                    print(f"Ativo {ativo['id']} colapsou (preço {novo_valor:.2f}) - removendo da carteira")
                    remover_ativo_para_todos(ativo["id"], conn)   # apenas remove das carteiras, não desativa

                # 7. Arredondamento final
                novo_valor = round(novo_valor, 2)

                # Atualiza preço do ativo
                conn.execute("UPDATE investimentos SET valor_cota = ? WHERE id = ?", (novo_valor, ativo["id"]))

                # Insere histórico
                conn.execute("""
                    INSERT INTO historico_precos (investimento_id, preco, data)
                    VALUES (?, ?, ?)
                """, (ativo["id"], novo_valor, datetime.now().isoformat()))

            # Limpa histórico antigo: mantém apenas os últimos 100 registros por ativo
            for ativo in ativos:
                keep_ids = conn.execute("""
                    SELECT id FROM historico_precos
                    WHERE investimento_id = ?
                    ORDER BY data DESC
                    LIMIT 100
                """, (ativo["id"],)).fetchall()
                keep_ids = [row[0] for row in keep_ids]
                if keep_ids:
                    placeholders = ','.join('?' for _ in keep_ids)
                    conn.execute(f"""
                        DELETE FROM historico_precos
                        WHERE investimento_id = ? AND id NOT IN ({placeholders})
                    """, (ativo["id"], *keep_ids))

            # Atualiza timestamp da última atualização (se a coluna existir)
            try:
                conn.execute("UPDATE investimentos SET ultimo_update = ?", (datetime.now().isoformat(),))
            except sqlite3.OperationalError:
                pass  # coluna não existe, ignora

            conn.commit()
        except Exception as e:
            conn.rollback()
        finally:
            conn.close()
        print(f"[{datetime.now()}] Ativos atualizados e histórico limpo")

def busca_investimento_temporarios():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    agora = int(time.time() * 1000)
    print(f"DEBUG: Busca expirados - agora={agora}")
    expirados = conn.execute("""
        SELECT * FROM investimentos_temporarios
        WHERE (tempo_inicio + duracao) <= ?
    """, (agora,)).fetchall()
    print(f"DEBUG: Encontrados {len(expirados)} expirados")
    conn.close()
    return [dict(row) for row in expirados]


def processar_investimentos_expirados():
    expirados = busca_investimento_temporarios()
    conn = get_db()
    agora = int(time.time() * 1000) 
    for inv in expirados:
        print(f"DEBUG: Processando expirado id={inv['id']}, conta={inv['conta_id']}, investimento={inv['investimento_id']}, tempo_inicio={inv['tempo_inicio']}, duracao={inv['duracao']}, expira_em={inv['tempo_inicio']+inv['duracao']}, agora={agora}")
        conta_id = inv["conta_id"]
        investimento_id = inv["investimento_id"]
        quantidade = inv["quantidade"]
        preco_medio = inv["preco_medio"]
        temp_id = inv["id"]
        ativo = conn.execute("SELECT nome, valor_cota FROM investimentos WHERE id = ?", (investimento_id,)).fetchone()
        if not ativo:
            continue
        preco_atual = ativo["valor_cota"]
        valor_venda = quantidade * preco_atual
        custo_total = quantidade * preco_medio
        lucro = valor_venda - custo_total
        # Atualiza o saldo do usuário
        conn.execute("UPDATE contas SET saldo = saldo + ? WHERE id = ?", (valor_venda, conta_id))
        conn.execute("DELETE FROM investimentos_temporarios WHERE id = ?", (temp_id,))
        notificacao = {
            'tipo': 'venda_automatica',
            'nome': ativo['nome'],
            'quantidade': quantidade,
            'lucro': lucro,
            'preco_venda': preco_atual,
            'preco_medio': preco_medio
        }
        with notificacoes_lock:
            notificacoes_pendentes.setdefault(conta_id, []).append(notificacao)
        conn.commit()
    conn.close()
    
    
    
def limpar_historico_antigo(conn, limite_por_ativo=100):
    for ativo in ativos:
        # pega os IDs dos registros a manter
        keep_ids = conn.execute("""
            SELECT id FROM historico_precos
            WHERE investimento_id = ?
            ORDER BY data DESC
            LIMIT ?
        """, (ativo["id"], limite_por_ativo)).fetchall()
        keep_ids = [row[0] for row in keep_ids]
        if keep_ids:
            # deleta os que não estão na lista
            placeholders = ','.join('?' for _ in keep_ids)
            conn.execute(f"""
                DELETE FROM historico_precos
                WHERE investimento_id = ? AND id NOT IN ({placeholders})
            """, (ativo["id"], *keep_ids))