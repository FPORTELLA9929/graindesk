from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.modules.admin.models.perfil import Perfil
from app.modules.admin.models.perfil_permissao import PerfilPermissao
from app.modules.admin.models.permissao import Permissao


def usuario_logado(request: Request) -> bool:
    return bool(request.session.get("usuario_logado"))


def perfil_usuario(request: Request) -> str | None:
    return request.session.get("usuario_perfil")


def possui_permissao(
    db: Session,
    request: Request,
    codigo_permissao: str,
) -> bool:
    if not usuario_logado(request):
        return False

    permissoes_sessao = request.session.get("permissoes", [])

    if codigo_permissao in permissoes_sessao:
        return True

    perfil_nome = perfil_usuario(request)

    if not perfil_nome:
        return False

    perfil = (
        db.query(Perfil)
        .filter(Perfil.nome.ilike(perfil_nome))
        .first()
    )

    if not perfil:
        return False

    permissao = (
        db.query(Permissao)
        .join(PerfilPermissao, PerfilPermissao.permissao_id == Permissao.id)
        .filter(PerfilPermissao.perfil_id == perfil.id)
        .filter(Permissao.codigo == codigo_permissao)
        .filter(Permissao.ativo == True)
        .first()
    )

    return permissao is not None


def redirecionar_se_nao_logado_ou_sem_permissao(
    db: Session,
    request: Request,
    codigo_permissao: str,
):
    if not usuario_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    if not possui_permissao(db, request, codigo_permissao):
        return RedirectResponse(url="/dashboard", status_code=303)

    return None