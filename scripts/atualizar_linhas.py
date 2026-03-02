#!/usr/bin/env python3
"""
Gera data/linhas.json a partir do site da Piracicabana.

Fonte: loadLines.php retorna HTML com todas as linhas disponíveis.
Este script parseia esse HTML e salva o mapeamento em data/linhas.json.

Quando rodar:
  - Mensalmente (atualização preventiva)
  - Após reajuste de tarifas (geralmente janeiro)
  - Quando uma linha nova for criada ou desativada

Como rodar (de dentro da pasta emtu-go):
  python3 scripts/atualizar_linhas.py
"""

import json
import os
import sys
from urllib.parse import urlparse, parse_qs
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
BASE = "http://m.piracicabana.com.br/_versoes/3"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "data", "linhas.json")


def obter_html_linhas() -> str:
    """Faz a requisição ao servidor e retorna o HTML."""
    print("Buscando lista de linhas em loadLines.php...")
    try:
        resp = requests.post(
            f"{BASE}/parts/loadLines.php",
            data={"var_company": "0", "var_pesq": ""},
            headers={
                "User-Agent": UA,
                "Referer": "http://m.piracicabana.com.br/",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            timeout=10
        )
        resp.raise_for_status()
        return resp.text
    except RequestException as e:
        print(f"ERRO DE REDE: Não foi possível acessar o site da Piracicabana. Detalhes: {e}")
        sys.exit(1)


def extrair_dados_linhas(html: str) -> list:
    """Analisa o HTML e extrai a lista de dicionários com os dados das linhas."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Buscamos os containers que representam cada linha, independente se hoje é uma tag <a>
    elementos_linha = soup.find_all(class_="link-line")

    if not elementos_linha:
        print("ERRO: Nenhum elemento de linha encontrado — a estrutura do site pode ter mudado.")
        sys.exit(1)

    print(f"Encontrados {len(elementos_linha)} registros de linhas.")
    mapeamento = []

    for elemento in elementos_linha:
        # Extrai os metadados embutidos na URL/Ação de clique
        url_destino = elemento.get("href", "")
        parametros_url = parse_qs(urlparse(url_destino).query)
        lid = parametros_url.get("lid", [""])[0]
        cid = parametros_url.get("cid", [""])[0]

        # Extrai o ID interno do sistema da empresa
        container_var = elemento.find(class_="btn-inner-lines")
        var_linha = container_var.get("id", "") if container_var else ""

        # Extrai os dados visíveis ao passageiro
        elemento_numero = elemento.find(class_="line-id")
        numero = elemento_numero.text.strip() if elemento_numero else ""

        elemento_nome = elemento.find("b")
        nome = elemento_nome.text.strip() if elemento_nome else ""

        tarifa = ""
        for paragrafo in elemento.find_all("p"):
            if "R$" in paragrafo.text:
                tarifa = paragrafo.text.strip()
                break

        mapeamento.append({
            "numero": numero,
            "nome": nome,
            "tarifa": tarifa,
            "var_linha": var_linha,
            "lid": lid,
            "cid": cid,
        })

    return mapeamento


def salvar_json(dados: list, caminho_arquivo: str):
    """Salva o JSON apenas se a pasta de destino já existir."""
    caminho_final = os.path.normpath(caminho_arquivo)
    diretorio_destino = os.path.dirname(caminho_final)
    
    # Aborta sem fazer nada se a estrutura do projeto não estiver correta
    if not os.path.exists(diretorio_destino):
        print(f"ERRO: A pasta '{diretorio_destino}' não existe.")
        print("Certifique-se de que a estrutura do projeto está correta antes de salvar os dados.")
        sys.exit(1)

    with open(caminho_final, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Salvo com sucesso em {caminho_final}")


def validar_integridade(mapeamento: list):
    """Verifica anomalias estruturais nos dados extraídos."""
    erros = 0
    
    for linha in mapeamento:
        # Verifica se alguma linha veio sem as chaves fundamentais para o sistema funcionar
        if not linha.get("numero") or not linha.get("var_linha"):
            print(f"ATENÇÃO: Registro incompleto detectado: {linha}")
            erros += 1
            
        # Verifica se o parser da tarifa falhou
        if not linha.get("tarifa"):
            print(f"ATENÇÃO: Linha {linha.get('numero', 'Desconhecida')} sem tarifa detectada.")
            erros += 1

    if erros == 0:
        print("\nValidação: Dados estruturalmente íntegros.")
    else:
        print(f"\nValidação: {erros} alertas encontrados. Verifique o mapeamento gerado.")


def main():
    html = obter_html_linhas()
    mapeamento = extrair_dados_linhas(html)
    salvar_json(mapeamento, OUTPUT_PATH)
    
    print("\nVerifique o diff antes de commitar:")
    print("  git diff data/linhas.json")
    
    validar_integridade(mapeamento)


if __name__ == "__main__":
    main()