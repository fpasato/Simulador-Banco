import sqlite3
from datetime import datetime

DB_PATH = "database.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def limpar_tabela():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investimentos")
    conn.commit()
    conn.close()

def adicionar_coluna_se_nao_existir(cursor, tabela, coluna, tipo):
    """Adiciona uma coluna à tabela se ela não existir."""
    try:
        cursor.execute(f"SELECT {coluna} FROM {tabela} LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        print(f"Coluna '{coluna}' adicionada à tabela {tabela}.")

def gerar_investimentos():
    conn = get_db()
    cursor = conn.cursor()

    # Garantir que as colunas necessárias existam
    adicionar_coluna_se_nao_existir(cursor, "investimentos", "tipo", "TEXT DEFAULT 'fundo'")
    adicionar_coluna_se_nao_existir(cursor, "investimentos", "setor", "TEXT DEFAULT 'outros'")
    # Caso a coluna 'categoria' ainda não exista (para compatibilidade)
    adicionar_coluna_se_nao_existir(cursor, "investimentos", "categoria", "TEXT DEFAULT 'outros'")

    investimentos = [
        # --- Fundos de Setor (tipo = fundo) ---
        ("Fundo Tech Brasil", "Fundo de investimento focado em empresas de tecnologia brasileiras.", 132.75, "medio", "fundo", "tecnologia"),
        ("Fundo Saúde Sustentável", "Fundo com foco em hospitais e biotecnologia.", 108.40, "baixo", "fundo", "saude"),
        ("Fundo Energia Verde", "Investimentos em energia renovável e infraestrutura.", 97.15, "medio", "fundo", "energia"),
        ("Fundo Agro Inteligente", "Fundo voltado ao agronegócio moderno.", 82.60, "baixo", "fundo", "agro"),
        ("Fundo Imobiliário Logístico", "FII focado em galpões logísticos.", 74.30, "baixo", "fundo", "imobiliario"),
        ("Fundo Financeiro Premium", "Fundo multimercado com gestão ativa.", 145.90, "medio", "fundo", "financeiro"),
        ("Fundo Sustentabilidade Global", "Foco em economia circular e ESG.", 111.25, "medio", "fundo", "sustentabilidade"),

        # --- Ações (tipo = acao) ---
        ("TechNova S.A.", "Empresa de software industrial.", 210.80, "alto", "acao", "tecnologia"),
        ("BioGenética", "Pesquisa genética avançada.", 265.30, "alto", "acao", "saude"),
        ("Energia Sul", "Geradora de energia renovável.", 68.90, "baixo", "acao", "energia"),
        ("Agroforte", "Tecnologia agrícola e fertilizantes.", 102.45, "medio", "acao", "agro"),
        ("Construtora Viva", "Incorporadora imobiliária.", 59.70, "medio", "acao", "imobiliario"),
        ("Banco Digital BR", "Banco digital em expansão.", 175.20, "alto", "acao", "financeiro"),
        ("EcoRecicla", "Reciclagem industrial.", 92.10, "medio", "acao", "sustentabilidade"),

        # --- Cripto (tipo = cripto) ---
        ("Bitcoin Trust", "Exposição ao Bitcoin.", 325000.00, "alto", "cripto", "digital"),
        ("Ethereum Smart", "Participação em staking de Ethereum.", 18200.50, "alto", "cripto", "digital"),
        ("Blockchain Brasil", "Carteira diversificada cripto.", 8750.75, "alto", "cripto", "digital"),

        # --- Renda Fixa (tipo = renda_fixa) ---
        ("Tesouro IPCA+ 2035", "Título público atrelado à inflação.", 1025.80, "baixo", "renda_fixa", "financeiro"),
        ("CDB Banco Digital", "CDB com liquidez diária.", 1000.00, "baixo", "renda_fixa", "financeiro"),
        ("Debênture Energia", "Debênture incentivada.", 1120.45, "medio", "renda_fixa", "energia"),

        # --- FIIs / Cotas (tipo = cota) ---
        ("FII Galpões Log", "Galpões logísticos.", 118.35, "baixo", "cota", "imobiliario"),
        ("FII Lajes Corp", "Lajes corporativas.", 96.20, "medio", "cota", "imobiliario"),
        ("FII Shoppings", "Participação em shoppings.", 88.90, "medio", "cota", "imobiliario"),
    ]

    inseridos = 0

    for nome, descricao, valor, risco, tipo, setor in investimentos:
        try:
            cursor.execute("SELECT id FROM investimentos WHERE nome = ?", (nome,))
            if cursor.fetchone():
                print(f"⚠️ Ativo já existe: {nome}")
                continue

            cursor.execute("""
                INSERT INTO investimentos 
                (nome, descricao, valor_cota, risco, preco_base, tipo, setor, categoria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, descricao, valor, risco, valor, tipo, setor, setor))
            inseridos += 1
        except Exception as e:
            print(f"❌ Erro ao inserir {nome}: {e}")

    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] {inseridos} investimentos inseridos com sucesso!")

if __name__ == "__main__":
    limpar_tabela()
    gerar_investimentos()