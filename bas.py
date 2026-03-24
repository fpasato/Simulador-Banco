import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ativa foreign key
conn.execute("PRAGMA foreign_keys = ON")

# 👤 USUARIOS
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# 💰 CONTAS
cursor.execute("""
CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    numero_conta TEXT NOT NULL UNIQUE,
    saldo REAL DEFAULT 0,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
""")

# 📄 TRANSACOES DA CONTA (PIX, depósito, débito)
cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes_conta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conta_id INTEGER NOT NULL,
    valor REAL NOT NULL,
    tipo TEXT NOT NULL, -- deposito, pix, debito
    descricao TEXT,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (conta_id) REFERENCES contas(id)
)
""")

# 💳 CARTOES
cursor.execute("""
CREATE TABLE IF NOT EXISTS cartoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conta_id INTEGER NOT NULL,
    numero_cartao TEXT NOT NULL UNIQUE,
    validade TEXT,
    cvv TEXT,
    limite REAL,
    tipo TEXT, -- credito ou debito

    FOREIGN KEY (conta_id) REFERENCES contas(id)
)
""")

# 🔒 evita duplicar cartão por tipo (1 crédito + 1 débito)
cursor.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_cartao_unico
ON cartoes(conta_id, tipo)
""")


# 💳 TRANSACOES DO CARTAO (CRÉDITO)
cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes_cartao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cartao_id INTEGER NOT NULL,
    valor REAL NOT NULL,
    descricao TEXT,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    pago INTEGER DEFAULT 0, -- 0 = aberto, 1 = pago

    FOREIGN KEY (cartao_id) REFERENCES cartoes(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacoes_pix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    transacao_id INTEGER NOT NULL, -- ligação com a tabela transacoes
    
    chave_origem TEXT,
    chave_destino TEXT,
    
    tipo_chave TEXT, -- cpf, email, telefone, aleatoria
    
    descricao TEXT, -- mensagem opcional do pix
    
    FOREIGN KEY (transacao_id) REFERENCES transacoes_conta(id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chaves_pix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    conta_id INTEGER NOT NULL,
    
    tipo TEXT NOT NULL, -- cpf, email, telefone, aleatoria
    chave TEXT NOT NULL UNIQUE,
    
    criada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conta_id) REFERENCES contas(id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS investimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    nome TEXT NOT NULL,
    descricao TEXT,

    valor_cota REAL NOT NULL,
    
    risco TEXT DEFAULT 'medio',
    
    ativo INTEGER DEFAULT 1,
    
    ultimo_update DATETIME DEFAULT CURRENT_TIMESTAMP,

    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP

    preco_base REAL,
    
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS historico_precos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    investimento_id INTEGER NOT NULL,
    preco REAL NOT NULL,
    
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (investimento_id) REFERENCES investimentos(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS faturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    conta_id INTEGER NOT NULL,
    
    tipo TEXT NOT NULL, -- luz, agua, internet, aluguel, etc
    
    valor REAL NOT NULL,
    
    status TEXT DEFAULT 'pendente', -- pendente, pago, vencido
    
    data_vencimento DATETIME NOT NULL,
    
    juros REAL DEFAULT 0,
    
    descricao TEXT,
    
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conta_id) REFERENCES contas(id)
)
""")


# Tabela carteira_investimentos
cursor.execute("""
CREATE TABLE IF NOT EXISTS carteira_investimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conta_id INTEGER NOT NULL,
    investimento_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_medio REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conta_id) REFERENCES contas(id),
    FOREIGN KEY (investimento_id) REFERENCES investimentos(id),
    UNIQUE(conta_id, investimento_id)
)
""")

# Tabela investimentos_temporarios
cursor.execute("""
CREATE TABLE IF NOT EXISTS investimentos_temporarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conta_id INTEGER NOT NULL,
    investimento_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_medio REAL NOT NULL,
    tempo_inicio INTEGER NOT NULL,
    duracao INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conta_id) REFERENCES contas(id),
    FOREIGN KEY (investimento_id) REFERENCES investimentos(id)
)
""")

# Tabela historico_precos
cursor.execute("""
CREATE TABLE IF NOT EXISTS historico_precos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investimento_id INTEGER NOT NULL,
    preco REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (investimento_id) REFERENCES investimentos(id)
)
""")

conn.commit()
conn.close()

print("Banco criado com sucesso 🚀")