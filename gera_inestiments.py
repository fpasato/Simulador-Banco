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

    investimentos = [
        # --- AÇÕES DE TECNOLOGIA (4) ---
        ("TOTVS S.A. (TOTS3)", "Maior desenvolvedora de software empresarial da América Latina, líder em ERP e soluções de gestão.", 28.75, "medio", "acao", "tecnologia"),
        ("B3 S.A. (B3SA3)", "Principal bolsa de valores do Brasil, com forte atuação em tecnologia financeira e infraestrutura de mercado.", 11.90, "baixo", "acao", "tecnologia"),
        ("Locaweb (LWSA3)", "Plataforma de serviços digitais para empresas, incluindo hospedagem, e-commerce e soluções de marketing.", 4.85, "alto", "acao", "tecnologia"),
        ("Intelbras (INTB3)", "Fabricante de equipamentos de telecomunicações, segurança eletrônica e redes, com forte presença no mercado corporativo.", 22.60, "medio", "acao", "tecnologia"),

        # --- AÇÕES DE SAÚDE (4) ---
        ("Rede D'Or São Luiz (RDOR3)", "Maior rede de hospitais privados do Brasil, com atuação em medicina de alta complexidade e planos de saúde.", 27.45, "baixo", "acao", "saude"),
        ("Hapvida (HAPV3)", "Segunda maior operadora de planos de saúde do país, com modelo verticalizado e forte capilaridade regional.", 3.92, "medio", "acao", "saude"),
        ("Fleury (FLRY3)", "Líder em medicina diagnóstica, com ampla rede de laboratórios e serviços de imagem, referência em qualidade.", 14.20, "baixo", "acao", "saude"),
        ("Hypera Pharma (HYPE3)", "Gigante farmacêutica com portfólio diversificado de medicamentos, incluindo genéricos, prescritos e de venda livre.", 28.15, "medio", "acao", "saude"),

        # --- FUNDOS DE TECNOLOGIA (4) ---
        ("ETF IT Now (IETF11)", "Fundo de índice que replica o desempenho de empresas de tecnologia brasileiras, seguindo o Índice de Tecnologia da Informação (ITAG).", 8.65, "alto", "fundo", "tecnologia"),
        ("Fundo de Ações Tecnologia XP (XPTEC11)", "Fundo ativo gerido pela XP, focado em empresas de software, hardware e inovação digital listadas na B3.", 12.40, "medio", "fundo", "tecnologia"),
        ("Trend Tech ETF (TECK11)", "ETF da Trend que investe em empresas globais de tecnologia, com exposição a big techs e semicondutores.", 9.20, "alto", "fundo", "tecnologia"),
        ("Kinea Tecnologia FIA", "Fundo de ações com gestão ativa da Kinea, buscando oportunidades em empresas disruptivas de tecnologia no Brasil.", 14.90, "alto", "fundo", "tecnologia"),

        # --- FUNDOS DE SAÚDE (4) ---
        ("ETF Saúde (SAUD11)", "ETF que replica o Índice de Saúde (ISAU), composto por empresas dos setores hospitalar, diagnóstico e farmacêutico.", 6.70, "medio", "fundo", "saude"),
        ("Fundo de Ações Saúde Itaú (ITSAU11)", "Fundo de índice gerido pelo Itaú, focado em empresas do setor de saúde e bem-estar.", 5.90, "medio", "fundo", "saude"),
        ("SulAmérica Saúde FIA", "Fundo de ações da SulAmérica com foco em empresas de planos de saúde, hospitais e serviços médicos.", 8.25, "medio", "fundo", "saude"),
        ("Bradesco Pharma FIC FIA", "Fundo que investe predominantemente em empresas farmacêuticas e de biotecnologia listadas na B3.", 7.85, "alto", "fundo", "saude"),

        # --- CRIPTO (10 ativos com valores aproximados em BRL) ---
        ("Bitcoin (BTC)", "A primeira e mais conhecida criptomoeda do mundo, usada como reserva de valor digital e meio de transferência global, com ampla liquidez e aceitação.", 369461.60, "alto", "cripto", "digital"),
        ("Ethereum (ETH)", "Plataforma de contratos inteligentes líder no mercado, base para DeFi e NFTs, com grande ecossistema de aplicações descentralizadas.", 11134.00, "alto", "cripto", "digital"),
        ("BNB (Binance Coin)", "Token nativo da Binance, utilizado para taxas reduzidas na exchange e participações no ecossistema Binance Smart Chain.", 4731.47, "alto", "cripto", "digital"),
        ("Solana (SOL)", "Blockchain de alta performance focada em velocidade e baixo custo de transações, muito popular em aplicações DeFi e Web3.", 469.10, "alto", "cripto", "digital"),
        ("XRP (XRP)", "Criptomoeda otimizada para pagamentos rápidos e de baixo custo, frequentemente usada para liquidez em remessas internacionais.", 10.27, "alto", "cripto", "digital"),
        ("Cardano (ADA)", "Blockchain orientada à segurança e sustentabilidade, com foco em governança on‑chain e contratos inteligentes escaláveis.", 1.95, "medio", "cripto", "digital"),
        ("Dogecoin (DOGE)", "Criptomoeda meme originada como piada, mas com forte comunidade e presença em pagamentos ponto‑a‑ponto.", 0.68, "alto", "cripto", "digital"),
        ("Polygon (MATIC)", "Solução de escalabilidade para Ethereum, oferecendo transações rápidas e com baixo custo em sidechains compatíveis.", 0.58, "medio", "cripto", "digital"),
        ("Avalanche (AVAX)", "Plataforma de contratos inteligentes de alta velocidade e finalização rápida, focada em interoperabilidade entre blockchains.", 68.97, "alto", "cripto", "digital"),
        ("Litecoin (LTC)", "Uma das primeiras alternativas ao Bitcoin, projetada para transações rápidas com taxas mais baixas, frequentemente usada como moeda de pagamento.", 433.31, "alto", "cripto", "digital"),

            # --- RENDA FIXA - FINANCEIRO (4) ---
        ("Tesouro IPCA+ 2035 (NTN-B)", "Título público federal atrelado ao IPCA + juros reais, com vencimento em 2035; ideal para proteção contra inflação.", 1042.50, "baixo", "renda_fixa", "financeiro"),
        ("CDB Itaú 110% CDI", "Certificado de Depósito Bancário com rendimento de 110% do CDI e liquidez diária, emitido pelo Itaú Unibanco.", 1000.00, "baixo", "renda_fixa", "financeiro"),
        ("LCI Banco do Brasil 95% CDI", "Letra de Crédito Imobiliário isenta de IR, com rendimento de 95% do CDI e vencimento em 2 anos.", 1023.75, "baixo", "renda_fixa", "financeiro"),
        ("Debênture Incentivada Bradesco", "Debênture emitida pelo Bradesco com incentivo fiscal, pagando IPCA + 5,5% ao ano, vencimento em 2030.", 1120.00, "medio", "renda_fixa", "financeiro"),

        # --- RENDA FIXA - ENERGIA (4) ---
        ("Debênture Incentivada Neoenergia", "Debênture incentivada do setor elétrico, com remuneração IPCA + 6,0% ao ano e prazo de 10 anos.", 1150.00, "medio", "renda_fixa", "energia"),
        ("CDB Verde Banco BV", "CDB que direciona recursos para projetos de energia renovável, rendendo 105% do CDI com liquidez diária.", 1000.00, "baixo", "renda_fixa", "energia"),
        ("LCI Solar Santander", "LCI destinada ao financiamento de usinas solares, com isenção de IR e rendimento de 98% do CDI.", 980.50, "baixo", "renda_fixa", "energia"),
        ("Tesouro Verde 2030 (NTN-B)", "Título público com foco em sustentabilidade, atrelado ao IPCA + 5,8% ao ano, vencimento em 2030.", 1045.00, "baixo", "renda_fixa", "energia"),

        # --- COTAS / FIIs - IMOBILIÁRIO (4) ---
        ("HGBS11 (Hedge Brasil Shopping)", "FII focado em shoppings centers de alta qualidade, com portfólio diversificado e boa distribuição de dividendos.", 178.40, "medio", "cota", "imobiliario"),
        ("KNRI11 (Kinea Renda Imobiliária)", "Maior FII de tijolo do Brasil, com carteira de lajes corporativas, galpões logísticos e shoppings.", 126.50, "baixo", "cota", "imobiliario"),
        ("VISC11 (Vinci Shopping)", "FII especializado em shoppings, com ativos de alto padrão em regiões nobres, gestão ativa da Vinci.", 110.20, "medio", "cota", "imobiliario"),
        ("BRCR11 (BTG Pactual Corporate)", "FII de lajes corporativas com locações para empresas de grande porte, alta vacância controlada e dividendos consistentes.", 95.80, "baixo", "cota", "imobiliario"),

        # --- COTAS / FIIs - AGRO (4) ---
        ("AAZQ11 (Alianza Trust)", "FII de recebíveis do agronegócio (Fiagro) focado em CRAs de produtores e empresas do setor.", 98.90, "medio", "cota", "agro"),
        ("VGIR11 (Valora Agro)", "Fiagro que investe em direitos creditórios do agronegócio, com diversificação em operações de soja, milho e pecuária.", 101.40, "medio", "cota", "agro"),
        ("RURA11 (Rura Agro)", "Fundo de investimento em direitos creditórios do agronegócio, com gestão ativa e foco em crédito rural.", 99.30, "medio", "cota", "agro"),
        ("SNAG11 (Suno Agro)", "Fiagro que combina CRAs e participação em terrenos agrícolas, buscando proteção cambial e rendimentos reais.", 96.70, "baixo", "cota", "agro"),
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