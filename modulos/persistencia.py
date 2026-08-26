import json
import os

ARQUIVO = 'dados.json'

def carregar_dados():
    # Se o arquivo não existir, retorna uma lista vazia, sem caô.
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_dados(dados):
    # Salva os bagulhos com identação pra ficar bonitinho
    with open(ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4)




















