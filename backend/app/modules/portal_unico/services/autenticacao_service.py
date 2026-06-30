import os
import time

import requests


ROLE_TYPE = os.getenv("PORTAL_UNICO_ROLE_TYPE", "IMPEXP").strip()
AMBIENTE = os.getenv("PORTAL_UNICO_AMBIENTE", "producao").strip()

BASE_URL = "https://portalunico.siscomex.gov.br"

if AMBIENTE.lower() == "validacao":
    BASE_URL = "https://val.portalunico.siscomex.gov.br"


_TOKEN_CACHE = None
_TOKEN_TIME = None


def limpar_cache_token_portal_unico():
    global _TOKEN_CACHE, _TOKEN_TIME

    _TOKEN_CACHE = None
    _TOKEN_TIME = None


def _mensagem_erro_autenticacao(response: requests.Response) -> str:
    try:
        dados = response.json()
    except Exception:
        return response.text or "Erro não identificado na autenticação."

    if isinstance(dados, dict):
        mensagens = dados.get("message") or dados.get("mensagem")

        if isinstance(mensagens, list):
            return " | ".join(str(item) for item in mensagens)

        if mensagens:
            return str(mensagens)

    return "Erro retornado pelo Portal Único na autenticação."


def autenticar_portal_unico():
    global _TOKEN_CACHE, _TOKEN_TIME

    client_id = os.getenv("PORTAL_UNICO_CLIENT_ID", "").strip()
    client_secret = os.getenv("PORTAL_UNICO_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise ValueError(
            "Credenciais do Portal Único não configuradas no .env."
        )

    if _TOKEN_CACHE and _TOKEN_TIME:
        segundos = time.time() - _TOKEN_TIME

        if segundos < 58:
            return _TOKEN_CACHE

    url = f"{BASE_URL}/portal/api/autenticar/chave-acesso"

    headers = {
        "Client-Id": client_id,
        "Client-Secret": client_secret,
        "Role-Type": ROLE_TYPE,
        "Accept": "application/json",
    }

    response = requests.post(
        url,
        headers=headers,
        timeout=60,
    )

    if response.status_code == 422:
        if _TOKEN_CACHE:
            return _TOKEN_CACHE

        raise ValueError(
            "O Portal Único informou que já existe uma autenticação válida "
            "gerada recentemente. Aguarde alguns segundos e tente novamente."
        )

    if response.status_code not in [200, 201, 204]:
        raise ValueError(
            f"Erro ao autenticar no Portal Único: "
            f"{response.status_code} - {_mensagem_erro_autenticacao(response)}"
        )

    token = response.headers.get("Set-Token")
    csrf_token = response.headers.get("X-CSRF-Token")

    if not token:
        raise ValueError("Portal Único não retornou Set-Token.")

    _TOKEN_CACHE = {
        "Authorization": token,
        "X-CSRF-Token": csrf_token,
        "Role-Type": ROLE_TYPE,
        "Accept": "application/json",
    }

    _TOKEN_TIME = time.time()

    return _TOKEN_CACHE