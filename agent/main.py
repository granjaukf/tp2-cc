import argparse
from .agent_manager import start_agent

def main():
    
    parser = argparse.ArgumentParser(description="Agente para enviar RegisterPDU para o servidor.")
    parser.add_argument("host",type=str,help="Endereço IP do servidor.")
    parser.add_argument("--alert_port", type=int, default=12346,help="Porta para envio de alertas ao servidor")
    
    args = parser.parse_args()
    
    start_agent(args.host,alert_port=args.alert_port)
    
if __name__ == "__main__":
    main()
    