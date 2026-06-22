import random
from datetime import datetime


def somente_numeros(valor) -> str:
    if not valor:
        return ""

    return "".join(filter(str.isdigit, str(valor)))


def gerar_codigo_mdf() -> str:
    return str(random.randint(1, 99999999)).zfill(8)


def calcular_dv_chave(chave_sem_dv: str) -> str:
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    peso_index = 0

    for numero in reversed(chave_sem_dv):
        soma += int(numero) * pesos[peso_index]
        peso_index += 1

        if peso_index == len(pesos):
            peso_index = 0

    resto = soma % 11
    dv = 11 - resto

    if dv >= 10:
        dv = 0

    return str(dv)


def gerar_chave_mdfe(
    cuf: int,
    data_emissao: datetime,
    cnpj_emitente: str,
    serie: int,
    numero: int,
    tp_emis: int = 1,
    c_mdf: str | None = None,
) -> dict:
    cnpj = somente_numeros(cnpj_emitente)

    if len(cnpj) != 14:
        raise ValueError("CNPJ do emitente inválido para geração da chave MDF-e.")

    if not c_mdf:
        c_mdf = gerar_codigo_mdf()

    c_mdf = somente_numeros(c_mdf).zfill(8)[-8:]

    chave_sem_dv = (
        str(cuf).zfill(2)
        + data_emissao.strftime("%y%m")
        + cnpj
        + "58"
        + str(serie).zfill(3)
        + str(numero).zfill(9)
        + str(tp_emis)
        + c_mdf
    )

    if len(chave_sem_dv) != 43:
        raise ValueError(
            f"Chave MDF-e sem DV inválida. Tamanho gerado: {len(chave_sem_dv)}."
        )

    dv = calcular_dv_chave(chave_sem_dv)
    chave = chave_sem_dv + dv

    return {
        "chave": chave,
        "cMDF": c_mdf,
        "cDV": dv,
    }