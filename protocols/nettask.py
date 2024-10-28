import socket
import threading
import json
import time
from queue import Queue
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

class NetTaskPacket:
    def __init__(self, 
                 packet_type: str,
                 seq_num: int,
                 ack_num: int,
                 data: dict,
                 window_size: int = 0):
        self.packet_type = packet_type  # 'DATA', 'ACK', 'REGISTER', 'TASK'
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data = data
        self.window_size = window_size
        self.timestamp = datetime.now().timestamp()

    def to_json(self) -> str:
        return json.dumps({
            'type': self.packet_type,
            'seq': self.seq_num,
            'ack': self.ack_num,
            'window': self.window_size,
            'data': self.data,
            'timestamp': self.timestamp
        })

    @staticmethod
    def from_json(json_str: str) -> 'NetTaskPacket':
        data = json.loads(json_str)
        packet = NetTaskPacket(
            data['type'],
            data['seq'],
            data['ack'],
            data['data'],
            data['window']
        )
        packet.timestamp = data['timestamp']
        return packet

class NetTaskProtocol:
    def __init__(self, socket: socket.socket, is_server: bool = False):
        self.socket = socket
        self.is_server = is_server
        self.sequence_number = 0
        self.expected_seq = 0
        self.window_size = 5  # Sliding window size
        self.timeout = 1.0    # Timeout in seconds
        
        # Buffers for sending and receiving
        self.send_buffer = Queue()
        self.receive_buffer: Dict[int, NetTaskPacket] = {}
        self.unacked_packets: Dict[int, Tuple[NetTaskPacket, float]] = {}
        
        # Flow control
        self.receiver_window = 5
        self.congestion_window = 1
        self.ssthresh = 16
        
        # Start worker threads
        self.running = True
        self.send_thread = threading.Thread(target=self._send_worker)
        self.receive_thread = threading.Thread(target=self._receive_worker)
        self.retransmit_thread = threading.Thread(target=self._retransmit_worker)
        
        self.send_thread.start()
        self.receive_thread.start()
        self.retransmit_thread.start()

    def send(self, data: dict, packet_type: str = 'DATA') -> None:
        """Enqueue data to be sent"""
        packet = NetTaskPacket(
            packet_type=packet_type,
            seq_num=self.sequence_number,
            ack_num=self.expected_seq,
            data=data,
            window_size=self.window_size
        )
        self.send_buffer.put(packet)
        self.sequence_number += 1

    def _send_worker(self) -> None:
        """Worker thread for sending packets"""
        while self.running:
            if not self.send_buffer.empty() and len(self.unacked_packets) < self.window_size:
                packet = self.send_buffer.get()
                self._send_packet(packet)
            time.sleep(0.01)

    def _send_packet(self, packet: NetTaskPacket) -> None:
        """Send a single packet and track it for potential retransmission"""
        try:
            data = packet.to_json().encode()
            if packet.packet_type != 'ACK':  # Don't track ACKs for retransmission
                self.unacked_packets[packet.seq_num] = (packet, time.time())
            self.socket.send(data)
        except Exception as e:
            print(f"Error sending packet: {e}")

    def _receive_worker(self) -> None:
        """Worker thread for receiving packets"""
        while self.running:
            try:
                data = self.socket.recv(4096)
                if data:
                    packet = NetTaskPacket.from_json(data.decode())
                    self._handle_packet(packet)
            except Exception as e:
                print(f"Error receiving packet: {e}")
                time.sleep(0.1)

    def _handle_packet(self, packet: NetTaskPacket) -> None:
        """Handle received packets based on type"""
        if packet.packet_type == 'ACK':
            self._handle_ack(packet)
        else:
            self._handle_data(packet)

    def _handle_ack(self, packet: NetTaskPacket) -> None:
        """Handle received ACK packets"""
        # Remove acknowledged packets from unacked_packets
        self.unacked_packets.pop(packet.ack_num, None)
        
        # Update flow control
        self.receiver_window = packet.window_size
        if self.congestion_window < self.ssthresh:
            # Slow start
            self.congestion_window += 1
        else:
            # Congestion avoidance
            self.congestion_window += 1 / self.congestion_window
        
        self.window_size = min(self.receiver_window, int(self.congestion_window))

    def _handle_data(self, packet: NetTaskPacket) -> None:
        """Handle received data packets"""
        # Send ACK
        ack_packet = NetTaskPacket(
            packet_type='ACK',
            seq_num=self.sequence_number,
            ack_num=packet.seq_num,
            data={},
            window_size=self.window_size
        )
        self._send_packet(ack_packet)
        
        # Store in receive buffer if in window
        if self.expected_seq <= packet.seq_num < self.expected_seq + self.window_size:
            self.receive_buffer[packet.seq_num] = packet
            
            # Process in-order packets
            while self.expected_seq in self.receive_buffer:
                received_packet = self.receive_buffer.pop(self.expected_seq)
                self._process_received_data(received_packet)
                self.expected_seq += 1

    def _retransmit_worker(self) -> None:
        """Worker thread for handling retransmissions"""
        while self.running:
            current_time = time.time()
            for seq_num, (packet, send_time) in list(self.unacked_packets.items()):
                if current_time - send_time > self.timeout:
                    # Packet timed out, retransmit
                    print(f"Retransmitting packet {seq_num}")
                    self._send_packet(packet)
                    # Update congestion control
                    self.ssthresh = max(2, int(self.congestion_window / 2))
                    self.congestion_window = 1
                    self.window_size = 1
            time.sleep(0.1)

    def _process_received_data(self, packet: NetTaskPacket) -> None:
        """Process received data (override in subclass)"""
        pass

    def close(self) -> None:
        """Clean shutdown of the protocol"""
        self.running = False
        self.send_thread.join()
        self.receive_thread.join()
        self.retransmit_thread.join()
