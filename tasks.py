import logging
import signal
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR
from pytz import utc

# Importe as funções das suas tarefas
from utils.services.banco.investimento import (
    atualizar_ativos,
    processar_investimentos_expirados
)
from utils.services.banco.faturas import (
    gerar_faturas_mensais_todos_usuarios,
    gerar_faturas_aleatorias_todos_usuarios,
    checa_juros
)
from utils.services.emprego.functions import pagar_salarios


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Define um executor com pool de threads limitado (máximo 5 threads)
    executors = {
        'default': ThreadPoolExecutor(5)
    }

    # Cria o scheduler com timezone UTC e executor configurado
    scheduler = BackgroundScheduler(
        timezone=utc,
        executors=executors
    )

    # Adiciona as tarefas com parâmetros de segurança
    jobs_config = [
        # Tarefas curtas (segundos)
        {
            'func': atualizar_ativos,
            'trigger': IntervalTrigger(seconds=5),
            'id': 'ativos',
            'max_instances': 1,
            'coalesce': True,
            'misfire_grace_time': 10,   # evita execução atrasada por mais de 10s
            'replace_existing': True
        },
        {
            'func': processar_investimentos_expirados,
            'trigger': IntervalTrigger(seconds=10),
            'id': 'investimentos_expirados',
            'max_instances': 1,
            'coalesce': True,
            'misfire_grace_time': 15,
            'replace_existing': True
        },
        # Tarefa de juros (5 minutos)
        {
            'func': checa_juros,
            'trigger': IntervalTrigger(seconds=300),
            'id': 'juros',
            'max_instances': 1,
            'coalesce': True,
            'misfire_grace_time': 30,
            'replace_existing': True
        },
        # Tarefas de 1 hora – com jitter para espalhar a execução
        {
            'func': pagar_salarios,
            'trigger': IntervalTrigger(seconds=3600, jitter=60),
            'id': 'salarios',
            'max_instances': 1,
            'coalesce': True,
            'misfire_grace_time': 120,
            'replace_existing': True
        },
        {
            'func': gerar_faturas_mensais_todos_usuarios,
            'trigger': IntervalTrigger(seconds=3600, jitter=60),
            'id': 'faturas_mensais',
            'max_instances': 1,
            'coalesce': True,
            'misfire_grace_time': 120,
            'replace_existing': True
        },
        {
            'func': gerar_faturas_aleatorias_todos_usuarios,
            'trigger': IntervalTrigger(seconds=3600, jitter=60),
            'id': 'faturas_aleatorias',
            'max_instances': 1,
            'coalesce': True,
            'misfire_grace_time': 120,
            'replace_existing': True
        }
    ]

    # Função de callback para erros nos jobs
    def job_error_listener(event):
        logger.error(f"Job '{event.job_id}' falhou na execução. Exceção: {event.exception}")

    # Adiciona o listener de erros
    scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)

    # Agenda todos os jobs
    for job in jobs_config:
        scheduler.add_job(**job)
        logger.info(f"Job '{job['id']}' agendado com intervalo {job['trigger']}")

    scheduler.start()

    try:
        # Mantém rodando sem consumir CPU
        import threading
        threading.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

    # Tratamento de sinais para desligamento gracioso
    def signal_handler(signum, frame):
        logger.info("Sinal recebido, desligando scheduler...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Bloqueia até receber um sinal
    signal.pause()

if __name__ == "__main__":
    main()