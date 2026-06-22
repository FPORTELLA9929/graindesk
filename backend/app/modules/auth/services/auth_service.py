from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha, verificar_senha
from app.modules.admin.models.perfil import Perfil
from app.modules.admin.models.perfil_permissao import PerfilPermissao
from app.modules.admin.models.permissao import Permissao
from app.modules.auth.models.usuario import Usuario
from app.modules.auth.schemas.usuario import UsuarioCreate


def normalizar_perfil(nome_perfil: str | None) -> str:
    if not nome_perfil:
        return ""

    mapa = {
        "administrador": "Administrador",
        "operacional": "Operacional",
        "comercial": "Comercial",
        "logística": "Logística",
        "logistica": "Logística",
        "financeiro": "Financeiro",
        "consulta": "Consulta",
    }

    return mapa.get(nome_perfil.lower().strip(), nome_perfil.strip())


def contar_usuarios(db: Session) -> int:
    return db.query(Usuario).count()


def buscar_usuario_por_email(db: Session, email: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.email == email.lower().strip()).first()


def criar_usuario(db: Session, dados: UsuarioCreate) -> Usuario:
    if dados.senha != dados.confirmar_senha:
        raise ValueError("As senhas não conferem.")

    email = dados.email.lower().strip()

    if buscar_usuario_por_email(db, email):
        raise ValueError("Já existe um usuário cadastrado com este e-mail.")

    primeiro_usuario = contar_usuarios(db) == 0

    usuario = Usuario(
        nome=dados.nome.strip(),
        empresa=dados.empresa.strip(),
        cnpj=dados.cnpj.strip(),
        email=email,
        telefone=dados.telefone.strip() if dados.telefone else None,
        cargo=dados.cargo.strip() if dados.cargo else None,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil="administrador" if primeiro_usuario else "operacional",
        status="ativo" if primeiro_usuario else "pendente",
        ativo=True,
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> Usuario | None:
    usuario = buscar_usuario_por_email(db, email)

    if not usuario:
        return None

    if not usuario.ativo:
        return None

    if usuario.status != "ativo":
        return None

    if not verificar_senha(senha, usuario.senha_hash):
        return None

    usuario.ultimo_login = datetime.utcnow()
    db.commit()

    return usuario


def listar_codigos_permissoes_usuario(db: Session, usuario: Usuario) -> list[str]:
    nome_perfil = normalizar_perfil(usuario.perfil)

    perfil = (
        db.query(Perfil)
        .filter(Perfil.nome == nome_perfil)
        .filter(Perfil.ativo == True)
        .first()
    )

    if not perfil:
        return []

    permissoes = (
        db.query(Permissao)
        .join(PerfilPermissao, PerfilPermissao.permissao_id == Permissao.id)
        .filter(PerfilPermissao.perfil_id == perfil.id)
        .filter(Permissao.ativo == True)
        .all()
    )

    return [permissao.codigo for permissao in permissoes]