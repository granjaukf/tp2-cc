import threading
import time
from threading import Lock
from queue import Queue
from agent.sequence_manager import get_next_seq_num
from .tasks_parser import load_tasks

class TaskManager:
    def __init__(self):
        self._task_queues = {}  # device_id -> Queue
        self._pending_tasks = {}  # (device_id, seq_num) -> Event
        self._pending_metrics = {}  # (device_id, seq_num) -> Event
        self._lock = Lock()
        
    def queue_task(self, device_id, task_pdu):
        """Adiciona uma tarefa à fila do dispositivo"""
        with self._lock:
            if device_id not in self._task_queues:
                self._task_queues[device_id] = Queue()
            self._task_queues[device_id].put(task_pdu)

    def send_single_task(self, task_pdu, device_id, agent_addr, server_socket):
        """Envia uma única tarefa e aguarda confirmação"""
        task_pdu.seq_num = get_next_seq_num(device_id, 1)
        packed_task = task_pdu.pack()
        
        # Cria eventos para rastrear ACK e métrica
        ack_event = threading.Event()
        metric_event = threading.Event()
        
        with self._lock:
            self._pending_tasks[(device_id, task_pdu.seq_num)] = ack_event
            self._pending_metrics[(device_id, task_pdu.seq_num)] = metric_event

        try:
            for attempt in range(6):
                print(f"\n[TASK ENVIADA] Para {device_id} no endereço {agent_addr}")
                print(f"  Tarefa seq_num: {task_pdu.seq_num}\n")
                
                server_socket.sendto(packed_task, agent_addr)
                
                # Aguarda ACK por 3 segundos
                if ack_event.wait(3.0):
                    with self._lock:
                        key = (device_id, task_pdu.seq_num)
                        if key in self._pending_metrics:
                            print("[DUP] Pacote Duplicado\n")
                            return True
                    print(f"[ACK RECEBIDO] ACK recebido para a tarefa seq_num {task_pdu.seq_num}\n")
                print(f"[TIMEOUT] Tentativa {attempt + 1} de envio da tarefa {task_pdu.seq_num}\n")
                time.sleep(1)
            
            return False
            
        finally:
            # Limpa os eventos pendentes
            with self._lock:
                self._pending_tasks.pop((device_id, task_pdu.seq_num), None)
                self._pending_metrics.pop((device_id, task_pdu.seq_num), None)

    def handle_ack(self, device_id, seq_num):
        """Processa um ACK recebido e sinaliza o evento correspondente"""
        with self._lock:
            event = self._pending_tasks.get((device_id, seq_num))
            if event:
                event.set()  # Sinaliza que o ACK foi recebido
                return True
        print(f"[ERRO] Nenhum evento de ACK encontrado para device_id={device_id}, seq_num={seq_num}")
        return False


    def handle_metric(self, device_id, seq_num):
        """Processa uma métrica recebida"""
        with self._lock:
            event = self._pending_metrics.get((device_id, seq_num))
            if event:
                event.set()
                return True
        return False

# Instância global do gerenciador de tarefas
task_manager = TaskManager()

def start_task_processing(device_id, agent_addr, server_socket):
    """Inicia o processamento de tarefas para um agente"""
    def process_tasks():
        tasks = load_tasks()

        for task_device_id, task_pdu in tasks:
            if task_device_id == device_id:
                task_manager.queue_task(device_id, task_pdu)

        # Processa tarefas da fila uma por uma
        task_queue = task_manager._task_queues.get(device_id)
        if not task_queue:
            print(f"[AVISO] Nenhuma tarefa encontrada para {device_id}")
            return

        while not task_queue.empty():
            task_pdu = task_queue.get()
            if not task_manager.send_single_task(task_pdu, device_id, agent_addr, server_socket):
                print(f"[ERRO] Falha ao processar tarefa {task_pdu.seq_num} para {device_id}\n")
                break
            
            # Aguarda um intervalo entre tarefas
            time.sleep(2)

    threading.Thread(target=process_tasks).start()