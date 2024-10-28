from protocols.nettask import NetTaskProtocol, NetTaskPacket
import socket

class AgentNetTask(NetTaskProtocol):
    def __init__(self, socket: socket.socket, agent_id: str):
        super().__init__(socket, is_server=False)
        self.agent_id = agent_id
        
    def _process_received_data(self, packet: NetTaskPacket):
        # Implementar lógica específica do agente aqui
        if packet.data.get('type') == 'TASK':
            print(f"Received task from server: {packet.data}")
        elif packet.packet_type == 'REGISTER_ACK':
            print(f"Registration confirmed for agent {self.agent_id}")
