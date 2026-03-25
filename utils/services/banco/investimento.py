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

import math
import random
import sqlite3
from datetime import datetime, date
from threading import Lock
from utils.validators import get_db

_notificacoes_pendentes = {}
_notificacoes_lock = Lock()
_atualizar_lock = Lock()

def garantir_tabela_variacoes(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS variacoes_diarias (
            ativo_id INTEGER PRIMARY KEY,
            data TEXT NOT NULL,
            variacao REAL NOT NULL
        )
    ''')
    conn.commit()

def remover_ativo_para_todos(ativo_id, conn):
    """Remove o ativo das carteiras e desativa-o permanentemente."""
    conn.execute("DELETE FROM carteira_investimentos WHERE investimento_id = ?", (ativo_id,))
    conn.execute("DELETE FROM investimentos_temporarios WHERE investimento_id = ?", (ativo_id,))
    conn.execute("UPDATE investimentos SET ativo = 0 WHERE id = ?", (ativo_id,))  # <- agora desativa

def atualizar_ativos():
    with _atualizar_lock:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        try:
            garantir_tabela_variacoes(conn)

            # Carrega todos os ativos ativos
            ativos = conn.execute("""
                SELECT id, nome, valor_cota, risco, preco_base, tipo, setor
                FROM investimentos
                WHERE ativo = 1
            """).fetchall()

            hoje = date.today().isoformat()
            agora = datetime.now()

            drift_por_tipo = {
                'acao': 0.02,
                'fundo': 0.01,
                'cripto': 0.15,        # aumentado
                'renda_fixa': 0.005,
                'cota': 0.01
            }

            reversao_por_tipo = {
                'acao': 0.01,
                'fundo': 0.008,
                'cripto': 0.001,       # reduzido drasticamente
                'renda_fixa': 0.05,
                'cota': 0.02
            }

            volatilidade_base = {
                'baixo': 0.03,
                'medio': 0.15,
                'alto': 0.80           # aumentado
            }

            volatilidade_mult = {
                'acao': 1.0,
                'fundo': 0.9,
                'cripto': 2.2,         # aumentado
                'renda_fixa': 0.6,
                'cota': 1.0
            }

            max_passo = {
                'acao': 0.10,
                'fundo': 0.08,
                'cripto': 0.12,        # aumentado
                'renda_fixa': 0.03,
                'cota': 0.07
            }

            limite_diario = {
                'acao': 0.15,
                'fundo': 0.12,
                'cripto': 0.35,        # aumentado
                'renda_fixa': 0.08,
                'cota': 0.15
            }
        

            intervalo_anos = 30 / (365 * 24 * 3600)   # 30 segundos em anos

            # Carrega variação acumulada do dia
            variacao_diaria = {}
            rows = conn.execute("SELECT ativo_id, variacao FROM variacoes_diarias WHERE data = ?", (hoje,)).fetchall()
            for row in rows:
                variacao_diaria[row['ativo_id']] = row['variacao']

            updates = []          # (novo_valor, id)
            historico = []        # (investimento_id, preco, data)
            variacoes_para_salvar = []   # (ativo_id, data, variacao_nova)
            ativos_removidos = []

            for ativo in ativos:
                ativo_id = ativo['id']
                nome = ativo['nome']
                valor = ativo['valor_cota']
                preco_base = ativo['preco_base']
                risco = ativo['risco']
                tipo = ativo['tipo']

                try:
                    # Volatilidade ajustada
                    volatilidade_anual = volatilidade_base[risco] * volatilidade_mult.get(tipo, 1.0)
                    volatilidade_intervalo = volatilidade_anual * math.sqrt(intervalo_anos)

                    ruido = random.gauss(0, volatilidade_intervalo)
                    if tipo == 'cripto':
                        if random.random() < 0.01:  # 1% de chance
                            choque = random.uniform(-0.25, 0.25)  # -25% a +25%
                            ruido += choque

                    # Drift
                    drift_anual = drift_por_tipo.get(tipo, 0.01)
                    drift_intervalo = drift_anual * intervalo_anos

                    # Reversão à média
                    forca_reversao_anual = reversao_por_tipo.get(tipo, 0.005)
                    reversao = (preco_base - valor) * forca_reversao_anual * intervalo_anos
                    # Cap maior para cripto (opcional)
                    if tipo == 'cripto':
                        reversao_rel = max(-0.12, min(0.12, reversao / valor))
                    else:
                        reversao_rel = max(-0.05, min(0.05, reversao / valor))

                    variacao_log = drift_intervalo + ruido + reversao_rel
                    novo_valor = valor * math.exp(variacao_log)

                    # Limite por passo
                    max_passo_tipo = max_passo.get(tipo, 0.10)
                    if novo_valor > valor * (1 + max_passo_tipo):
                        novo_valor = valor * (1 + max_passo_tipo)
                    elif novo_valor < valor * (1 - max_passo_tipo):
                        novo_valor = valor * (1 - max_passo_tipo)

                    # Limite diário (corrigido)
                    limite = limite_diario.get(tipo, 0.15)
                    variacao_hoje = (novo_valor / valor) - 1
                    acumulado = variacao_diaria.get(ativo_id, 0.0)
                    if abs(acumulado + variacao_hoje) > limite:
                        if (acumulado + variacao_hoje) > 0:
                            ajuste = limite - acumulado
                        else:
                            ajuste = -limite - acumulado
                        novo_valor = valor * (1 + ajuste)
                        variacao_hoje = ajuste
                    novo_acumulado = acumulado + variacao_hoje
                    variacoes_para_salvar.append((ativo_id, hoje, novo_acumulado))

                    # Piso mínimo
                    preco_minimo = preco_base * 0.2
                    if novo_valor < preco_minimo:
                        novo_valor = preco_minimo

                    # Colapso
                    if novo_valor < preco_base * 0.1:
                        print(f"[COLAPSO] Ativo {ativo_id} ({nome}) caiu para {novo_valor:.2f}. Removendo e desativando.")
                        remover_ativo_para_todos(ativo_id, conn)
                        ativos_removidos.append(ativo_id)
                        continue

                    # Arredondamento
                    if tipo == 'cripto':
                        novo_valor = round(novo_valor, 6)
                    else:
                        novo_valor = round(novo_valor, 4)

                    updates.append((novo_valor, ativo_id))
                    historico.append((ativo_id, novo_valor, agora.isoformat(timespec='microseconds')))

                except Exception as e:
                    print(f"[ERRO] Processando ativo {ativo_id} ({nome}): {e}")
                    continue

            # Executa em lote
            if updates:
                conn.executemany("UPDATE investimentos SET valor_cota = ? WHERE id = ?", updates)
            if historico:
                conn.executemany(
                    "INSERT INTO historico_precos (investimento_id, preco, data) VALUES (?, ?, ?)",
                    historico
                )
            if variacoes_para_salvar:
                conn.executemany(
                    "INSERT OR REPLACE INTO variacoes_diarias (ativo_id, data, variacao) VALUES (?, ?, ?)",
                    variacoes_para_salvar
                )
            # Remove variações muito antigas (opcional)
            conn.execute("DELETE FROM variacoes_diarias WHERE data < date('now', '-30 days')")

            # Limpeza do histórico (mantém últimos 100 registros)
            for ativo in ativos:
                if ativo['id'] in ativos_removidos:
                    continue
                keep_ids = conn.execute("""
                    SELECT id FROM historico_precos
                    WHERE investimento_id = ?
                    ORDER BY data DESC
                    LIMIT 100
                """, (ativo['id'],)).fetchall()
                keep_ids = [row[0] for row in keep_ids]
                if keep_ids:
                    placeholders = ','.join('?' for _ in keep_ids)
                    conn.execute(f"""
                        DELETE FROM historico_precos
                        WHERE investimento_id = ? AND id NOT IN ({placeholders})
                    """, (ativo['id'], *keep_ids))

            # Atualiza timestamp global
            try:
                conn.execute("UPDATE investimentos SET ultimo_update = ?", (agora.isoformat(),))
            except sqlite3.OperationalError:
                pass

            conn.commit()
            print(f"[{datetime.now().isoformat(timespec='seconds')}] Atualização OK: {len(updates)} ativos, {len(ativos_removidos)} removidos.")

        except sqlite3.Error as e:
            print(f"[ERRO SQLite] {e}")
            conn.rollback()
        except Exception as e:
            print(f"[ERRO inesperado] {e}")
            conn.rollback()
        finally:
            conn.close()

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