from utils.validators import get_db
    
def get_balance(usuario_id):
    """Get balance for a specific user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT saldo FROM contas WHERE usuario_id = ?", (usuario_id,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    return 0.0