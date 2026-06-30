from app.modules.admin.models.portal_unico_material import PortalUnicoMaterial
from app.modules.admin.models.portal_unico_urf import PortalUnicoURF
from app.modules.admin.models.portal_unico_recinto import PortalUnicoRecinto
from app.modules.cadastros.models.empresa import Empresa


def limpar_cnpj(valor: str | None) -> str:
    return "".join(filter(str.isdigit, str(valor or "")))


def extrair_cnpj_emitente_da_chave(chave: str) -> str:
    chave = "".join(filter(str.isdigit, str(chave or "")))

    if len(chave) != 44:
        return ""

    return chave[6:20]


def extrair_numero_nf(chave: str) -> str:
    chave = "".join(filter(str.isdigit, str(chave or "")))

    if len(chave) != 44:
        return "-"

    numero = chave[25:34]

    try:
        return str(int(numero))
    except Exception:
        return numero


def traduzir_material(db, ncm: str | None) -> str:
    ncm = str(ncm or "").strip()

    if not ncm:
        return "NCM NÃO INFORMADO"

    material = (
        db.query(PortalUnicoMaterial)
        .filter(
            PortalUnicoMaterial.ncm == ncm,
            PortalUnicoMaterial.ativo == True,
        )
        .first()
    )

    if material:
        return material.descricao

    return f"NCM {ncm}"


def traduzir_urf(db, codigo: str | None) -> str:
    codigo = str(codigo or "").strip()

    if not codigo:
        return "URF NÃO INFORMADA"

    urf = (
        db.query(PortalUnicoURF)
        .filter(
            PortalUnicoURF.codigo == codigo,
            PortalUnicoURF.ativo == True,
        )
        .first()
    )

    if urf:
        return urf.descricao

    return f"URF {codigo}"


def traduzir_recinto(db, codigo: str | None) -> str:
    codigo = str(codigo or "").strip()

    if not codigo:
        return "RECINTO NÃO INFORMADO"

    recinto = (
        db.query(PortalUnicoRecinto)
        .filter(
            PortalUnicoRecinto.codigo == codigo,
            PortalUnicoRecinto.ativo == True,
        )
        .first()
    )

    if recinto:
        return recinto.descricao

    return f"RECINTO {codigo} NÃO CADASTRADO"


def traduzir_centro_origem_por_chave(db, chave: str) -> str:
    cnpj = extrair_cnpj_emitente_da_chave(chave)

    if not cnpj:
        return "CNPJ ORIGEM INVÁLIDO"

    empresa = (
        db.query(Empresa)
        .filter(Empresa.cnpj == cnpj)
        .first()
    )

    if not empresa:
        return f"CNPJ {cnpj} NÃO CADASTRADO"

    cidade_uf = ""

    if empresa.cidade:
        cidade_uf = empresa.cidade

    if empresa.estado:
        cidade_uf = f"{cidade_uf} - {empresa.estado}" if cidade_uf else empresa.estado

    if cidade_uf:
        return f"{empresa.razao_social} ({cidade_uf})"

    return empresa.razao_social