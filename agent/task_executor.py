import socket
import subprocess
import json
import psutil
from .sequence_manager import sequence_manager
from msg_type.metric_pdu import MetricPDU
from msg_type.ack_pdu import AckPDU
from msg_type.report_pdu import AlertPDU
from server.data_storage import data_storage
import time


class TaskExecutor:
    def __init__(self, server_ip, alert_port, task_port, agent_id, iperf_port=5202):
        self.server_ip = server_ip
        self.alert_port = alert_port
        self.task_port = task_port
        self.agent_id = agent_id
        self.iperf_port = iperf_port

    
    def execute_task(self, task_pdu, seq_num):
        """Executa uma tarefa e envia os resultados"""
        print("------------------------------")
        print(f"[A EXECUTAR TAREFA] Seq_num: {task_pdu.seq_num}")
        print(f"  Tipo: {task_pdu.task_type}")
        print("------------------------------")
    
        
        #seq_num = task_pdu.seq_num
        metric_value = self._collect_metric(task_pdu)
        
        self._send_metric(task_pdu.task_type,metric_value,seq_num)

        if self._check_threshold(task_pdu, metric_value) == True:
            self._send_alert(task_pdu.task_type, metric_value, seq_num)
            data_storage.store_alert(self.agent_id, task_pdu.task_type, metric_value, seq_num)

        if metric_value != 0 or task_pdu.task_type == 6:
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
        elif task_type in [3,4,5]:
            if task_pdu.payload.transport == "TCP" and task_type in [4,5]:
                print("[IPERF] As tarefas 4 e 5 não executam numa conexão TCP \n")
                time.sleep(10)
                return metric_value
            metrics = self._execute_iperf_metrics(task_pdu.payload)
            if task_type == 3:
                metric_value = metrics[0]
            if task_type == 4:
                metric_value = metrics[1]
            if task_type == 5:
                metric_value = metrics[2]
        elif task_type == 6:
            metric_value = self._execute_pps_task(task_pdu.payload)
    
            
        return metric_value

    
    
    def _execute_iperf_metrics(self, payload):
        """Executa o iperf e retorna tupla (bandwidth, jitter, packet_loss)"""

        if payload.mode == "server":
            print("[IPERF] Executar no modo servidor, não executa o comando cliente.\n")
            time.sleep(5)
            return (0, 0, 0)

        server_ip = payload.server_ip
        transport = payload.transport
        iperf_port = self.iperf_port

        success = False

        try:
            command = [
                "iperf3",
                "-c", server_ip,
                "-p", str(iperf_port),
            ]
            if transport == "UDP":
                command.append("-u")
            command.extend(["-t", "3", "--json"])

            print(f"[IPERF] A executar comando: {' '.join(command)}")

            while not success:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    success = True
                    data = json.loads(result.stdout)
                    if transport == "TCP":
                        try:
                            bandwidth = data["end"]["sum_sent"]["bits_per_second"] / 1_000_000  # Converte para Mbps
                            print(f"[IPERF RESULTS] Bandwidth: {bandwidth:.2f} Mbps")
                            return (bandwidth, 0, 0)
                        except (KeyError, ValueError) as e:
                            print(f"[ERROR] Falha ao processar resultado TCP: {e}")
                            return (0, 0, 0)
                    elif transport == "UDP":
                        try:
                            udp_data = data["end"]["streams"][0]["udp"]
                            bandwidth = udp_data["bits_per_second"] / 1_000_000  # Converte para Mbps
                            jitter = udp_data["jitter_ms"]
                            packet_loss = udp_data["lost_percent"]

                            print(f"[IPERF RESULTS]")
                            print(f"  Bandwidth: {bandwidth:.2f} Mbps")
                            print(f"  Jitter: {jitter:.2f} ms")
                            print(f"  Packet Loss: {packet_loss:.2f}%")

                            return (bandwidth, jitter, packet_loss)
                        except (KeyError, ValueError) as e:
                            print(f"[ERROR] Falha ao processar resultado UDP: {e}")
                            return (0, 0, 0)

            print("[ERROR] Todas as tentativas de iperf3 falharam.")
            return (0, 0, 0)

        except Exception as e:
            print(f"[ERROR] Exceção ao executar iperf: {e}")
            return (0, 0, 0)

    
    
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
        
    def _execute_pps_task(self, payload):
        interface = payload.interface_name.strip()
        try:
        # Obter dados iniciais
            dados_iniciais = psutil.net_io_counters(pernic=True).get(interface)
            if not dados_iniciais:
                print(f"Interface '{interface}' não encontrada!")
                return
        
            pacotes_recebidos_anterior = dados_iniciais.packets_recv

            while True:
                time.sleep(5)
                # Obter dados atuais
                dados_atual = psutil.net_io_counters(pernic=True).get(interface)
                pacotes_recebidos_atual = dados_atual.packets_recv

                # Calcular a diferença
                pacotes_por_segundo = (pacotes_recebidos_atual - pacotes_recebidos_anterior)/5

                pacotes_por_segundo = int(pacotes_por_segundo)

                print(f"Pacotes recebidos por segundo: {pacotes_por_segundo:.2f}")

                return pacotes_por_segundo

        except Exception as e:
            print(f"Erro: {e}")
            return 0


    
    def _check_threshold(self, task_pdu, metric_value):
        """verifica se o valor da métrica execedeu o threshold"""
        if hasattr(task_pdu.payload, 'threshold_value'):
            return metric_value > task_pdu.payload.threshold_value
        return False
    
    def _send_metric(self, task_type, metric_value, seq_num):
        """Envia métrica para o servidor com tentativas de retransmissão"""
        try:
            # Arredonda o valor da métrica
            rounded_value = round(metric_value, 3)

            # Cria o PDU da métrica
            metric_pdu = MetricPDU(
                msg_type=3,
                seq_num=seq_num,
                task_type=task_type,
                metric_value=rounded_value
            )

            # Envia a métrica através do socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as metric_socket:
                attempt = 0
                max_attempts = 3
                while attempt < max_attempts:
                    try:
                        metric_socket.settimeout(5)
                        print(f"\n[METRIC SENT] A enviar métrica para o servidor")
                        print(f"  Task type: {metric_pdu.task_type}")
                        print(f"  Metric value: {metric_pdu.metric_value}")
                        print(f"  Seq num: {metric_pdu.seq_num}\n")

                        metric_socket.sendto(metric_pdu.pack(), (self.server_ip, self.task_port))

                        ack_data, _ = metric_socket.recvfrom(1024)
                        ack_message = AckPDU.unpack(ack_data)
                        if ack_message.seq_num == metric_pdu.seq_num:
                            print(f"[ACK RECEIVED] ACK recebido para a métrica")
                            print(f"  Seq num: {ack_message.seq_num}\n")
                            return True

                    except socket.timeout:
                        print(f"[TIMEOUT] Tentativa {attempt + 1} de envio da métrica")
                        attempt += 1

                print("[ERROR] Falha ao receber confirmação da métrica após várias tentativas")
                return False

        except Exception as e:
            print(f"[ERROR] Falha ao enviar métrica: {e}")


    
    def _send_alert(self, task_type, metric_value,seq_num):
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
                print(f"Alerta enviado ao servidor com seq_num {alert_pdu.seq_num}")  
        except Exception as e:
            print(f"Erro ao enviar o alerta: {e}")