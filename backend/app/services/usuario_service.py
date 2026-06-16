from sqlalchemy.orm import Session

from app.models.usuario import Usuario


def listar_usuarios(db: Session):
    return db.query(Usuario).order_by(Usuario.criado_em.desc()).all()


def buscar_usuario_por_id(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def aprovar_usuario(db: Session, usuario: Usuario):
    usuario.status = "ativo"
    usuario.ativo = True
    db.commit()
    db.refresh(usuario)
    return usuario


def recusar_usuario(db: Session, usuario: Usuario):
    usuario.status = "recusado"
    usuario.ativo = False
    db.commit()
    db.refresh(usuario)
    return usuario


def inativar_usuario(db: Session, usuario: Usuario):
    usuario.status = "inativo"
    usuario.ativo = False
    db.commit()
    db.refresh(usuario)
    return usuario


def reativar_usuario(db: Session, usuario: Usuario):
    usuario.status = "ativo"
    usuario.ativo = True
    db.commit()
    db.refresh(usuario)
    return usuario