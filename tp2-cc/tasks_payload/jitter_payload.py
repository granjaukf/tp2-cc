from .bandwidth_payload import BandwidthPayload

class JitterPayload(BandwidthPayload):
    def __init__(self,mode,server_ip,transport,duration,threshold_value):
        super().__init__(mode, server_ip,transport,duration,threshold_value)
      
        