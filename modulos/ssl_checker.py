import ssl
import socket
from datetime import datetime

def verificar_ssl(dominio):
    # Limpa a string caso o usuário seja burro e coloque http://
    hostname = dominio.replace("https://", "").replace("http://", "").split('/')[0]
    context = ssl.create_default_context()
    
    try:
        # Tenta conectar na porta 443 com timeout de 5 segs
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                # Pega a data de expiração e converte
                data_expiracao = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                hoje = datetime.utcnow()
                dias_restantes = (data_expiracao - hoje).days
                
                return dias_restantes
    except Exception as e:
        return -999 # Código de erro pra quando o site cair ou der BO











