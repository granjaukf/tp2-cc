import json
import os
from datetime import datetime

class DataStorage:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Garante que os diretórios necessários existem"""
        directories = [
            self.base_dir,
            os.path.join(self.base_dir, "metrics"),
            os.path.join(self.base_dir, "alerts")
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def store_metric(self, device_id, task_type, metric_value, seq_num):
        """Armazena uma métrica recebida"""
        timestamp = datetime.now().isoformat()
        filename = os.path.join(self.base_dir, "metrics", f"{device_id.split()}.json")
    
        data = {
            "timestamp": timestamp,
            "task_type": task_type,
            "metric_value": metric_value,
            "seq_num": seq_num
        }
    
        self._append_to_file(filename, data)
    
    def store_alert(self, device_id, task_type, metric_value, seq_num):
        """Armazena um alerta recebido"""
        timestamp = datetime.now().isoformat()
        filename = os.path.join(self.base_dir, "alerts", f"{device_id.split()}.json")
        
        data = {
            "timestamp": timestamp,
            "task_type": task_type,
            "metric_value": metric_value,
            "seq_num": seq_num
        }
        
        self._append_to_file(filename, data)
        
    def _append_to_file(self, filename, data):
        """Adiciona dados a um arquivo JSON"""
        try:
            file_data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        content = f.read()
                        if content:
                            file_data = json.loads(content)
                            if not isinstance(file_data, list):
                                file_data = []
                except json.JSONDecodeError:
                    file_data = []
            
            file_data.append(data)
            
            with open(filename, 'w') as f:
                json.dump(file_data, f, indent=2)  # Usando dump em vez de dumps
                
        except Exception as e:
            print(f"[ERRO] Falha ao armazenar dados: {e}")

# Instância global do armazenamento de dados
data_storage = DataStorage()