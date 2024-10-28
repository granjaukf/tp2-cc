# nms_server/server_nettask.py
import socket
from protocols.nettask import NetTaskProtocol, NetTaskPacket

class ServerNetTask(NetTaskProtocol):
    def __init__(self, socket: socket.socket):
        super().__init__(socket, is_server=True)
        
    def _process_received_data(self, packet: NetTaskPacket):
        # Implementar lógica específica do servidor aqui
        if packet.data.get('type') == 'metric':
            print(f"Received metric from agent: {packet.data}")
        elif packet.data.get('type') == 'register':
            print(f"Agent registration request: {packet.data}")
            # Enviar confirmação de registro
            self.send({'status': 'registered'}, 'REGISTER_ACK')
