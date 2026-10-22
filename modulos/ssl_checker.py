"""Consulta validade do certificado HTTPS e localização aproximada do IP."""

import socket
import ssl
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests
from cryptography import x509


GEO_CACHE_SECONDS = 24 * 60 * 60
_GEO_CACHE = {}
_GEO_LOCK = threading.Lock()


def normalizar_dominio(dominio):
    """Aceita domínio puro ou URL completa e devolve apenas o hostname."""
    valor = (dominio or "").strip()
    if not valor:
        return ""

    if "://" not in valor:
        valor = "//" + valor

    partes = urlsplit(valor)
    hostname = partes.hostname
    if hostname:
        return hostname.strip().rstrip(".")

    # Fallback para entradas simples sem esquema.
    return valor.removeprefix("//").split("/")[0].strip().rstrip(".")


def _localizar_ip(ip):
    """Retorna localização aproximada do IP, com cache para poupar consultas."""
    agora = time.time()
    with _GEO_LOCK:
        item = _GEO_CACHE.get(ip)
        if item and agora - item["consultado_em"] < GEO_CACHE_SECONDS:
            return dict(item["dados"])

    dados = {
        "cidade": None,
        "regiao": None,
        "pais": None,
        "provedor": None,
    }
    try:
        resposta = requests.get(
            f"https://ipapi.co/{ip}/json/",
            timeout=5,
            headers={"User-Agent": "Equiplex-SSL-Guard/1.1"},
        )
        resposta.raise_for_status()
        info = resposta.json()
        if not info.get("error"):
            dados.update({
                "cidade": info.get("city"),
                "regiao": info.get("region"),
                "pais": info.get("country_name") or info.get("country_name_en"),
                "provedor": info.get("org"),
            })
    except (requests.RequestException, ValueError, TypeError):
        # A falha de geolocalização não deve impedir a verificação do SSL.
        pass

    if any(dados.values()):
        with _GEO_LOCK:
            _GEO_CACHE[ip] = {"consultado_em": agora, "dados": dict(dados)}
    return dados


def verificar_dominio(dominio, timeout=5):
    """Consulta certificado, prazo restante, IP conectado e geolocalização.

    O contexto TLS é usado sem validação da cadeia para conseguir ler também
    certificados expirados. Portanto, este módulo verifica o prazo do
    certificado, não substitui uma auditoria completa de confiança TLS.
    """
    hostname = normalizar_dominio(dominio)
    resultado = {
        "dominio": hostname,
        "dias": -999,
        "expiracao": None,
        "ip": None,
        "cidade": None,
        "regiao": None,
        "pais": None,
        "provedor": None,
        "erro": None,
    }

    if not hostname:
        resultado["erro"] = "Domínio vazio."
        return resultado

    try:
        enderecos = socket.getaddrinfo(
            hostname, 443, type=socket.SOCK_STREAM
        )
    except (socket.gaierror, OSError) as erro:
        resultado["erro"] = f"Não foi possível localizar o domínio: {erro}"
        return resultado

    # Não valida a cadeia do certificado, pois precisamos ler sua data mesmo
    # quando já venceu. O hostname continua sendo enviado via SNI.
    contexto = ssl._create_unverified_context()
    erros_conexao = []
    certificado = None
    certificado_der = None
    ip_conectado = None

    for familia, tipo, protocolo, _, endereco in enderecos:
        sock = None
        tls_sock = None
        try:
            sock = socket.socket(familia, tipo, protocolo)
            sock.settimeout(timeout)
            sock.connect(endereco)
            tls_sock = contexto.wrap_socket(sock, server_hostname=hostname)
            sock = None  # O socket agora pertence ao TLS.
            certificado_der = tls_sock.getpeercert(binary_form=True)
            ip_conectado = tls_sock.getpeername()[0].split("%")[0]
            tls_sock.close()
            tls_sock = None
            if certificado_der:
                break
        except (OSError, ssl.SSLError, ValueError) as erro:
            erros_conexao.append(str(erro))
        finally:
            if tls_sock is not None:
                try:
                    tls_sock.close()
                except OSError:
                    pass
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    if not certificado_der:
        resultado["erro"] = (
            "Não foi possível obter o certificado HTTPS. "
            + (erros_conexao[-1] if erros_conexao else "O servidor não apresentou certificado.")
        )
        return resultado

    resultado["ip"] = ip_conectado
    try:
        certificado = x509.load_der_x509_certificate(certificado_der)
        expiracao = getattr(certificado, "not_valid_after_utc", None)
        if expiracao is None:  # Compatibilidade com versões antigas da cryptography.
            expiracao = certificado.not_valid_after.replace(tzinfo=timezone.utc)
        agora = datetime.now(timezone.utc)
        resultado["expiracao"] = expiracao
        resultado["dias"] = int((expiracao - agora).total_seconds() // 86400)
    except (KeyError, ValueError, TypeError) as erro:
        resultado["erro"] = f"Não foi possível interpretar a validade: {erro}"
        return resultado

    if ip_conectado:
        resultado.update(_localizar_ip(ip_conectado))

    return resultado


def verificar_ssl(dominio):
    """Compatibilidade com versões anteriores do projeto: retorna os dias."""
    return verificar_dominio(dominio)["dias"]
