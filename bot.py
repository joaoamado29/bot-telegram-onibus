from __future__ import annotations

import argparse
import logging
import os
from contextlib import closing
from pathlib import Path

from onibus.core import coletar_linha, conectar, publicar_linha
from onibus.refresh import CoordenadorColeta, registrar_coletas
from onibus.telegram_handlers import build_application
from scraping import LinhaOnibus

DB_PATH = Path(__file__).resolve().parent / "onibus.sqlite3"
ENV_PATH = Path(__file__).resolve().parent / ".env"


def _carregar_env(caminho: Path) -> None:
    """
    O que faz: Lê pares CHAVE=VALOR de um arquivo .env local e define no ambiente.
    Por que foi feito assim: Permite carregar o token do Telegram de forma segura e local,
    sem exigir bibliotecas de terceiros e sem expor credenciais no código ou no versionamento.
    """
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip("'\"")
        if chave and chave not in os.environ:
            os.environ[chave] = valor


def main() -> None:
    parser = argparse.ArgumentParser(description="Consulta de horários ETUFOR no Telegram")
    parser.add_argument("--coletar-linha", type=int, metavar="NUMERO")
    args = parser.parse_args()
    _carregar_env(ENV_PATH)
    if args.coletar_linha is not None:
        with closing(conectar(DB_PATH)) as conn:
            row = conn.execute("SELECT numero,nome,link FROM linhas WHERE numero=?", (args.coletar_linha,)).fetchone()
        if row is None:
            parser.error("Linha não encontrada no catálogo; execute scraping.py primeiro.")
        try:
            horarios = coletar_linha(LinhaOnibus(row["numero"], row["nome"], row["link"]))
            with closing(conectar(DB_PATH)) as conn:
                publicar_linha(conn, horarios)
        except Exception:
            parser.exit(1, "Não foi possível atualizar a linha; os dados anteriores foram preservados.\n")
        print(f"Linha {row['numero']:03d} atualizada.")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        parser.exit(1, "Configure TELEGRAM_BOT_TOKEN no ambiente local; não compartilhe o token.\n")
    # Bibliotecas HTTP podem incluir URLs autenticadas nos logs INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    application = build_application(token, DB_PATH)
    coordenador = CoordenadorColeta(DB_PATH)
    registrar_coletas(application, coordenador)
    try:
        application.run_polling(allowed_updates=["message", "inline_query", "callback_query"])
    except Exception:
        parser.exit(1, "Não foi possível iniciar o bot. Confira a configuração local e a conexão.\n")


if __name__ == "__main__":
    main()
