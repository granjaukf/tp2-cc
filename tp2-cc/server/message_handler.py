import socket
from .pdu_processor import process_register_pdu, process_ack_pdu, process_metric_pdu, process_alert_pdu

def handle_agent_message(data, addr, server_socket, is_alert=False):
    """Processa mensagens recebidas dos agentes"""
    if is_alert:
        return process_alert_pdu(data, addr, server_socket)
    
    msg_type = data[0] >> 5
    handlers = {
        0: process_register_pdu,  # RegisterPDU
        1: process_ack_pdu,       # AckPDU
        3: process_metric_pdu     # MetricPDU
    }
    
    if msg_type in handlers:
        return handlers[msg_type](data, addr, server_socket)
    else:
        print(f"\n[ERRO] Tipo de mensagem desconhecido: {msg_type}\n")
        return None