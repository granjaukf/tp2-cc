import socket
import select
import threading
from .message_handler import handle_agent_message

def start_server(task_port=12345, alert_port=12346):
    """Inicia o servidor NMS"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', task_port))
    print(f"\n[SERVER INICIADO] A escutar na porta UDP {task_port} para registos e tarefas.\n")

    alert_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    alert_socket.bind(('0.0.0.0', alert_port))
    alert_socket.listen(5)
    print(f"[SERVER INICIADO] A escutar na porta TCP {alert_port} para alertas.\n")

    try:
        while True:
            ready_sockets, _, _ = select.select([server_socket, alert_socket], [], [])
            for sock in ready_sockets:
                if sock == server_socket:
                    data, addr = server_socket.recvfrom(1024)
                    threading.Thread(target=handle_agent_message, 
                                  args=(data, addr, server_socket, False)).start()
                elif sock == alert_socket:
                    client_socket, addr = alert_socket.accept()
                    data = client_socket.recv(1024)
                    threading.Thread(target=handle_agent_message,
                                  args=(data, addr, client_socket, True)).start()
                    client_socket.close()
    except KeyboardInterrupt:
        print("\n[SERVER ENCERRADO]\n")
    finally:
        server_socket.close()
        alert_socket.close()

if __name__ == "__main__":
    start_server()