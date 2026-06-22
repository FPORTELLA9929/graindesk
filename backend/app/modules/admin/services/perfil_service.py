from sqlalchemy.orm import Session

from app.modules.admin.models.perfil import Perfil
from app.modules.admin.models.permissao import Permissao
from app.modules.admin.models.perfil_permissao import PerfilPermissao


PERFIS_PADRAO = [
    {
        "nome": "Administrador",
        "descricao": "Acesso total ao sistema.",
    },
    {
        "nome": "Operacional",
        "descricao": "Operações de exportação e documentos.",
    },
    {
        "nome": "Comercial",
        "descricao": "Clientes, propostas e negociações.",
    },
    {
        "nome": "Logística",
        "descricao": "Embarques, booking e transporte.",
    },
    {
        "nome": "Financeiro",
        "descricao": "Financeiro e relatórios.",
    },
    {
        "nome": "Consulta",
        "descricao": "Somente visualização.",
    },
]


PERMISSOES_PADRAO = [
    ("dashboard", "Dashboard", "Dashboard"),
    ("usuarios", "Usuários", "Administração"),
    ("perfis", "Perfis e Permissões", "Administração"),
    ("empresas", "Empresas", "Cadastros"),
    ("processos", "Processos de Exportação", "Operacional"),
    ("due", "DUE", "Operacional"),
    ("nfe_exportacao", "NF-e de Exportação", "Operacional"),
    ("cct", "CCT / Siscomex", "Operacional"),
    ("contratos", "Contratos", "Operacional"),
    ("booking", "Booking / Embarque", "Logística"),
    ("relatorios", "Relatórios", "Gestão"),
]
    

def criar_perfis_padrao(db: Session):
    for perfil in PERFIS_PADRAO:

        existente = (
            db.query(Perfil)
            .filter(Perfil.nome == perfil["nome"])
            .first()
        )

        if existente:
            continue

        novo = Perfil(
            nome=perfil["nome"],
            descricao=perfil["descricao"],
            ativo=True,
        )

        db.add(novo)

    db.commit()


def criar_permissoes_padrao(db: Session):
    for codigo, nome, modulo in PERMISSOES_PADRAO:

        existente = (
            db.query(Permissao)
            .filter(Permissao.codigo == codigo)
            .first()
        )

        if existente:
            continue

        permissao = Permissao(
            codigo=codigo,
            nome=nome,
            modulo=modulo,
            ativo=True,
        )

        db.add(permissao)

    db.commit()


def listar_perfis(db: Session):
    return (
        db.query(Perfil)
        .order_by(Perfil.nome.asc())
        .all()
    )


def listar_permissoes(db: Session):
    return (
        db.query(Permissao)
        .order_by(Permissao.modulo.asc(), Permissao.nome.asc())
        .all()
    )


def buscar_perfil(db: Session, perfil_id: int):
    return (
        db.query(Perfil)
        .filter(Perfil.id == perfil_id)
        .first()
    )


def listar_permissoes_perfil(db: Session, perfil_id: int):
    registros = (
        db.query(PerfilPermissao)
        .filter(PerfilPermissao.perfil_id == perfil_id)
        .all()
    )

    return [registro.permissao_id for registro in registros]


def atualizar_permissoes_perfil(
    db: Session,
    perfil_id: int,
    permissoes_ids: list[int],
):
    (
        db.query(PerfilPermissao)
        .filter(PerfilPermissao.perfil_id == perfil_id)
        .delete()
    )

    for permissao_id in permissoes_ids:

        db.add(
            PerfilPermissao(
                perfil_id=perfil_id,
                permissao_id=permissao_id,
            )
        )

    db.commit()