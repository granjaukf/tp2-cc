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
    
    agent_id = socket.gethostname().ljust(20)[:20]
    server_address = (host,port)
    
    if not register_agent(client_socket, agent_id, server_address):
        client_socket.close()
        return 
    
    task_executor = TaskExecutor(host, alert_port,task_port, agent_id)
    process_tasks(client_socket, task_executor, timeout)
    client_socket.close()

def register_agent(client_socket, agent_id, server_address):
    "Regista o agente no servidor"
    attempts = 0
    max_attempts = 5
    seq_num = sequence_manager.get_next_seq_num(agent_id,len(agent_id))
    register_message = RegisterPDU(0, seq_num, agent_id)
    packed_register = register_message.pack()
    
    while attempts < max_attempts:
        client_socket.sendto(packed_register,server_address)
        print(f"Register PDU enviado com seq_num {register_message.seq_num}")
        
        try:
            ack_data, _ = client_socket.recvfrom(1024)
            ack_message = AckPDU.unpack(ack_data)
            if ack_message.seq_num == register_message.seq_num:
                print("ACK recebido, registo confirmado.")
                return True
        except socket.timeout:
            print("Nenhum ACK recebido, retransmitindo...")
            attempts += 1
            seq_num = sequence_manager.get_next_seq_num(agent_id,len(packed_register))
    
    print("Falha ao receber o ACK após várias tentativas.")
    return False

def process_tasks(client_socket, task_executor, timeout):
    """Processa as tarefas recebidas do servidor"""
    last_task_time = time.time()
    
    while True:
        try:
            # Recebe a tarefa
            task_data, server_addr = client_socket.recvfrom(1024)
            task_pdu = NetTaskPDU.unpack(task_data)
            print(f"[TASK RECEIVED] Tarefa recebida com seq_num {task_pdu.seq_num}")
            
            # Envia ACK para a tarefa
            if send_task_ack(client_socket, task_pdu, server_addr):
                task_executor.execute_task(task_pdu)
                last_task_time = time.time()
        
        except socket.timeout:
            if time.time() - last_task_time > timeout:
                print("Agente a encerrar por inatividade.")
                break
            continue
        except Exception as e:
            print(f"[ERRO] Eroo as processar a mensagem: {e}")
            
def send_task_ack(client_socket, task_pdu, server_addr):
    """Envia ACK para uma tarefa recebida"""
    
    try:
        ack_pdu = AckPDU(1,task_pdu.seq_num)
        packed_ack = ack_pdu.pack()
        client_socket.sendto(packed_ack,server_addr)
        print(f"[ACK SENT] ACK enviado para o servidor")
        print(f"  Seq_num do ACK: {ack_pdu.seq_num}")
        print(f"  Endereço do servidor: {server_addr}\n")
        return True
    except Exception as e:
        print(f"[ERRO] Tentativa de envio de ACK falhou: {e}")
        return False
    

