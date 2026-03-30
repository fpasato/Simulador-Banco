from utils.validators import get_db
from uuid import uuid4

def register_default_keys(conta_id, cpf, email):
    conn = get_db()
    cursor = conn.cursor()

    # Verifica se o CPF já existe como chave em QUALQUER conta
    cursor.execute("SELECT 1 FROM chaves_pix WHERE chave = ?", (cpf,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO chaves_pix (conta_id, tipo, chave)
            VALUES (?, 'cpf', ?)
        """, (conta_id, cpf))
        print(f"CPF {cpf} inserido como chave para conta {conta_id}")
    else:
        print(f"CPF {cpf} já existe como chave em outra conta")

    # Verifica se o email já existe como chave em QUALQUER conta
    cursor.execute("SELECT 1 FROM chaves_pix WHERE chave = ?", (email,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO chaves_pix (conta_id, tipo, chave)
            VALUES (?, 'email', ?)
        """, (conta_id, email))
        print(f"Email {email} inserido como chave para conta {conta_id}")
    else:
        print(f"Email {email} já existe como chave em outra conta")

    conn.commit()
    conn.close()
    
# Recupera todas as chaves
def get_all_keys(conta_id):
    conn = get_db()
    cursor = conn.cursor()
    with conn:
        cursor.execute("SELECT * FROM chaves_pix WHERE conta_id = ?", (conta_id,))
        keys = cursor.fetchall()
    return keys


# Gera chave aleatória única
def create_random_key():
    """
    Gera uma chave aleatória única e verifica se já existe no banco de dados.
    Se já existir, gera outra chave até encontrar uma única.
    """
    chave_aleatoria = str(uuid4())
    while key_exists(chave_aleatoria):
        chave_aleatoria = str(uuid4())
        
    return {"success": True, "message": "Chave criada com sucesso", "chave": chave_aleatoria}


# Checar se chave já existe
def key_exists(chave):
    conn = get_db()
    cursor = conn.cursor()
    with conn:
        cursor.execute("SELECT * FROM chaves_pix WHERE chave = ?", (chave,))
        key = cursor.fetchone()
    return bool(key)



# Registrar chave aleatória no banco
def register_key(key, conta_id):
    conn = get_db()
    cursor = conn.cursor()
    with conn:
        cursor.execute("INSERT INTO chaves_pix (conta_id, tipo, chave) VALUES (?, 'aleatoria', ?)", (conta_id, key))
        # Busca a data/hora que foi registrada
        cursor.execute("SELECT criada_em FROM chaves_pix WHERE chave = ?", (key,))
        result = cursor.fetchone()
        data_registro = result[0] if result else None
        print(f"DEBUG: Chave {key} registrada em: {data_registro}")
    return {"success": True, "message": "Chave registrada com sucesso", "data_registro": data_registro}

# Deletar chave aleatória pelo ID
def delete_key_by_id(key_id):
    conn = get_db()
    cursor = conn.cursor()
    with conn:
        cursor.execute("DELETE FROM chaves_pix WHERE id = ?", (key_id,))
    return {"success": True, "message": "Chave deletada com sucesso"}

def get_key_by_value(chave):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.id AS conta_id,
            u.nome_completo,
            u.cpf,
            cp.tipo
        FROM chaves_pix cp
        JOIN contas c ON cp.conta_id = c.id
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE cp.chave = ?
    """, (chave,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "success": True,
            "data": {
                "conta_id": row[0],
                "nome": row[1],
                "cpf": row[2],
                "tipo_chave": row[3]
            }
        }
    return {"success": False}

def mask_cpf(cpf):
    return f"***.***.***-{cpf[-2:]}"
