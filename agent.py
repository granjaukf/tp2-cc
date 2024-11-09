import socket
import argparse
import subprocess
from register_pdu import RegisterPDU
from ack_pdu import AckPDU
from nettask_pdu import NetTaskPDU
import time
import psutil
from report_pdu import AlertPDU

def execute_task(task_pdu, server_ip, alert_port):
    task_type = task_pdu.task_type
    threshold_exceeded = False  # Variável para verificar se o limite foi excedido
    metric_value = 0  # Valor da métrica monitorada

    print(f"A executar a tarefa do tipo:{task_type}")

    # Verifica e executa cada tipo de tarefa com uma condição para alerta
    if task_type == 0:  # CPU
        metric_value = psutil.cpu_percent()  # Obtém o uso atual de CPU em %
        print(f"A monitorizar CPU com limite de {task_pdu.payload.threshold_value}%. Valor atual: {metric_value}%")
        if metric_value > task_pdu.payload.threshold_value:
            threshold_exceeded = True

    elif task_type == 1:  # RAM
        metric_value = psutil.virtual_memory().percent  # Obtém o uso atual de RAM em %
        print(f"A monitorizar RAM com limite de {task_pdu.payload.threshold_value}%. Valor atual: {metric_value}%")
        if metric_value > task_pdu.payload.threshold_value:
            threshold_exceeded = True

    elif task_type == 2:  # Latency
        # Código para medir a latência aqui (ping, por exemplo)
        # Usando um valor fictício para exemplo
        metric_value = 120  # Exemplo de latência em ms
        print(f"A executar o teste de latência para {task_pdu.payload.destination}. Latência atual: {metric_value} ms")
        if metric_value > task_pdu.payload.threshold_value:
            threshold_exceeded = True

    elif task_type == 3:  # Throughput
        metric_value = task_pdu.payload.threshold_value  # Limite de throughput (exemplo)
        print(f"A executar o teste de throughput com limite de {metric_value} ms.")
        if metric_value > 200:  # Limite de exemplo para throughput
            threshold_exceeded = True

    elif task_type == 4:  # Interface
        # Exemplo fictício para monitorar tráfego da interface
        metric_value = 1600  # Exemplo de tráfego atual
        print(f"A monitorizar estatísticas da interface {task_pdu.payload.interface_name}. Tráfego atual: {metric_value}")
        if metric_value > task_pdu.payload.threshold_value:
            threshold_exceeded = True

    # Envia um alerta ao servidor se o limite for excedido
    if threshold_exceeded:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as alert_socket:
                alert_socket.connect((server_ip, alert_port))
                alert_pdu = AlertPDU(msg_type=3, seq_num=task_pdu.seq_num, task_type=task_type, metric_value=metric_value)
                alert_socket.sendall(alert_pdu.pack())
                print(f"Alerta enviado ao servidor para o tipo de tarefa {task_type} com valor da métrica {metric_value}.")
        except Exception as e:
            print(f"Erro ao enviar o alerta: {e}")


def start_agent(host, port=12345, alert_port=12346, timeout=30):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('0.0.0.0', 0))  # Porta dinâmica (0) para permitir múltiplos agentes
    client_socket.settimeout(5)  # Timeout para aguardar respostas do servidor
    
    agent_id = socket.gethostname().ljust(20)[:20]  # Garante que agent_id tenha exatamente 20 bytes  
    last_task_time = time.time()  # Marca o tempo da última tarefa recebida

    try:
        # Tenta enviar a mensagem de registro e aguardar o ACK
        attempts = 0
        max_attempts = 5  # Número máximo de tentativas para retransmissão
        msg_type = 0
        register_seq_num = 0  # Sequência para o registro inicial
        while attempts < max_attempts:
            register_message = RegisterPDU(msg_type, register_seq_num, agent_id)
            packed_register = register_message.pack()
            client_socket.sendto(packed_register, (host, port))
            print(f"RegisterPDU enviado para {host}:{port}:")
            print(f"  msg_type: {msg_type}")
            print(f"  seq_num: {register_seq_num}")
            print(f"  agent_id: {agent_id} (tentativa {attempts + 1})")
            
            try:
                # Espera por uma resposta do servidor   
                ack_data, _ = client_socket.recvfrom(1024)
                ack_message = AckPDU.unpack(ack_data)
                print("ACK recebido do servidor:")
                print(f"  msg_type: {ack_message.msg_type}")
                print(f"  seq_num: {ack_message.seq_num}")
                
                # Verifica se o ACK corresponde ao número de sequência do registro inicial
                if ack_message.seq_num == register_seq_num:
                    print("Registro confirmado.")
                    break
            except socket.timeout:
                print("Nenhum ACK recebido, retransmitindo...")
                attempts += 1
                register_seq_num += 1
        if attempts == max_attempts:
            print("Falha ao receber o ACK após várias tentativas.")
            return
        
        # Loop para aguardar e processar tarefas
        while True:
            try:
                task_data, server_addr = client_socket.recvfrom(1024)
                task_pdu = NetTaskPDU.unpack(task_data)
                print("Tarefa recebida do servidor.")
                
                # Executa a tarefa e verifica se um alerta deve ser enviado
                execute_task(task_pdu, server_ip=host, alert_port=alert_port)
                
                # Atualiza o tempo da última tarefa recebida
                last_task_time = time.time()
                
                # Envia o ACK de volta ao servidor com o mesmo seq_num da tarefa recebida
                ack_message = AckPDU(msg_type=1, seq_num=task_pdu.seq_num)
                client_socket.sendto(ack_message.pack(), server_addr)
                print(f"ACK enviado de volta ao servidor para confirmar recebimento da tarefa. seq_num: {task_pdu.seq_num}")
                
            except socket.timeout:
                # Verifica se o tempo desde a última tarefa recebida excede o timeout
                if time.time() - last_task_time > timeout:
                    print(f"Tempo limite de {timeout} segundos atingido sem receber novas tarefas. Encerrando agente.")
                    break
                
    except KeyboardInterrupt:
        print("\nAgente encerrado.")
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente para enviar RegisterPDU para o servidor.")
    parser.add_argument("host", type=str, help="Endereço IP do servidor.")
    parser.add_argument("--alert_port", type=int, default=12346, help="Porta para envio de alertas ao servidor.")
    parser.add_argument("--timeout", type=int, default=30, help="Tempo limite em segundos para aguardar tarefas.")
    args = parser.parse_args()
    
    start_agent(args.host, alert_port=args.alert_port, timeout=args.timeout)
