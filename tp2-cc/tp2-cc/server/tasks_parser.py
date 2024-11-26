import json
import os
from typing import List, Tuple
from msg_type.nettask_pdu import NetTaskPDU
from tasks_payload.cpu_payload import CPUPayload
from tasks_payload.ram_payload import RAMPayload
from tasks_payload.bandwidth_payload import BandwidthPayload
from tasks_payload.latency_payload import LatencyPayload
from tasks_payload.interface_payload import InterfacePayload
from tasks_payload.jitter_payload import JitterPayload
from tasks_payload.packet_loss_payload import PacketLossPayload

def load_tasks() -> List[Tuple[str, NetTaskPDU]]:
    """Carrega e retorna a lista de tarefas do arquivo JSON"""
    file_path = os.path.join(os.path.dirname(__file__), "tasks.json")
    
    with open(file_path, 'r') as f:
        tasks_data = json.load(f)
        
    tasks = []
    
    for task in tasks_data['tasks']:
        for device in task['devices']:
            device_id = device['device_id']
            freq = task['frequency']
            
            # Processa tarefas de CPU
            if "cpu_usage" in device['device_metrics'] and device['device_metrics']['cpu_usage'] == True:
                threshold = device['alertflow_conditions'].get('cpu_usage', 50)
                task_pdu = NetTaskPDU(
                    msg_type=2, 
                    seq_num=0,  # seq_num sera atualizado no task_manager
                    freq=freq, 
                    task_type=0, 
                    payload=CPUPayload(threshold_value=threshold)
                )
                tasks.append((device_id, task_pdu))
            
            # Processa tarefas de RAM
            if "ram_usage" in device['device_metrics'] and device['device_metrics']['ram_usage'] == True:
                threshold = device['alertflow_conditions'].get('ram_usage', 50)
                task_pdu = NetTaskPDU(
                    msg_type=2, 
                    seq_num=0, 
                    freq=freq, 
                    task_type=1, 
                    payload=RAMPayload(threshold_value=threshold)
                )
                tasks.append((device_id, task_pdu))
                
            # Processa tarefas de latência (ping)
            if "latency" in device['link_metrics'] and "ping" in device['link_metrics']['latency']:
                ping_threshold = 100
                ping_data = device['link_metrics']['latency']['ping']
                destination = ping_data.get('destination')
                count = ping_data.get('count')
                frequency = ping_data.get('frequency')
                
                if destination and count is not None and frequency is not None:
                    task_pdu = NetTaskPDU(
                        msg_type=2, 
                        seq_num=0, 
                        freq=freq, 
                        task_type=2, 
                        payload=LatencyPayload(
                            threshold_value=ping_threshold,
                            destination=destination,
                            count=count,
                            frequency=frequency
                        )
                    )
                    tasks.append((device_id, task_pdu))
            
                
                
            # Processa tarefas de bandwidth (iperf)
            if "bandwidth" in device['link_metrics'] and "iperf" in device['link_metrics']['bandwidth']:
                iperf_data = device['link_metrics']['bandwidth']['iperf']
                mode = iperf_data.get('mode')
                server_ip = iperf_data.get('server_ip')
                transport = iperf_data.get('transport')
                duration = iperf_data.get('duration')
                threshold = 100
                
                
                if mode and server_ip and transport and duration is not None:
                    task_pdu = NetTaskPDU(
                        msg_type=2, 
                        seq_num=0, 
                        freq=freq, 
                        task_type=3, 
                        payload=BandwidthPayload(
                            mode=mode,
                            server_ip=server_ip,
                            transport=transport,
                            duration=duration,
                            threshold_value = threshold
                        )
                    )
                    tasks.append((device_id, task_pdu))
                    
            if "bandwidth" in device['link_metrics'] and "iperf" in device['link_metrics']['bandwidth']:
                iperf_data = device['link_metrics']['bandwidth']['iperf']
                mode = iperf_data.get('mode')
                server_ip = iperf_data.get('server_ip')
                transport = iperf_data.get('transport')
                duration = iperf_data.get('duration')
                threshold = device['alertflow_conditions'].get('jitter')
                
                if mode and server_ip and transport and duration is not None:
                    task_pdu = NetTaskPDU(
                        msg_type=2,
                        seq_num=0,
                        freq=freq,
                        task_type=4,
                        payload=JitterPayload(mode,server_ip,transport,duration,threshold)
                        
                    )
                    tasks.append((device_id,task_pdu))

            if "bandwidth" in device['link_metrics'] and "iperf" in device['link_metrics']['bandwidth']:
                iperf_data = device['link_metrics']['bandwidth']['iperf']
                mode = iperf_data.get('mode')
                server_ip = iperf_data.get('server_ip')
                transport = iperf_data.get('transport')
                duration = iperf_data.get('duration')
                threshold = device['alertflow_conditions'].get('packet_loss')
                
                if mode and server_ip and transport and duration is not None:
                    task_pdu = NetTaskPDU(
                        msg_type=2,
                        seq_num=0,
                        freq=freq,
                        task_type=5,
                        payload= PacketLossPayload(mode,server_ip,transport,duration,threshold)
                        
                    )
                    tasks.append((device_id,task_pdu))
            
            
            # Processa tarefas de interface
            if "interface_stats" in device['device_metrics']:
                interface_threshold = device['alertflow_conditions'].get('interface_stats', 1000)
                for interface_name in device['device_metrics']['interface_stats']:
                    task_pdu = NetTaskPDU(
                        msg_type=2, 
                        seq_num=0, 
                        freq=freq, 
                        task_type=6, 
                        payload=InterfacePayload(
                            threshold_value=interface_threshold, 
                            interface_name=interface_name
                        )
                    )
                    tasks.append((device_id, task_pdu))

    return tasks