from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.exportacao.services.rastreabilidade_service import (
    obter_rastreabilidade_entrada_por_chave,
)
from app.modules.portal_unico.services.peso_service import (
    normalizar_peso_portal_unico,
)
from app.modules.portal_unico.services.portal_api_service import get_portal_unico
from app.modules.portal_unico.services.tradutores_service import (
    extrair_numero_nf,
    traduzir_centro_origem_por_chave,
    traduzir_material,
    traduzir_recinto,
    traduzir_urf,
)


TAMANHO_LOTE = 25


def _decimal(valor, default: Decimal = Decimal("0")) -> Decimal:
    if valor in [None, ""]:
        return default

    try:
        return Decimal(str(valor).replace(",", "."))
    except Exception:
        return default


def consultar_lote_cct(chaves: list[str]) -> dict:
    lista_nfe = ",".join(chaves)

    path = (
        "/cct/api/ext/deposito-carga/"
        f"estoque-nota-fiscal/{lista_nfe}"
    )

    retorno = get_portal_unico(
        path=path,
        timeout=180,
    )

    if isinstance(retorno, list):
        return {
            "estoqueNotasFiscais": retorno,
            "mensagens": [],
        }

    if isinstance(retorno, dict):
        return retorno

    return {
        "estoqueNotasFiscais": [],
        "mensagens": [
            {
                "mensagem": f"Retorno inválido do Portal Único: {retorno}",
            }
        ],
        "erro": True,
        "retorno_original": retorno,
    }


def _mensagem_nota(nota: dict | None) -> str:
    if not nota:
        return ""

    mensagens = nota.get("mensagens", [])

    if not mensagens:
        return "Consulta realizada com sucesso"

    textos = []

    for msg in mensagens:
        if isinstance(msg, dict):
            textos.append(
                msg.get("message")
                or msg.get("mensagem")
                or msg.get("descricao")
                or str(msg)
            )
        else:
            textos.append(str(msg))

    return " | ".join(textos)


def _mensagem_retorno_lote(retorno: dict | None) -> str:
    if not retorno:
        return "Sem retorno do Portal Único."

    mensagens = retorno.get("mensagens", [])

    if not mensagens:
        return "Nota não localizada no Portal Único."

    textos = []

    for msg in mensagens:
        if isinstance(msg, dict):
            textos.append(
                msg.get("message")
                or msg.get("mensagem")
                or msg.get("descricao")
                or str(msg)
            )
        else:
            textos.append(str(msg))

    return " | ".join(textos) or "Nota não localizada no Portal Único."


def _obter_saldo_bruto_cct(nota: dict | None) -> Decimal:
    if not nota:
        return Decimal("0")

    saldo_principal = nota.get("saldo")

    if saldo_principal not in [None, ""]:
        return _decimal(saldo_principal)

    itens = nota.get("itens", [])

    if itens and isinstance(itens, list) and isinstance(itens[0], dict):
        saldo_item = itens[0].get("saldo")
        return _decimal(saldo_item)

    return Decimal("0")


def _obter_peso_nf_kg(nota: dict | None) -> Decimal:
    if not nota:
        return Decimal("0")

    return _decimal(nota.get("pesoAferido")).quantize(Decimal("1"))


def _historico_consumo(
    db: Session,
    chave: str,
) -> dict:
    return obter_rastreabilidade_entrada_por_chave(
        db=db,
        chave_nfe=chave,
    )


def consultar_notas_cct(
    db: Session,
    chaves: list[str],
) -> list[dict]:
    chaves = [
        "".join(filter(str.isdigit, str(chave)))
        for chave in chaves
        if str(chave).strip()
    ]

    chaves_validas = []
    resultados_invalidos = []

    for chave in chaves:
        if len(chave) != 44:
            resultados_invalidos.append(
                {
                    "chave": chave,
                    "numero_nfe": "-",
                    "centro_origem": "CHAVE INVÁLIDA",
                    "material": "-",
                    "peso_nf": Decimal("0"),
                    "peso_cct": Decimal("0"),
                    "saldo": Decimal("0"),
                    "porto": "-",
                    "recinto": "-",
                    "mensagem": "Chave de acesso inválida.",
                    "situacao": "Inválida",
                    "dados": None,
                    "historico_consumo": _historico_consumo(db, chave),
                }
            )
            continue

        if chave not in chaves_validas:
            chaves_validas.append(chave)

    resultado = resultados_invalidos

    for i in range(0, len(chaves_validas), TAMANHO_LOTE):
        lote = chaves_validas[i:i + TAMANHO_LOTE]

        retorno = consultar_lote_cct(lote)

        notas = retorno.get("estoqueNotasFiscais", [])

        if not isinstance(notas, list):
            notas = []

        encontrados = {
            nota.get("numero"): nota
            for nota in notas
            if isinstance(nota, dict) and nota.get("numero")
        }

        mensagem_lote = _mensagem_retorno_lote(retorno)

        for chave in lote:
            nota = encontrados.get(chave)

            if nota:
                ncm = nota.get("ncm")

                peso_nf = _obter_peso_nf_kg(nota)
                saldo_bruto_cct = _obter_saldo_bruto_cct(nota)

                saldo_cct = normalizar_peso_portal_unico(
                    db=db,
                    valor=saldo_bruto_cct,
                    ncm=ncm,
                )

                resultado.append(
                    {
                        "chave": chave,
                        "numero_nfe": extrair_numero_nf(chave),
                        "centro_origem": traduzir_centro_origem_por_chave(db, chave),
                        "material": traduzir_material(db, ncm),
                        "peso_nf": peso_nf,
                        "peso_cct": saldo_cct,
                        "saldo": saldo_cct,
                        "porto": traduzir_urf(db, nota.get("urf")),
                        "recinto": traduzir_recinto(db, nota.get("recinto")),
                        "mensagem": _mensagem_nota(nota),
                        "situacao": "OK",
                        "dados": nota,
                        "historico_consumo": _historico_consumo(db, chave),
                    }
                )
            else:
                resultado.append(
                    {
                        "chave": chave,
                        "numero_nfe": extrair_numero_nf(chave),
                        "centro_origem": traduzir_centro_origem_por_chave(db, chave),
                        "material": "NF NÃO ENCONTRADA",
                        "peso_nf": Decimal("0"),
                        "peso_cct": Decimal("0"),
                        "saldo": Decimal("0"),
                        "porto": "NF NÃO ENCONTRADA",
                        "recinto": "NF NÃO ENCONTRADA",
                        "mensagem": mensagem_lote,
                        "situacao": "NÃO ENCONTRADA",
                        "dados": retorno,
                        "historico_consumo": _historico_consumo(db, chave),
                    }
                )

    return resultado