import socket
import threading
import json
from protocols.nettask import NetTaskPacket
from server_nettask import ServerNetTask

class NMSServer:
    def __init__(self, udp_port=5000, tcp_port=5001):
        # UDP Socket for NetTask protocol
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('0.0.0.0', udp_port))
        nettask = ServerNetTask(server_socket)

        nettask.send({
            'type': 'TASK',
            'task_id': '123',
            'description': 'collect_metrics'
        })

        
        # TCP Socket for AlertFlow protocol
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(('0.0.0.0', tcp_port))
        self.tcp_socket.listen(5)
        
        # Store registered agents
        self.agents = {}
        
        print(f"Server started on UDP port {udp_port} and TCP port {tcp_port}")
        
    def start(self):
        # Start UDP listener thread
        udp_thread = threading.Thread(target=self.handle_udp_messages)
        udp_thread.start()
        
        # Start TCP listener thread
        tcp_thread = threading.Thread(target=self.handle_tcp_connections)
        tcp_thread.start()
        
    def handle_udp_messages(self):
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = json.loads(data.decode())
                
                if message['type'] == 'register':
                    # Handle agent registration
                    agent_id = message['agent_id']
                    self.agents[agent_id] = addr
                    print(f"Agent {agent_id} registered from {addr}")
                    
                    # Send confirmation
                    response = json.dumps({'type': 'register_ack', 'status': 'success'})
                    self.udp_socket.sendto(response.encode(), addr)
                    
                elif message['type'] == 'metric':
                    # Handle metric reports
                    print(f"Received metric from {message['agent_id']}: {message['data']}")
                    
            except Exception as e:
                print(f"Error handling UDP message: {e}")
                
    def handle_tcp_connections(self):
        while True:
            try:
                client_socket, addr = self.tcp_socket.accept()
                # Start a new thread for each TCP connection
                thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,))
                thread.start()
            except Exception as e:
                print(f"Error accepting TCP connection: {e}")
                
    def handle_tcp_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                alert = json.loads(data.decode())
                print(f"Received alert: {alert}")
                
        except Exception as e:
            print(f"Error handling TCP client: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    server = NMSServer()
    server.start()