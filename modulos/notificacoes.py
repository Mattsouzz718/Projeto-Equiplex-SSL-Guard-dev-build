"""Notificações nativas do Windows."""

import sys
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ICONE_NOTIFICACAO = PASTA_PROJETO / "icone_bandeja.png"

def enviar_notificacao_windows(titulo, mensagem):
    """Envia uma notificação nativa do Windows 10/11, quando disponível."""
    if sys.platform != "win32":
        return False
    try:
        from winotify import Notification

        notificacao = Notification(
            app_id="Equiplex SSL Guard",
            title=titulo,
            msg=mensagem,
            icon=str(ICONE_NOTIFICACAO) if ICONE_NOTIFICACAO.exists() else "",
            duration="long",
        )
        notificacao.show()
        return True
    except Exception as erro:
        # A falha é registrada no terminal; nenhum popup alternativo é exibido.
        print(f"Não foi possível enviar a notificação do Windows: {erro}")
        return False
