from __future__ import annotations

import asyncio
import re
from contextlib import closing
from datetime import datetime
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, InlineQueryHandler

from onibus.core import BRT, ConsultaSaidas, carregar_pontos, conectar, proximas_saidas
from onibus.search import buscar_sugestoes

# Padrão do callback data: p:numero:revisao:posicao (exemplo: p:11:1:1)
_CALLBACK_RE = re.compile(r"p:([0-9]{1,10}):([0-9]{1,10}):([1-5])")


def build_application(token: str, db_path: str | Path) -> Application:
    """
    O que faz: Constrói a aplicação do bot do Telegram e registra os manipuladores de eventos.
    Por que foi feito assim: Centraliza o registro de rotas (/start, busca inline e cliques em botões)
    e vincula o caminho do banco de dados na memória do bot (bot_data).
    """
    application = Application.builder().token(token).build()
    application.bot_data["db_path"] = str(db_path)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(ponto_callback))
    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    O que faz: Responde ao comando /start com uma saudação e um botão que ativa a busca inline.
    Por que foi feito assim: Conforme regra D-02, a experiência é inline e imediata no chat atual,
    sem obrigar o passageiro a digitar comandos complexos.
    """
    if update.effective_message:
        await update.effective_message.reply_text(
            "Escolha uma linha pelo número ou nome:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Buscar linha", switch_inline_query_current_chat="")]]
            ),
        )


def criar_artigo(linha, pontos) -> InlineQueryResultArticle:
    """
    O que faz: Monta o card de resultado inline para uma linha de ônibus.
    Por que foi feito assim: Conforme regra D-03, ao enviar a mensagem, ela já lista os endereços
    completos e apresenta botões para escolher o ponto desejado de forma direta.
    """
    titulo = f"{linha['numero']:03d} - {linha['nome']}"
    enderecos = [f"{i}. {pontos[f'ponto{i}']}" for i in range(1, 6) if pontos and pontos[f"ponto{i}"]]
    teclado = [
        [InlineKeyboardButton(f"Ponto {i}", callback_data=f"p:{linha['numero']}:{pontos['revisao']}:{i}")]
        for i in range(1, 6)
        if pontos and pontos[f"ponto{i}"]
    ]
    return InlineQueryResultArticle(
        id=f"l:{linha['numero']}:{pontos['revisao'] if pontos else 1}",
        title=titulo[:256],
        description=" | ".join(enderecos)[:512],
        input_message_content=InputTextMessageContent(titulo + "\nEscolha o endereço:\n" + "\n".join(enderecos)),
        reply_markup=InlineKeyboardMarkup(teclado),
    )


def _artigos(db_path: str | Path, termo: str, offset: str) -> tuple[list[InlineQueryResultArticle], str]:
    """
    O que faz: Realiza a busca no banco SQLite fora da thread principal e monta a lista de artigos.
    Por que foi feito assim: Garante que consultas a disco não travem o loop de eventos assíncrono do bot.
    """
    pagina = buscar_sugestoes(db_path, termo, offset, limit=10)
    with closing(conectar(db_path)) as conn:
        artigos = [criar_artigo(linha, carregar_pontos(conn, linha["numero"])) for linha in pagina.itens]
    return artigos, pagina.next_offset


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    O que faz: Processa as buscas inline conforme o usuário digita no Telegram.
    Por que foi feito assim: Conforme regras D-01 a D-05, busca números e nomes com normalização
    Unicode sem acentos, com paginação de 10 em 10 itens via next_offset.
    """
    query = update.inline_query
    if query is None:
        return
    offset_text = query.offset or "0"
    if not re.fullmatch(r"[0-9]{1,6}", offset_text) or int(offset_text) > 100000:
        await query.answer(results=[], next_offset="", cache_time=0)
        return

    artigos, next_offset = await asyncio.to_thread(
        _artigos, context.bot_data["db_path"], query.query[:256].strip(), offset_text
    )
    await query.answer(results=artigos, next_offset=next_offset, cache_time=30, is_personal=True)


def formato_saidas(consulta: ConsultaSaidas) -> str:
    """
    O que faz: Formata a resposta com o número e nome da linha na primeira linha do cabeçalho,
    seguido do endereço do ponto, data e as próximas saídas no padrão de Brasília.
    Por que foi feito assim: Atende à solicitação de identificar com destaque a linha consultada
    no topo da mensagem antes dos horários.
    """
    linha_cabecalho = f"{consulta.numero:03d} - {consulta.nome}\n" if consulta.numero and consulta.nome else ""
    cabecalho = f"{linha_cabecalho}{consulta.endereco}\n{consulta.data:%d/%m/%Y} — horário de Brasília"
    if consulta.status == "indisponivel":
        return cabecalho + "\nHorários indisponíveis para este ponto e calendário."
    if consulta.status == "encerrado":
        return cabecalho + "\nOs horários de hoje terminaram."
    return cabecalho + "\nPróximas saídas:\n" + "\n".join(consulta.horarios)


def _consultar(db_path: str | Path, numero: int, revisao: int, posicao: int, agora: datetime) -> ConsultaSaidas | None:
    """
    O que faz: Valida a revisão dos dados e obtém as próximas saídas para o ponto selecionado.
    Por que foi feito assim: Se a linha foi atualizada e a revisão mudou, retorna None para
    que o usuário seja orientado a refazer a busca, evitando exibir dados obsoletos.
    """
    with closing(conectar(db_path)) as conn:
        pontos = carregar_pontos(conn, numero)
        if pontos is None or pontos["revisao"] != revisao or not pontos[f"ponto{posicao}"]:
            return None
        return proximas_saidas(conn, numero, posicao, agora)


async def ponto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    O que faz: Atende ao clique nos botões de endereço/ponto da linha.
    Por que foi feito assim: Conforme regra D-03, edita a mensagem substituindo o texto
    pelos próximos horários. Funciona perfeitamente com mensagens inline (apenas inline_message_id).
    """
    query = update.callback_query
    if query is None:
        return
    match = _CALLBACK_RE.fullmatch(query.data or "")
    if match is None:
        await query.answer("Seleção inválida. Busque a linha novamente.", show_alert=True)
        return

    await query.answer()
    agora = context.bot_data.get("clock", lambda: datetime.now(BRT))()
    consulta = await asyncio.to_thread(_consultar, context.bot_data["db_path"], *map(int, match.groups()), agora)
    texto = formato_saidas(consulta) if consulta else "Esta seleção expirou porque os dados foram atualizados. Busque a linha novamente."
    try:
        await query.edit_message_text(text=texto)
    except BadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise
