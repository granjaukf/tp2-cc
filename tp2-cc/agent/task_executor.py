import socket
import subprocess
import json
import psutil
from .sequence_manager import sequence_manager
from msg_type.metric_pdu import MetricPDU
from msg_type.ack_pdu import AckPDU
from msg_type.report_pdu import AlertPDU

class TaskExecutor:
    def __init__(self, server_ip, alert_port, task_port, agent_id):
        self.server_ip = server_ip
        self.alert_port = alert_port
        self.task_port = task_port
        self.agent_id = agent_id
        self.server_process = None
    
    def execute_task(self,task_pdu):
        """Executa uma tarefa e envia os resultados"""
        print(f"A executar a tarefa do tipo: {task_pdu.task_type}")
        
        metric_value = self._collect_metric(task_pdu)
        threshold_exceeded = self._check_threshold(task_pdu,metric_value)
        
        self._send_metric(task_pdu.task_type, metric_value)
        
        if threshold_exceeded:
            self._send_alert(task_pdu.task_type,metric_value)
    
    def _collect_metric(self,task_pdu):
        """Coleta a métrica específica da tarefa"""
        task_type = task_pdu.task_type
        metric_value = 0
        
        if task_type == 0: #CPU
            metric_value = int(psutil.cpu_percent())
        elif task_type == 1: #RAM
            metric_value = int(psutil.virtual_memory().percent)
        elif task_type == 2: # Latencia
            metric_value = self._execute_ping_task(task_pdu.payload)
        elif task_type == 3: #Throughput
            metric_value = self._execute_iperf_task(task_pdu.payload)
        elif task_type == 4: #Interface
            metric_value = self._execute_ip_task(task_pdu.payload)
            
        return metric_value
    
    def _execute_ping_task(self,payload):
        """Executa tarefa de ping"""
        frequency = payload.frequency.split(",")[0]
        result = subprocess.run(["ping", "-c", str(payload.count), "-i", frequency,
                                 payload.destination],capture_output=True,text=True)
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "avg" in line or "rtt" in line:
                    return int(float(line.split("/")[4]))
        return 0
    
    def _execute_iperf_task(self,payload):
        """Executa tarefa do iperf"""
        if payload.mode == "server":
            try:
                self.server_process = subprocess.Popen(
                    ["iperf3","-s"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return (0,0)
            except Exception as e:
                print(f"Erro ao iniciar o iperf no modo servidor: {e}")
                return (0,0) # (jitter, packet_loss) para servidor
        
        else: #client mode
            command = ["iperf3","-c",payload.server_ip, "-t",
                       str(payload.duration), "--json"]
            if payload.transport == "UDP":
                command.append("-u")
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                return self._parse_iperf_result(result.stdout,payload)
            return (0,0)
        
    def _execute_ip_task(self, payload):
        """Executa monitoramento de estatísticas de interfaces"""
        interfaces = payload.interface_stats  # Lista de interfaces no JSON
        stats = {}
    
        for iface in interfaces:
            try:
                # Verifica se a interface existe e coleta dados
                result = subprocess.run(["ip", "-s", "link", "show", "dev", iface], capture_output=True, text=True)
            
                if result.returncode == 0:
                    lines = result.stdout.splitlines()
                    iface_stats = {
                        "rx_packets": 0,
                        "tx_packets": 0,
                        "rx_errors": 0,
                        "tx_errors": 0
                    }
                
                    for i, line in enumerate(lines):
                        if "RX:" in line:  # Pacotes recebidos
                            iface_stats["rx_packets"] = int(lines[i+1].split()[0])
                            iface_stats["rx_errors"] = int(lines[i+1].split()[2])
                        elif "TX:" in line:  # Pacotes enviados
                            iface_stats["tx_packets"] = int(lines[i+1].split()[0])
                            iface_stats["tx_errors"] = int(lines[i+1].split()[2])
                
                    stats[iface] = iface_stats
                else:
                    print(f"[ERRO] Interface {iface} não encontrada ou inacessível")
            except Exception as e:
                print(f"[ERRO] Falha ao coletar estatísticas da interface {iface}: {e}")
    
        return stats  # Retorna um dicionário com as estatísticas das interfaces

        
    
    def _parse_iperf_result(self,stdout,payload):
        """Processa resultado do iperf em json para parse mais facil"""
        iperf_data = json.loads(stdout)
        if payload.transport == "UDP":
            jitter_value = float(iperf_data["end"]["streams"][0]["udp"]["jitter_ms"])
            packet_loss = float(iperf_data["end"]["streams"]["0"]["udp"]["lost_percent"])
            print(f"Jitter atual: {jitter_value} ms")
            print(f"Packet loss atual: {packet_loss}%")
            return (jitter_value,packet_loss)
        else:
            throughput = iperf_data["end"]["streams"][0]["receiver"]["bits_per_second"] / 1_000_000
            return (throughput,0) # apenas throughput para TCP
    
    def _check_threshold(self, task_pdu, metric_value):
        """verifica se o valor da métrica execedeu o threshold"""
        if hasattr(task_pdu.payload, 'threshold_value'):
            return metric_value > task_pdu.payload.threshold_value
        return False
    
    def _send_metric(self, task_type, metric_value, metric_subtype=None):
        """Envia metrica para o servidor"""
        try:
            seq_num = sequence_manager.get_next_seq_num(self.agent_id,5)
            metric_pdu = MetricPDU(
                msg_type=3,
                seq_num=seq_num,
                task_type=task_type,
                metric_value=int(metric_value)
            )   
        
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as metric_socket:
                self._send_with_retry(metric_socket,metric_pdu)
        
        except Exception as e:
            subtype_str = f" ({metric_subtype})" if metric_subtype else ""
            print(f"[ERROR] Erro ao enviar métrica{subtype_str}: {e}")
    
    def _send_alert(self, task_type, metric_value, metric_subtype=None):
        """Envia alerta para o servidor"""
        try:
            seq_num = sequence_manager.get_next_seq_num(self.agent_id, 5)
            alert_pdu = AlertPDU(
                msg_type=4,
                seq_num=seq_num,
                task_type=task_type,
                metric_value=int(metric_value)
            )
        
            ##subtype_str = f" ({metric_subtype})" if metric_subtype else ""
        
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as alert_socket:
                alert_socket.connect((self.server_ip, self.alert_port))
                alert_socket.sendall(alert_pdu.pack())
                print(f"Alerta enviado ao servidor com seq_num {alert_pdu.seq_num}")
            
                # Aguarda ACK do servidor
                try:
                    alert_socket.settimeout(5)
                    ack_data = alert_socket.recv(1024)
                    ack_message = AckPDU.unpack(ack_data)
                
                    if ack_message.seq_num == alert_pdu.seq_num:
                        print(f"[ACK RECEIVED] ACK recebido para o alerta")
                        print(f"  Seq num: {ack_message.seq_num}\n")
                    else:
                        print(f"[ERRO] ACK recebido com seq_num incorreto")
                    
                except socket.timeout:
                    print("[TIMEOUT] Não recebeu ACK para o alerta")
              
        except Exception as e:
            #subtype_str = f" ({metric_subtype})" if metric_subtype else ""
            print(f"Erro ao enviar o alerta: {e}") 

            
    def _send_with_retry(self, socket, pdu, max_attempts=3):
        """Envia PDU com tentativas de retransmissão"""
        attempt = 0
        while attempt < max_attempts:
            try:
                socket.settimeout(5)
                print(f"\n[METRIC SENT] Enviando métrica para o servidor")
                print(f"  Task type: {pdu.task_type}")
                print(f"  Metric value: {pdu.metric_value}")
                print(f"  Seq num: {pdu.seq_num}\n")
                
                socket.sendto(pdu.pack(), (self.server_ip, self.task_port))
                
                ack_data, _ = socket.recvfrom(1024)
                ack_message = AckPDU.unpack(ack_data)
                if ack_message.seq_num == pdu.seq_num:
                    print(f"[ACK RECEIVED] ACK recebido para a métrica")
                    print(f"  Seq num: {ack_message.seq_num}\n")
                    return True
                
            except socket.timeout:
                print(f"[TIMEOUT] Tentativa {attempt + 1} de envio da métrica")
                attempt += 1
                
        print("[ERROR] Falha ao receber confirmação da métrica após várias tentativas")
        return False
                