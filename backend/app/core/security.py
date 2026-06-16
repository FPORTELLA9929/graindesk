import base64
import hashlib
import hmac
import os


def gerar_hash_senha(senha: str) -> str:
    salt = os.urandom(16)
    chave = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        120_000,
    )

    salt_b64 = base64.b64encode(salt).decode("utf-8")
    chave_b64 = base64.b64encode(chave).decode("utf-8")

    return f"pbkdf2_sha256$120000${salt_b64}${chave_b64}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        algoritmo, iteracoes, salt_b64, chave_b64 = senha_hash.split("$")
    except ValueError:
        return False

    if algoritmo != "pbkdf2_sha256":
        return False

    salt = base64.b64decode(salt_b64.encode("utf-8"))
    chave_original = base64.b64decode(chave_b64.encode("utf-8"))

    chave_teste = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        int(iteracoes),
    )

    return hmac.compare_digest(chave_original, chave_teste)