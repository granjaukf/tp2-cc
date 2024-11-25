import socket
import subprocess
import json
import time
import psutil
from .sequence_manager import sequence_manager
from msg_type.metric_pdu import MetricPDU
from msg_type.ack_pdu import AckPDU
from msg_type.report_pdu import AlertPDU
from server.data_storage import data_storage


class TaskExecutor:
    def __init__(self, server_ip, alert_port, task_port, agent_id):
        self.server_ip = server_ip
        self.alert_port = alert_port
        self.task_port = task_port
        self.agent_id = agent_id

    
    def execute_task(self, task_pdu):
        """Executa uma tarefa e envia os resultados"""
        print("------------------------------")
        print(f"[EXECUTANDO TAREFA] Seq_num: {task_pdu.seq_num}")
        print(f"  Tipo: {task_pdu.task_type}")
        print("------------------------------")
    
        
        seq_num = task_pdu.seq_num
        metric_value =  self._collect_metric(task_pdu)
        
        self._send_metric(task_pdu.task_type,metric_value,seq_num)
        
        data_storage.store_metric(self.agent_id,task_pdu.task_type,metric_value,seq_num)

    

    
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
        elif task_type == 3:
            metric_value = self._execute_bandwidth_task(task_pdu.payload)
        elif task_type == 4:
            metric_value = self._execute_jitter_task(task_pdu.payload)
        elif task_type == 5: #Throughput
            metric_value = self._execute_packet_loss_task(task_pdu.payload)
        elif task_type == 6:
            metric_value = self._execute_interfaces_task(task_pdu.payload)
    
            
        return metric_value
    
    def _execute_ping_task(self, payload):
        """Executa tarefa de ping"""
    
        frequency = payload.frequency.split(",")[0]
        command = ["ping", "-c", str(payload.count), "-i", frequency, payload.destination]
        print(f"A executar comando ping: {' '.join(command)}")
    
        result = subprocess.run(command, capture_output=True, text=True)
    
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "avg" in line or "rtt" in line:
                    value = int(float(line.split("/")[4]))
                    print(f"Valor de latência obtido: {value}ms")
                    return value
        else:
            print(f"[ERROR] Comando ping falhou: {result.stderr}")
        return 0

    
    def _execute_bandwidth_task(self, payload):
        """Executa tarefa para coletar apenas a largura de banda no cliente"""
        
        print("[INFO] A executar o iperf no modo cliente para bandwidth")
        command = ["iperf3", "-c", payload.server_ip, "-t", "3", "--json"]
        if payload.transport == "TCP":
            command.append("-R")

        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                iperf_data = json.loads(result.stdout)
                throughput_bps = iperf_data["end"]["streams"][0]["receiver"]["bits_per_second"]
                throughput_mbps = throughput_bps / 1_000_000
                print(f"[BANDWIDTH] Throughput: {throughput_mbps} Mbps")
                return throughput_mbps
            else:
                print(f"[ERROR] Erro ao executar iperf para bandwidth: {result.stderr}")
                return 0
        except json.JSONDecodeError as e:
            print(f"[ERROR] Falha ao interpretar o resultado JSON do iperf: {e}")
            return 0
        except Exception as e:
            print(f"[ERROR] Falha ao executar iperf para bandwidth: {e}")
            return 0
        
        

    
    def _execute_jitter_task(self, payload):
        """Executa tarefa para coletar apenas jitter no cliente"""
        
        print("[INFO] A executar o iperf no modo cliente para jitter")
        command = ["iperf3", "-c", payload.server_ip, "-u", "-t", "3", "--json"]

        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                iperf_data = json.loads(result.stdout)
                jitter_value = float(iperf_data["end"]["streams"][0]["udp"]["jitter_ms"])
                print(f"[JITTER] Jitter atual: {jitter_value} ms")
                return jitter_value
            else:
                print(f"[ERROR] Erro ao executar iperf para jitter: {result.stderr}")
                return 0
        except Exception as e:
            print(f"[ERROR] Falha ao executar iperf para jitter: {e}")
            return 0



    def _execute_packet_loss_task(self, payload):
        """Executa tarefa para coletar apenas perda de pacotes no cliente"""

        print("[INFO] A executar o iperf no modo cliente para perda de pacotes")
        command = ["iperf3", "-c", payload.server_ip, "-u", "-t", "3", "--json"]

        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                iperf_data = json.loads(result.stdout)
                packet_loss = float(iperf_data["end"]["streams"][0]["udp"]["lost_percent"])
                print(f"[PACKET LOSS] Packet Loss atual: {packet_loss}%")
                return packet_loss
            else:
                print(f"[ERROR] Erro ao executar iperf para perda de pacotes: {result.stderr}")
                return 0
        except Exception as e:
            print(f"[ERROR] Falha ao executar iperf para perda de pacotes: {e}")
            return 0
        
    def _execute_interfaces_task(self, payload):
        """Executa a tarefa para coletar estatísticas de pacotes da interface"""
        interface_name = payload.interface_name.strip()
        path = f"/sys/class/net/{interface_name}/statistics/rx_packets"
        print(f"[DEBUG] Verificando estatísticas da interface: {path}")

        try:
            with open(path, "r") as file:
                rx_packets = int(file.read().strip())
                print(f"[INTERFACE STATS] Interface: {interface_name} | RX Packets: {rx_packets}")
                return rx_packets
        except FileNotFoundError:
            print(f"[ERROR] Arquivo {path} não encontrado. Verifique se a interface {interface_name} existe.")
            return 0
        except PermissionError:
            print(f"[ERROR] Permissão negada para acessar {path}. Execute o programa com privilégios suficientes.")
            return 0
        except ValueError:
            print(f"[ERROR] Valor inválido ao tentar ler RX packets da interface {interface_name}.")
            return 0
        except Exception as e:
            print(f"[ERROR] Falha ao coletar estatísticas da interface {interface_name}: {e}")
            return 0


    
    def _check_threshold(self, task_pdu, metric_value):
        """verifica se o valor da métrica execedeu o threshold"""
        if hasattr(task_pdu.payload, 'threshold_value'):
            return metric_value > task_pdu.payload.threshold_value
        return False
    
    def _send_metric(self, task_type, metric_value, seq_num):
        """Envia métrica para o servidor"""
        try:
        
            # Arredonda o valor da métrica
            rounded_value = round(metric_value, 4)

            # Cria a PDU da métrica
            metric_pdu = MetricPDU(
                msg_type=3,
                seq_num=seq_num,
                task_type=task_type,
                metric_value=rounded_value
            )

            # Envia a métrica usando o socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as metric_socket:
                self._send_with_retry(metric_socket, metric_pdu)
        except BaseException as e: 
            print(f"[ERROR] Falha ao enviar métrica: {e}")

    
    def _send_alert(self, task_type, metric_value,seq_num, metric_subtype=None):
        """Envia alerta para o servidor"""
        try:
            alert_pdu = AlertPDU(
                msg_type=4,
                seq_num=seq_num,
                task_type=task_type,
                metric_value=int(metric_value)
            )
        
        
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as alert_socket:
                alert_socket.connect((self.server_ip, self.alert_port))
                alert_socket.sendall(alert_pdu.pack())
                subtype_str = f" ({metric_subtype})" if metric_subtype else ""
                print(f"Alerta{subtype_str}enviado ao servidor com seq_num {alert_pdu.seq_num}")
            
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
                