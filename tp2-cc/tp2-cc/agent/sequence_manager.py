from threading import Lock

class SequenceManager:
    def __init__(self):
        self.last_seq_nums = {}
        self.lock = Lock()

    def get_next_seq_num(self, device_id, increment):
        """Gera o próximo número de sequência para um dispositivo"""
        with self.lock:
            if device_id not in self.last_seq_nums:
                self.last_seq_nums[device_id] = 0
            self.last_seq_nums[device_id] += increment
            return self.last_seq_nums[device_id]

    def validate_seq_num(self, device_id, seq_num):
        """Valida se o número de sequência é válido para o dispositivo"""
        with self.lock:
            if device_id in self.last_seq_nums and seq_num <= self.last_seq_nums[device_id]:
                print(f"\n[ERRO] `seq_num` não sequencial recebido de {device_id}. Ignorando a mensagem.\n")
                return False
            self.last_seq_nums[device_id] = seq_num
            return True

# Instância global do gerenciador de sequência
sequence_manager = SequenceManager()

def get_next_seq_num(device_id, increment):
    return sequence_manager.get_next_seq_num(device_id, increment)

def validate_seq_num(device_id, seq_num):
    return sequence_manager.validate_seq_num(device_id, seq_num)