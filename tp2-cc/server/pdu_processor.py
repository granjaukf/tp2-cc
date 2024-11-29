from msg_type.register_pdu import RegisterPDU
from msg_type.ack_pdu import AckPDU
from msg_type.report_pdu import AlertPDU
from msg_type.metric_pdu import MetricPDU
from agent.sequence_manager import get_next_seq_num, validate_seq_num
from .task_manager import start_task_processing, task_manager


device_id_map = {}

def process_register_pdu(data, addr, server_socket):
    """Processa PDUs de registro"""
    print("------------------------------")
    print("[REGISTO RECEBIDO]")
    print("------------------------------")
    try:
        register_message = RegisterPDU.unpack(data)
        device_id = register_message.agent_id.strip()
        current_seq_num = register_message.seq_num

        if not validate_seq_num(device_id, current_seq_num):
            print("[ERRO] Seq_num inválido.")
            return False

        print(f"[SUCESSO] Registo do dispositivo: {device_id}")
        print(f"  Seq_num: {current_seq_num}")
        print("------------------------------")
        
        device_id_map[addr[0]] = device_id
        ack_message = AckPDU(msg_type=1, seq_num=current_seq_num)
        server_socket.sendto(ack_message.pack(), addr)
        print("[ACK REGISTO ENVIADO]")
        print("------------------------------")

        start_task_processing(device_id, addr, server_socket)
        return True
    except Exception as e:
        print(f"[ERRO] Falha no registro: {e}")
        print("------------------------------")
        return False


def process_ack_pdu(data, addr, server_socket):
    """Processa PDUs de confirmação"""
    print("------------------------------")
    print("[PROCESSANDO ACK]")
    try:
        ack_message = AckPDU.unpack(data)
        device_id = device_id_map.get(addr[0])

        if not device_id:
            print(f"[ERRO] Dispositivo não registrado para o endereço: {addr[0]}")
            print("------------------------------")
            return False

        print(f"[ACK RECEBIDO] Dispositivo: {device_id}")
        print(f"  Seq_num: {ack_message.seq_num}")
        
        task_manager.handle_ack(device_id, ack_message.seq_num)
        print("[ACK PROCESSADO COM SUCESSO]")
        print("------------------------------")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao processar ACK: {e}")
        print("------------------------------")
        return False



def process_metric_pdu(data, addr, server_socket):
    """Processa PDUs de métricas"""
    print("------------------------------")
    print("[PROCESSANDO MÉTRICA]")
    try:
        metric_pdu = MetricPDU.unpack(data)
        device_id = device_id_map.get(addr[0])

        if not device_id:
            print(f"[ERRO] Dispositivo não registrado para o endereço: {addr[0]}")
            print("------------------------------")
            return False

        print(f"[MÉTRICA RECEBIDA] Dispositivo: {device_id}")
        print(f"  Task Type: {metric_pdu.task_type}")
        print(f"  Metric Value: {metric_pdu.metric_value}")
        print(f"  Seq_num: {metric_pdu.seq_num}")

        task_manager.handle_metric(device_id, metric_pdu.seq_num)

        # Envia ACK para a métrica
        ack_pdu = AckPDU(1, metric_pdu.seq_num)
        server_socket.sendto(ack_pdu.pack(), addr)
        print("[ACK ENVIADO PARA MÉTRICA]")
        print("------------------------------")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao processar métrica: {e}")
        print("------------------------------")
        return False



def process_alert_pdu(data, addr, server_socket=None):
    """Processa PDUs de alerta"""
    print("------------------------------")
    print("[PROCESSANDO ALERTA]")
    try:
        alert_pdu = AlertPDU.unpack(data)
        device_id = device_id_map.get(addr[0])

        if not device_id:
            print(f"[ERRO] Dispositivo não registrado para o endereço: {addr[0]}")
            print("------------------------------")
            return False

        """if not validate_seq_num(device_id, alert_pdu.seq_num):
            print(f"[ERRO] Seq_num inválido para alerta. Dispositivo: {device_id}")
            print("------------------------------")
            return False"""

        print(f"[ALERTA RECEBIDO] Dispositivo: {device_id}")
        print(f"  Seq_num: {alert_pdu.seq_num}")
        print(f"  Task_type: {alert_pdu.task_type}")
        print(f"  Metric_value: {alert_pdu.metric_value}")

        """task_manager.handle_alert(device_id, alert_pdu.seq_num)"""

        # Envia ACK para o alerta
        """ack_pdu = AckPDU(1, alert_pdu.seq_num)
        server_socket.sendall(ack_pdu.pack())
        print("[ACK ENVIADO PARA ALERTA]")
        print("------------------------------")"""
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao processar alerta: {e}")
        print("------------------------------")
        return False
