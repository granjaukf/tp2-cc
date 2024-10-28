import socket
import threading
import json
import time
import random

class NMSAgent:
    def __init__(self, agent_id, server_udp_addr=('localhost', 5000), server_tcp_addr=('localhost', 5001)):
        self.agent_id = agent_id
        self.server_udp_addr = server_udp_addr
        self.server_tcp_addr = server_tcp_addr
        
        # UDP Socket for NetTask protocol
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        agent_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        nettask = AgentNetTask(agent_socket, "agent_1")

        # Registrar o agente
        nettask.send({
            'type': 'register',
            'agent_id': 'agent_1'
        })

        # Enviar métricas
        nettask.send({
            'type': 'metric',
            'agent_id': 'agent_1',
            'metrics': {'cpu': 50, 'memory': 70}
        })
        
        # TCP Socket for AlertFlow protocol
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        
    def start(self):
        # Register with server
        self.register()
        
        # Connect TCP socket
        self.tcp_socket.connect(self.server_tcp_addr)
        
        # Start metric reporting
        metric_thread = threading.Thread(target=self.report_metrics)
        metric_thread.start()
        
        # Simulate alert generation
        alert_thread = threading.Thread(target=self.simulate_alerts)
        alert_thread.start()
        
    def register(self):
        message = {
            'type': 'register',
            'agent_id': self.agent_id
        }
        self.udp_socket.sendto(json.dumps(message).encode(), self.server_udp_addr)
        
        # Wait for confirmation
        data, _ = self.udp_socket.recvfrom(1024)
        response = json.loads(data.decode())
        if response['type'] == 'register_ack':
            print(f"Agent {self.agent_id} successfully registered")
            
    def report_metrics(self):
        while True:
            # Simulate metric collection
            metrics = {
                'type': 'metric',
                'agent_id': self.agent_id,
                'data': {
                    'cpu_usage': random.randint(0, 100),
                    'memory_usage': random.randint(0, 100)
                }
            }
            
            self.udp_socket.sendto(json.dumps(metrics).encode(), self.server_udp_addr)
            time.sleep(5)  # Report every 5 seconds
            
    def simulate_alerts(self):
        while True:
            time.sleep(15)  # Generate alert every 15 seconds
            alert = {
                'type': 'alert',
                'agent_id': self.agent_id,
                'severity': 'high',
                'message': 'Simulated critical event'
            }
            self.tcp_socket.send(json.dumps(alert).encode())

if __name__ == "__main__":
    # Create and start three agents
    agents = []
    for i in range(3):
        agent = NMSAgent(f"agent_{i+1}")
        agents.append(agent)
        agent.start()