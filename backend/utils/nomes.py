def nome_abreviado(nome: str) -> str:
    if not nome:
        return ""

    partes = nome.strip().split()

    if len(partes) == 1:
        return partes[0]

    if len(partes) == 2:
        return f"{partes[0]} {partes[1]}"

    return f"{partes[0]} {partes[1][0]}. {partes[-1]}"


def iniciais_nome(nome: str) -> str:
    if not nome:
        return "U"

    partes = nome.strip().split()

    if len(partes) == 1:
        return partes[0][0].upper()

    return f"{partes[0][0]}{partes[-1][0]}".upper()