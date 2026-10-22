"""Persistência dos domínios monitorados pelo aplicativo."""

import json
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO = PASTA_PROJETO / "dados.json"


def carregar_dados():
    if not ARQUIVO.exists():
        return []
    try:
        with ARQUIVO.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def salvar_dados(dados):
    with ARQUIVO.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)
