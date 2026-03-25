import time
from utils.tasks_control import deve_executar_tarefa
from utils.services.banco.investimento import atualizar_ativos, processar_investimentos_expirados
from utils.services.banco.faturas import gerar_faturas_mensais_todos_usuarios, gerar_faturas_aleatorias_todos_usuarios, checa_juros
from utils.services.emprego.functions import pagar_salarios

def main():
    print("Worker iniciado. Aguardando ciclos...")
    ultima_expiracao = time.time()
    while True:
        try:
            # ========== Tarefas com intervalos fixos ==========
            if deve_executar_tarefa("ativos", 5):
                atualizar_ativos()
                print("Atualização de ativos concluída")

            if deve_executar_tarefa("juros", 300):           # 5 minutos
                checa_juros()
                print("Juros aplicados")

            if deve_executar_tarefa("salarios", 3600):       # 1 hora
                pagar_salarios()
                print("Salários pagos")

            if deve_executar_tarefa("faturas_mensais", 3600): # 1 hora
                gerar_faturas_mensais_todos_usuarios()
                print("Faturas mensais geradas")

            if deve_executar_tarefa("faturas_aleatorias", 3600): # 1 hora
                gerar_faturas_aleatorias_todos_usuarios()
                print("Faturas aleatórias geradas")

            # ========== Tarefa de expiração (intervalo de 10s) ==========
            agora = time.time()
            if agora - ultima_expiracao >= 10:
                processar_investimentos_expirados()
                ultima_expiracao = agora
                print("Investimentos expirados processados")

        except Exception as e:
            print(f"[ERRO] Falha no ciclo do worker: {e}")

        time.sleep(1)   # Aguarda 1 segundo antes de repetir

if __name__ == "__main__":
    main()