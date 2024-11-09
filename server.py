import socket
import select  # Importação correta do módulo select
import threading
from register_pdu import RegisterPDU
from ack_pdu import AckPDU
from report_pdu import AlertPDU


# Dicionário para armazenar o estado dos agentes (inclui `seq_num`)
agent_state = {}

def get_next_seq_num(device_id):
    if device_id not in agent_state:
        agent_state[device_id] = {'seq_num': 1}
    else:
        agent_state[device_id]['seq_num'] += 1
    return agent_state[device_id]['seq_num']

def handle_agent_message(data, addr, server_socket, is_alert=False):
    if is_alert:
        # Trata a mensagem de alerta
        try:
            alert_pdu = AlertPDU.unpack(data)
            print(f"Alerta recebido de {addr}:")
            print(f"  task_type: {alert_pdu.task_type}")
            print(f"  metric_value: {alert_pdu.metric_value}")
        except Exception as e:
            print(f"Erro ao processar o alerta de {addr}: {e}")
    else:
        # Trata as mensagens normais (registro e tarefas)
        msg_type = data[0] >> 5
        if msg_type == 0:  # RegisterPDU
            register_message = RegisterPDU.unpack(data)
            device_id = register_message.agent_id.strip()
            print(f"RegisterPDU recebido de {addr}:")
            print(f"  msg_type: {register_message.msg_type}")
            print(f"  seq_num: {register_message.seq_num}")
            print(f"  agent_id: {register_message.agent_id}")

            agent_state[device_id] = {'addr': addr, 'seq_num': 0}
            print(f"Agente {device_id} registrado com sucesso em {addr}")

            ack_message = AckPDU(msg_type=1, seq_num=register_message.seq_num)
            server_socket.sendto(ack_message.pack(), addr)
            print("ACK enviado para o agente.")

            threading.Thread(target=send_tasks, args=(device_id, addr, server_socket)).start()

def send_tasks(device_id, agent_addr, server_socket):
    from tasks_parser import load_tasks
    tasks = load_tasks()
    for task_device_id, task_pdu in tasks:
        if task_device_id == device_id:
            print(f"A enviar a tarefa apropriada para {device_id} com o endereço {agent_addr}")
            server_socket.sendto(task_pdu.pack(), agent_addr)

def start_server(task_port=12345, alert_port=12346):
    # Configuração do socket UDP para escutar registros e tarefas
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', task_port))
    print(f"Servidor UDP escutando na porta {task_port} para registros e tarefas.")

    # Configuração do socket TCP para escutar alertas
    alert_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    alert_socket.bind(('0.0.0.0', alert_port))
    alert_socket.listen(5)
    print(f"Servidor TCP escutando na porta {alert_port} para alertas.")

    try:
        while True:
            ready_sockets, _, _ = select.select([server_socket, alert_socket], [], [])
            for sock in ready_sockets:
                if sock == server_socket:
                    data, addr = server_socket.recvfrom(1024)
                    threading.Thread(target=handle_agent_message, args=(data, addr, server_socket, False)).start()
                elif sock == alert_socket:
                    client_socket, addr = alert_socket.accept()
                    data = client_socket.recv(1024)
                    threading.Thread(target=handle_agent_message, args=(data, addr, client_socket, True)).start()
                    client_socket.close()

    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server_socket.close()
        alert_socket.close()

if __name__ == "__main__":
    start_server()
