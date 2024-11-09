import json
import os
from nettask_pdu import NetTaskPDU
from server import get_next_seq_num
from cpu_payload import CPUPayload
from ram_payload import RAMPayload
from throughput_payload import ThroughputPayload
from latency_payload import LatencyPayload
from interface_payload import InterfacePayload

seq_numbers = {}

def load_tasks():
    file_path = os.path.join(os.path.dirname(__file__), "tasks.json")
    
    with open(file_path, 'r') as f:
        tasks_data = json.load(f)
        
    tasks = []
    
    for task in tasks_data['tasks']:
        for device in task['devices']:
            device_id = device['device_id']
            freq = task['frequency']
            
            # Processa cada tipo de tarefa com verificação de `alertflow_conditions`
            if "cpu_usage" in device['device_metrics'] and device['device_metrics']['cpu_usage'] == True:
                seq_num = get_next_seq_num(device_id)
                threshold = device['alertflow_conditions'].get('cpu_usage', 50)
                task_pdu = NetTaskPDU(msg_type=2, seq_num=seq_num, freq=freq, task_type=0, payload=CPUPayload(threshold_value=threshold))
                tasks.append((device_id, task_pdu))
            
            if "ram_usage" in device['device_metrics'] and device['device_metrics']['ram_usage'] == True:
                seq_num = get_next_seq_num(device_id)
                threshold = device['alertflow_conditions'].get('ram_usage', 50)
                task_pdu = NetTaskPDU(msg_type=2, seq_num=seq_num, freq=freq, task_type=1, payload=RAMPayload(threshold_value=threshold))
                tasks.append((device_id, task_pdu))
                
            # Verifica se `bandwidth` e `iperf` estão presentes antes de acessar
            if "bandwidth" in device['link_metrics'] and "iperf" in device['link_metrics']['bandwidth']:
                seq_num = get_next_seq_num(device_id)
                jitter_threshold = device['alertflow_conditions'].get('jitter', 100)
                iperf_data = device['link_metrics']['bandwidth']['iperf']
                mode = iperf_data.get('mode')
                server_ip = iperf_data.get('server_ip')
                transport = iperf_data.get('transport')
                duration = iperf_data.get('duration')
                if mode and server_ip and transport and duration is not None:
                    task_pdu = NetTaskPDU(msg_type=2, seq_num=seq_num, freq=freq, task_type=3, payload=ThroughputPayload(threshold_value=jitter_threshold, mode=mode, server_ip=server_ip, transport=transport, duration=duration))
                    tasks.append((device_id, task_pdu))
            
            # Verifica se `latency` e `ping` estão presentes antes de acessar
            if "latency" in device['link_metrics'] and "ping" in device['link_metrics']['latency']:
                seq_num = get_next_seq_num(device_id)
                packet_loss_threshold = device['alertflow_conditions'].get('packet_loss', 5)
                ping_data = device['link_metrics']['latency']['ping']
                destination = ping_data.get('destination')
                count = ping_data.get('count')
                frequency = ping_data.get('frequency')
                if destination and count is not None and frequency is not None:
                    task_pdu = NetTaskPDU(msg_type=2, seq_num=seq_num, freq=freq, task_type=2, payload=LatencyPayload(threshold_value=packet_loss_threshold, destination=destination, count=count, frequency=frequency))
                    tasks.append((device_id, task_pdu))
            
            if "interface_stats" in device['device_metrics']:
                seq_num = get_next_seq_num(device_id)
                interface_threshold = device['alertflow_conditions'].get('interface_stats', 1000)
                for interface_name in device['device_metrics']['interface_stats']:
                    task_pdu = NetTaskPDU(msg_type=2, seq_num=seq_num, freq=freq, task_type=4, payload=InterfacePayload(threshold_value=interface_threshold, interface_name=interface_name))
                    tasks.append((device_id, task_pdu))
                    
    return tasks

