from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from utils.services.emprego.functions import pagar_salarios
from utils.services.banco.investimento import atualizar_ativos, processar_investimentos_expirados
from utils.services.banco.faturas import gerar_faturas_aleatorias_todos_usuarios, gerar_faturas_mensais_todos_usuarios, checa_juros

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Atualiza valores de investimento a cada 30 minutos
    scheduler.add_job(atualizar_ativos, 'interval', seconds=5)

    # Paga salários a cada 30 minutos 
    scheduler.add_job(pagar_salarios, 'interval', hours=1)

    # Gera faturas mensais obrigatórias a cada 30 minutos
    scheduler.add_job(gerar_faturas_mensais_todos_usuarios, 'interval', hours=1)

    # Gera faturas aleatórias a cada 25 minutos
    scheduler.add_job(gerar_faturas_aleatorias_todos_usuarios, 'interval', hours=1)
    
    # Aplica juros em faturas atrasadas
    scheduler.add_job(checa_juros, 'interval', minutes=5)
    
    # Processa investimentos expirados
    scheduler.add_job(processar_investimentos_expirados, 'interval', seconds=5)

    scheduler.start()
    
    
    