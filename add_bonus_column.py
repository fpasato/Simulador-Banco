import sqlite3

def migrate_bonus_column():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 1. Verificar se a coluna first_login_bonus existe em usuarios e removê-la
    cursor.execute("PRAGMA table_info(usuarios)")
    columns_usuarios = [col[1] for col in cursor.fetchall()]
    if "first_login_bonus" in columns_usuarios:
        cursor.execute("ALTER TABLE usuarios DROP COLUMN first_login_bonus")
        print("✅ Coluna 'first_login_bonus' removida da tabela 'usuarios'.")
    else:
        print("ℹ️ Coluna 'first_login_bonus' não existe em 'usuarios'.")

    # 2. Verificar se a coluna existe em contas; se não, adicionar
    cursor.execute("PRAGMA table_info(contas)")
    columns_contas = [col[1] for col in cursor.fetchall()]
    if "first_login_bonus" not in columns_contas:
        cursor.execute("ALTER TABLE contas ADD COLUMN first_login_bonus INTEGER DEFAULT 0")
        print("✅ Coluna 'first_login_bonus' adicionada à tabela 'contas'.")
    else:
        print("ℹ️ Coluna 'first_login_bonus' já existe em 'contas'.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_bonus_column()