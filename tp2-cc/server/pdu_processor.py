from msg_type.register_pdu import RegisterPDU
from msg_type.ack_pdu import AckPDU
from msg_type.report_pdu import AlertPDU
from msg_type.metric_pdu import MetricPDU
from agent.sequence_manager import get_next_seq_num, validate_seq_num
from .task_manager import start_task_processing
import socket

def process_register_pdu(data, addr, server_socket):
    """Processa PDUs de registo"""
    try:
        register_message = RegisterPDU.unpack(data)
        device_id = register_message.agent_id.strip()
        current_seq_num = register_message.seq_num

        if not validate_seq_num(device_id, current_seq_num):
            return False

        print(f"\n[REGISTER RECEBIDO] De {addr}")
        print(f"  Msg_type: {register_message.msg_type}")
        print(f"  Seq_num: {register_message.seq_num}")
        print(f"  Agent_id: {register_message.agent_id}\n")

        # Envia ACK de confirmação
        ack_message = AckPDU(msg_type=1, seq_num=current_seq_num)
        server_socket.sendto(ack_message.pack(), addr)
        print(f"[ACK ENVIADO] Confirmando registro para {addr}\n")

        # Inicia processamento de tarefas para o agente
        start_task_processing(device_id, addr, server_socket)
        return True
    except Exception as e:
        print(f"\n[ERRO] Falha ao processar registro: {e}\n")
        return False

def process_ack_pdu(data, addr, server_socket):
    """Processa PDUs de confirmação"""
    try:
        ack_message = AckPDU.unpack(data)
        print(f"\n[ACK RECEBIDO] De {addr}")
        print(f"  Seq_num: {ack_message.seq_num}")
        print(f"  Msg_type: {ack_message.msg_type}\n")
        return True
    except Exception as e:
        print(f"\n[ERRO] Falha ao processar ACK: {e}\n")
        return False

def process_metric_pdu(data, addr, server_socket):
    """Processa PDUs de métricas"""
    try:
        metric_pdu = MetricPDU.unpack(data)
        print(f"\n[METRIC RECEIVED] De {addr}")
        print(f"  Task type: {metric_pdu.task_type}")
        print(f"  Metric value: {metric_pdu.metric_value}")
        print(f"  Seq num: {metric_pdu.seq_num}\n")

        # Envia ACK para a métrica
        ack_pdu = AckPDU(1, metric_pdu.seq_num)
        server_socket.sendto(ack_pdu.pack(), addr)
        print(f"[ACK SENT] ACK enviado para métrica")
        print(f"  Seq num: {ack_pdu.seq_num}\n")
        return True
    except Exception as e:
        print(f"[ERROR] Erro ao processar métrica: {e}")
        return False

def process_alert_pdu(data, addr, server_socket=None):
    """Processa PDUs de alerta"""
    try:
        alert_pdu = AlertPDU.unpack(data)
        device_id = addr[0] if isinstance(addr, tuple) else addr  # Usa IP como identificador
        
        if not validate_seq_num(device_id, alert_pdu.seq_num):
            return False

        print(f"\n[ALERTA RECEBIDO] De {addr}")
        print(f"  Seq_num: {alert_pdu.seq_num}")
        print(f"  Msg_type: {alert_pdu.msg_type}")
        print(f"  Task_type: {alert_pdu.task_type}")
        print(f"  Metric_value: {alert_pdu.metric_value}\n")
        
        # Envia ACK para o alerta
        if not isinstance(server_socket, socket.socket) or server_socket.fileno() == -1:
            print("[ERRO] O server_socket não está válido ou foi fechado.")
            return False

        ack_pdu = AckPDU(1, alert_pdu.seq_num)
        server_socket.sendall(ack_pdu.pack())
        print(f"[ACK SENT] ACK enviado para alerta")
        print(f"  Seq num: {ack_pdu.seq_num}\n")
        
        return True
    
    except Exception as e:
        print(f"\n[ERRO] Falha ao processar alerta: {e}\n")
        return False