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

def gerar_investimentos():
    conn = get_db()
    cursor = conn.cursor()

    investimentos = [
        # Tecnologia
        ("TecBrasil", "Empresa de software fundada em 2010, especializada em soluções corporativas para pequenas e médias empresas brasileiras, incluindo ERP e sistemas de gestão de vendas.", 120.0, "alto"),
        ("Inteli AI", "Startup de inteligência artificial focada em automação industrial e análise preditiva de dados. Atua com clientes de diversos setores, de manufatura a serviços financeiros.", 200.0, "alto"),
        ("CloudSul", "Plataforma de computação em nuvem com serviços de armazenamento, backup e análise de dados para empresas do Sul e Sudeste, com contratos B2B robustos.", 140.0, "medio"),
        ("CyberProtec", "Empresa de segurança digital e consultoria em proteção de dados, com clientes em setores bancário e governamental, destacando-se pelo monitoramento 24/7.", 110.0, "medio"),

        # Financeiro
        ("BancoSeguro", "Banco tradicional com mais de 50 anos de atuação no Brasil, conhecido por baixo risco, atendimento presencial e digital, e carteira diversificada de clientes corporativos e pessoas físicas.", 80.0, "baixo"),
        ("PagBrasil", "Plataforma de pagamentos digitais que integra lojas online e físicas, oferecendo soluções de pagamento instantâneo, carteiras digitais e análise de transações.", 130.0, "medio"),
        ("CréditoFácil", "Fintech de crédito pessoal e empresarial com análise rápida de risco e oferta de linhas de financiamento inovadoras, focada no público emergente brasileiro.", 95.0, "medio"),

        # Energia
        ("SolarBrasil", "Empresa especializada em energia solar para residências e indústrias, com projetos personalizados e financiamentos próprios, buscando redução da pegada de carbono.", 95.0, "medio"),
        ("Ventos do Sul", "Produtora de energia eólica com parques instalados no Nordeste e Sul do Brasil, fornecendo energia limpa para grandes consumidores e distribuidores regionais.", 105.0, "medio"),
        ("PetroSul", "Companhia de exploração de petróleo e gás em campos nacionais, com alto potencial de lucro, porém sujeita a volatilidade de preços e regulação governamental.", 150.0, "alto"),

        # Imobiliário
        ("ImobBrasil", "Fundo imobiliário focado em imóveis residenciais, com contratos de aluguel de longo prazo, baixa vacância e valorização gradual em regiões urbanas em expansão.", 70.0, "baixo"),
        ("VivaUrbano", "Construtora de empreendimentos residenciais modernos, especializada em apartamentos compactos para jovens profissionais em capitais brasileiras.", 85.0, "medio"),
        ("MegaConstrutora", "Construtora de grande porte que desenvolve shopping centers, edifícios corporativos e condomínios residenciais, atuando em diversas capitais brasileiras.", 100.0, "medio"),

        # Agro
        ("AgroBrasil", "Grupo agroindustrial focado em produção de grãos, gestão de fazendas inteligentes e exportação de commodities para mercados da América Latina e Europa.", 60.0, "medio"),
        ("GrãoForte", "Fazendas especializadas em soja e milho, com técnicas modernas de irrigação e baixo risco operacional, voltadas ao mercado interno e exportação.", 75.0, "baixo"),
        ("AgroTech", "Empresa de tecnologia agrícola que fornece drones, sensores de solo e software de monitoramento para aumento da produtividade no campo brasileiro.", 90.0, "medio"),

        # Saúde
        ("Saúde+BR", "Rede hospitalar nacional com foco em atendimento humanizado, infraestrutura moderna e programas de prevenção e bem-estar para a população local.", 110.0, "baixo"),
        ("BioBrasil Labs", "Laboratório de pesquisa farmacêutica que desenvolve vacinas e medicamentos inovadores, com parcerias internacionais e risco elevado de P&D.", 180.0, "alto"),
        ("EquipMed", "Empresa de equipamentos médicos de alta tecnologia para hospitais e clínicas privadas, com contratos de manutenção e atualização constantes.", 95.0, "medio"),

        # Logística
        ("LogBrasil", "Transportadora e empresa de logística que atende grandes centros urbanos, especializada em roteirização inteligente e redução de custos operacionais.", 85.0, "medio"),
        ("EntregaRápida", "Serviço de entrega expressa para e-commerce, com frota própria e tecnologia de rastreamento em tempo real, voltada para clientes de médio e grande porte.", 120.0, "alto"),
        ("CargoBrasil", "Empresa de transporte nacional e internacional, especializada em cargas pesadas e contratos logísticos com grandes indústrias e distribuidores.", 130.0, "medio"),

        # Sustentabilidade
        ("PlanetaVerde", "Consultoria ambiental que auxilia empresas na implementação de projetos sustentáveis e certificações de impacto ambiental no Brasil.", 90.0, "medio"),
        ("EcoBrasil", "Companhia de energia renovável, desenvolvendo projetos solares, eólicos e hidrelétricos com foco em redução de emissão de CO2.", 100.0, "medio"),
        ("ReciclaTech", "Empresa de tecnologia aplicada à reciclagem, gestão de resíduos industriais e soluções de economia circular para indústrias brasileiras.", 80.0, "baixo"),

        # Digital / Crypto
        ("CriptoBrasil", "Exchange de ativos digitais com foco em traders brasileiros, oferecendo alta volatilidade e liquidez, voltada para investimentos de curto prazo.", 150.0, "alto"),
        ("BlockBrasil", "Plataforma de infraestrutura blockchain que oferece contratos inteligentes e soluções de tokenização para empresas nacionais.", 170.0, "alto"),
        ("TokenBR", "Plataforma de emissão e negociação de tokens digitais e NFTs para artistas e empresas brasileiras, com foco em inovação tecnológica.", 140.0, "alto"),

        # Diversificados
        ("MixGlobal BR", "Fundo diversificado com ações, renda fixa e commodities, oferecendo exposição a diferentes setores nacionais e internacionais.", 110.0, "baixo"),
        ("FundoMulti BR", "Fundo multimercado com gestão ativa e diversificação em renda fixa, ações e derivativos, voltado para investidores com perfil moderado.", 125.0, "medio"),
        ("CapitalBrasil", "Gestora de investimentos com portfólio diversificado e estratégia nacional, buscando retorno consistente com controle de risco.", 135.0, "medio"),
        
        
        ("WilliamWonka", "A maior produtora de bolos de cenoura com cobertura de chocolate da América Latina.", 55.0, "medio"),
        ("EztePhãnêa Estrim","O serviço de streaming pirata da EzthePhanea que promete todos os filmes e séries do mundo. ", 45.0, "alto"),
        ("Danilo Bones", "Marca de bonés ultra exclusivos criada por Danilo: cada boné vem com proteção contra raios cósmicos, garante uma aura de mistério que confunde até o cachorro da vizinhança.",26.0, "medio"), 
        ("Lucas Bus Paraty","Empresa de ônibus premium em Paraty, fundada por Lucas: oferece passeios turísticos com guias que contam histórias inventadas, Wi-Fi que funciona só quando quer, e assentos que se ajustam ao humor do passageiro. Um clássico do transporte criativo brasileiro.",83.0, "medio"),

    ]

    inseridos = 0

    for nome, descricao, valor, risco in investimentos:
        cursor.execute("SELECT id FROM investimentos WHERE nome = ?", (nome,))
        if cursor.fetchone():
            continue

        cursor.execute("""
            INSERT INTO investimentos (nome, descricao, valor_cota, risco, preco_base)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, descricao, valor, risco, valor))
        inseridos += 1

    conn.commit()
    conn.close()

    print(f"[{datetime.now()}] {inseridos} investimentos inseridos com sucesso!")

if __name__ == "__main__":
    limpar_tabela()
    gerar_investimentos()   