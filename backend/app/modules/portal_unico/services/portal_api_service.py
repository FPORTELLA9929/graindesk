import requests

from app.modules.portal_unico.services.autenticacao_service import (
    BASE_URL,
    autenticar_portal_unico,
)


def _mensagem_erro_portal(response: requests.Response) -> str:
    try:
        dados = response.json()
    except Exception:
        return response.text or "Erro não identificado no Portal Único."

    if isinstance(dados, dict):
        mensagem = dados.get("message") or dados.get("mensagem")

        if mensagem:
            return str(mensagem)

    return "Erro retornado pelo Portal Único."


def get_portal_unico(
    path: str,
    timeout: int = 180,
) -> dict | list:
    headers = autenticar_portal_unico()

    if not isinstance(headers, dict):
        raise ValueError(
            "Erro ao autenticar no Portal Único. "
            f"Retorno inválido da autenticação: {headers}"
        )

    if not headers.get("Authorization"):
        raise ValueError(
            "Erro ao autenticar no Portal Único. "
            "Header Authorization não foi gerado."
        )

    url = f"{BASE_URL}{path}"

    response = requests.get(
        url,
        headers=headers,
        timeout=timeout,
    )

    if response.status_code == 422:
        raise ValueError(
            "O Portal Único recusou uma nova autenticação porque já existe "
            "um token válido gerado recentemente. Aguarde alguns segundos e tente novamente."
        )

    if response.status_code in [401, 403]:
        raise ValueError(
            "A sessão do Portal Único expirou ou não possui autorização para esta consulta."
        )

    if response.status_code >= 400:
        raise ValueError(
            f"Erro ao consultar Portal Único: {response.status_code} - "
            f"{_mensagem_erro_portal(response)}"
        )

    try:
        return response.json()
    except Exception:
        raise ValueError(
            "Portal Único retornou uma resposta inválida ou vazia."
        )