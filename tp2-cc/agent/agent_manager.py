import socket 
import subprocess
import threading
import time
from .sequence_manager import sequence_manager
from .task_executor import TaskExecutor
from msg_type.register_pdu import RegisterPDU
from msg_type.ack_pdu import AckPDU
from msg_type.nettask_pdu import NetTaskPDU

def start_agent(host,port=12345, alert_port=12346,task_port=12345,iperf_port = 5202,timeout=120):
    "Inicia o agente e gere sua execução"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('0.0.0.0',0))
    client_socket.settimeout(5)
    agent_id = socket.gethostname().ljust(5)[:5]
    server_address = (host,port)
    
    iperf_thread = threading.Thread(target=start_iperf_server, args=(iperf_port,), daemon=True)
    iperf_thread.start()
    
    try:
        if not register_agent(client_socket, agent_id, server_address):
            client_socket.close()
            return 
    
        task_executor = TaskExecutor(host, alert_port,task_port, agent_id)
        process_tasks(client_socket, task_executor, timeout)
        client_socket.close()
    finally:
        client_socket.close()
        
def start_iperf_server(iperf_port):
    """Inicia o servidor iperf em modo servidor."""
    print(f"[IPERF] Iniciando servidor iperf na porta {iperf_port}...")
    try:
        command = ["iperf3", "-s", "-p", str(iperf_port)]
        subprocess.Popen(command,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erro ao iniciar o servidor iperf: {e}")
    except FileNotFoundError:
        print("[ERROR] iperf3 não está instalado. Verifique a instalação.")

def register_agent(client_socket, agent_id, server_address):
    """Registra o agente no servidor"""
    print("------------------------------")
    print(f"[A INICIAR REGISTO] Agente: {agent_id}")
    print("------------------------------")
    attempts = 0
    max_attempts = 5
    seq_num = sequence_manager.get_next_seq_num(agent_id, 1)
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
        seq_num = sequence_manager.get_next_seq_num(agent_id, 1)
    
    print("[ERRO] Registo falhou após várias tentativas.")
    print("------------------------------")
    return False


def process_tasks(client_socket, task_executor, timeout):
    """Processa as tarefas recebidas do servidor"""
    last_task_time = time.time()
    tasks = []
    i = 0
    seq_num = 0
    periodic = False
    length = 0

    
    while True:
        #if len(tasks) < 7:
        if periodic == False:
            try:
                # Recebe a tarefa
                task_data, server_addr = client_socket.recvfrom(1024)
                task_pdu = NetTaskPDU.unpack(task_data)
                if len(tasks) > 0 and tasks[len(tasks)-1].seq_num == task_pdu.seq_num:
                    print("[DUP] Pacote duplicado \n")
                    if send_task_ack(client_socket, task_pdu, server_addr):
                        last_task_time = time.time()
                    continue
                tasks.append(task_pdu)
                print(f"[TASK RECEIVED] Tarefa recebida com seq_num {task_pdu.seq_num}")
                seq_num = task_pdu.seq_num
                length = length+1
            
                # Envia ACK para a tarefa
                if send_task_ack(client_socket, task_pdu, server_addr):
                    #task_executor.execute_task(task_pdu, seq_num)
                    last_task_time = time.time()
        
            except socket.timeout:
                if time.time() - last_task_time >= 30:
                    periodic = True
                continue
            except Exception as e:
                print(f"[ERRO] Erro ao processar a mensagem: {e}")
        else:
            task = tasks[i]
            i = i+1
            seq_num = seq_num+1
            task_executor.execute_task(task, seq_num)
            if i == length:
                i = 0
            if i == 0:
                print(f"Frequência: {tasks[0].freq}")
                time.sleep(tasks[0].freq)



            
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

    

