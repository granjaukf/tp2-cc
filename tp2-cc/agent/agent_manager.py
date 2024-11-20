import socket 
import time
from .sequence_manager import sequence_manager
from .task_executor import TaskExecutor
from msg_type.register_pdu import RegisterPDU
from msg_type.ack_pdu import AckPDU
from msg_type.nettask_pdu import NetTaskPDU

def start_agent(host,port=12345, alert_port=12346,task_port=12345,timeout=120):
    "Inicia o agente e gere sua execução"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('0.0.0.0',0))
    client_socket.settimeout(5)
    agent_id = socket.gethostname().ljust(5)[:5]
    server_address = (host,port)
    
    if not register_agent(client_socket, agent_id, server_address):
        client_socket.close()
        return 
    
    task_executor = TaskExecutor(host, alert_port,task_port, agent_id)
    process_tasks(client_socket, task_executor, timeout)
    client_socket.close()

def register_agent(client_socket, agent_id, server_address):
    """Registra o agente no servidor"""
    print("------------------------------")
    print(f"[A INICIAR REGISTO] Agente: {agent_id}")
    print("------------------------------")
    attempts = 0
    max_attempts = 5
    seq_num = sequence_manager.get_next_seq_num(agent_id, len(agent_id))
    register_message = RegisterPDU(0, seq_num, agent_id)
    packed_register = register_message.pack()

    while attempts < max_attempts:
        print(f"[TENTATIVA {attempts + 1}] Enviando Register PDU com seq_num {seq_num}")
        client_socket.sendto(packed_register, server_address)
        
        try:
            ack_data, _ = client_socket.recvfrom(1024)
            ack_message = AckPDU.unpack(ack_data)
            if ack_message.seq_num == register_message.seq_num:
                print(f"[SUCESSO] Registo confirmado. ACK seq_num: {ack_message.seq_num}")
                print("------------------------------")
                return True
        except socket.timeout:
            print(f"[TIMEOUT] Nenhum ACK recebido. Tentando novamente...")

        attempts += 1
        seq_num = sequence_manager.get_next_seq_num(agent_id, len(packed_register))
    
    print("[ERRO] Registo falhou após várias tentativas.")
    print("------------------------------")
    return False


def process_tasks(client_socket, task_executor, timeout):
    """Processa as tarefas recebidas do servidor e gerencia periodicidade."""
    print("------------------------------")
    print("[A PROCESSAR TAREFAS]")
    print("------------------------------")

    tasks = {}  # Armazena tarefas recebidas
    last_task_time = {}  # Armazena o tempo da última execução de cada tarefa
    last_received_time = time.time()  # Marca o último momento em que uma tarefa foi recebida

    while True:
        try:
            # Recebe uma nova tarefa do servidor
            task_data, server_addr = client_socket.recvfrom(1024)
            task_pdu = NetTaskPDU.unpack(task_data)

            print("------------------------------")
            print(f"[NOVA TAREFA RECEBIDA] Seq_num: {task_pdu.seq_num}")
            print(f"  Tipo: {task_pdu.task_type} | Frequência: {task_pdu.freq}s")
            print("------------------------------")
            
            # Envia ACK para a tarefa recebida
            send_task_ack(client_socket, task_pdu, server_addr)
            
            # Registra a tarefa e inicializa o tempo da última execução
            tasks[task_pdu.seq_num] = task_pdu
            last_task_time[task_pdu.seq_num] = 0  # Nunca foi executada ainda
            last_received_time = time.time()  # Atualiza o tempo de última recepção

        except socket.timeout:
            current_time = time.time()

            # Verifica periodicidade das tarefas
            for seq_num, task_pdu in list(tasks.items()):
                if current_time - last_task_time[seq_num] >= task_pdu.freq:
                    print(f"[A RECOLHER A MÉTRICA PERIODICA] Seq_num: {seq_num}")
                    task_executor.execute_task(task_pdu)
                    last_task_time[seq_num] = current_time  # Atualiza o tempo de execução

            # Verifica inatividade do agente
            if current_time - last_received_time > timeout:
                print("[ENCERRANDO AGENTE...] Inatividade detectada.")
                print("------------------------------")
                break
        except Exception as e:
            print(f"[ERRO] Ao processar a tarefa: {e}")
            print("------------------------------")


            
def send_task_ack(client_socket, task_pdu, server_addr):
    """Envia ACK para uma tarefa recebida"""
    print("------------------------------")
    print(f"[ENVIANDO ACK] Seq_num: {task_pdu.seq_num}")
    print("------------------------------")
    
    try:
        ack_pdu = AckPDU(1, task_pdu.seq_num)
        packed_ack = ack_pdu.pack()
        client_socket.sendto(packed_ack, server_addr)
        print(f"[ACK ENVIADO] Seq_num: {ack_pdu.seq_num}")
        print("------------------------------")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao enviar ACK: {e}")
        print("------------------------------")
        return False

    

