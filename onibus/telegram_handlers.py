from __future__ import annotations

import asyncio
import re
from contextlib import closing
from datetime import datetime
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, InlineQueryHandler

from onibus.core import BRT, ConsultaSaidas, buscar_linhas, carregar_pontos, conectar, proximas_saidas

_CALLBACK_RE = re.compile(r"p:([0-9]{1,10}):([0-9]{1,10}):([1-5])")


def build_application(token: str, db_path: str | Path) -> Application:
    application = Application.builder().token(token).build()
    application.bot_data["db_path"] = str(db_path)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(ponto_callback))
    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text("Escolha uma linha pelo número ou nome:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buscar linha", switch_inline_query_current_chat="")]]))


def criar_artigo(linha, pontos) -> InlineQueryResultArticle:
    titulo = f"{linha['numero']:03d} - {linha['nome']}"
    enderecos = [f"{i}. {pontos[f'ponto{i}']}" for i in range(1, 6) if pontos[f"ponto{i}"]]
    teclado = [[InlineKeyboardButton(f"Ponto {i}", callback_data=f"p:{linha['numero']}:{pontos['revisao']}:{i}")] for i in range(1, 6) if pontos[f"ponto{i}"]]
    return InlineQueryResultArticle(id=f"l:{linha['numero']}:{pontos['revisao']}", title=titulo[:256], description=" | ".join(enderecos)[:512], input_message_content=InputTextMessageContent(titulo + "\nEscolha o endereço:\n" + "\n".join(enderecos)), reply_markup=InlineKeyboardMarkup(teclado))


def _artigos(db_path, termo, offset):
    with closing(conectar(db_path)) as conn:
        linhas = buscar_linhas(conn, termo, offset, limit=10)
        return [criar_artigo(linha, carregar_pontos(conn, linha["numero"])) for linha in linhas]


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query
    if query is None:
        return
    offset_text = query.offset or "0"
    if not re.fullmatch(r"[0-9]{1,6}", offset_text) or int(offset_text) > 100000:
        await query.answer(results=[], cache_time=0)
        return
    offset = int(offset_text)
    artigos = await asyncio.to_thread(_artigos, context.bot_data["db_path"], query.query[:256].strip(), offset)
    await query.answer(results=artigos, next_offset=str(offset + 10) if len(artigos) == 10 else "", cache_time=0, is_personal=True)


def formato_saidas(consulta: ConsultaSaidas) -> str:
    cabecalho = f"{consulta.endereco}\n{consulta.data:%d/%m/%Y} — horário de Brasília"
    if consulta.status == "indisponivel":
        return cabecalho + "\nHorários indisponíveis para este ponto e calendário."
    if consulta.status == "encerrado":
        return cabecalho + "\nOs horários de hoje terminaram."
    return cabecalho + "\nPróximas saídas:\n" + "\n".join(consulta.horarios)


def _consultar(db_path, numero, revisao, posicao, agora):
    with closing(conectar(db_path)) as conn:
        pontos = carregar_pontos(conn, numero)
        if pontos is None or pontos["revisao"] != revisao or not pontos[f"ponto{posicao}"]:
            return None
        return proximas_saidas(conn, numero, posicao, agora)


async def ponto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    match = _CALLBACK_RE.fullmatch(query.data or "")
    if match is None:
        await query.answer("Seleção inválida. Busque a linha novamente.")
        return
    await query.answer()
    agora = context.bot_data.get("clock", lambda: datetime.now(BRT))()
    consulta = await asyncio.to_thread(_consultar, context.bot_data["db_path"], *map(int, match.groups()), agora)
    texto = formato_saidas(consulta) if consulta else "Esta seleção expirou. Busque a linha novamente."
    try:
        await query.edit_message_text(text=texto)
    except BadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise
