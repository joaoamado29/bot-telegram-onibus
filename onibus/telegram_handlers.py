from __future__ import annotations

import asyncio
import re
from contextlib import closing
from datetime import datetime, time, timedelta
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, InlineQueryHandler
from telegram.helpers import create_deep_linked_url

from onibus.alertas import Alertas, ConsultaAlerta, Viagem, opcoes_antecedencia

from onibus.core import BRT, ConsultaSaidas, carregar_pontos, conectar, proximas_saidas
from onibus.search import buscar_sugestoes

# Padrão do callback data: p:numero:revisao:posicao (exemplo: p:11:1:1)
_CALLBACK_RE = re.compile(r"p:([0-9]{1,10}):([0-9]{1,10}):([1-5])")
_HORARIOS_RE = re.compile(r"h:([0-9]{1,10}):([0-9]{1,10}):([1-5]):([0-9]{8}):([0-9]{1,4})")
_VOLTAR_RE = re.compile(r"b:([0-9]{1,10}):([0-9]{1,10})")
_CALENDARIOS = {"uteis": "Dias úteis", "sabados": "Sábados", "domingos_feriados": "Domingos e feriados"}
_HORARIOS_POR_PAGINA = 28
_ALERTA_RE = re.compile(r"(an|av|aa|as):([A-Za-z0-9_-]{22})(?::([0-9]{1,2}))?")
_ALERTA_EXPIRADO = "Esta seleção expirou. Busque a linha novamente."


def build_application(token: str, db_path: str | Path) -> Application:
    """
    O que faz: Constrói a aplicação do bot do Telegram e registra os manipuladores de eventos.
    Por que foi feito assim: Centraliza o registro de rotas (/start, busca inline e cliques em botões)
    e vincula o caminho do banco de dados na memória do bot (bot_data).
    """
    application = Application.builder().token(token).build()
    application.bot_data["db_path"] = str(db_path)
    application.bot_data["alertas"] = Alertas()
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
        args = getattr(context, "args", None)
        if args and args[0].startswith("alerta_"):
            await _iniciar_alerta(update, context, args[0][7:])
            return
        await update.effective_message.reply_text(
            "Escolha uma linha pelo número ou nome:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Buscar linha", switch_inline_query_current_chat="")]]
            ),
        )


def _botao_buscar_outra_linha() -> InlineKeyboardButton:
    return InlineKeyboardButton("Buscar outra linha", switch_inline_query_current_chat="")


def _agora(context: ContextTypes.DEFAULT_TYPE) -> datetime:
    return context.bot_data.get("clock", lambda: datetime.now(BRT))()


def _saida(consulta: ConsultaAlerta, horario: str) -> datetime:
    return datetime.combine(consulta.dia, time.fromisoformat(horario), tzinfo=BRT)


async def _viagens(
    context: ContextTypes.DEFAULT_TYPE, consulta: ConsultaAlerta, chat_id: int
) -> list[Viagem]:
    dados = await asyncio.to_thread(
        _consultar, context.bot_data["db_path"], consulta.numero, consulta.revisao,
        consulta.ponto, datetime.combine(consulta.dia, time.min, tzinfo=BRT),
    )
    if dados is None:
        return []
    agora = _agora(context)
    return [
        Viagem(consulta, f"{dados.numero:03d} - {dados.nome}", saida, chat_id)
        for horario in consulta.horarios
        if horario in dados.todos_horarios and (saida := _saida(consulta, horario)) > agora
    ]


async def _iniciar_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    chat, usuario = update.effective_chat, update.effective_user
    if chat is None or chat.type != "private" or usuario is None:
        return
    alertas = context.bot_data["alertas"]
    consulta = alertas.obter(token, _agora(context), usuario.id)
    viagens = await _viagens(context, consulta, chat.id) if isinstance(consulta, ConsultaAlerta) else []
    if not viagens:
        await update.effective_message.reply_text(_ALERTA_EXPIRADO)
        return
    botoes = [
        [InlineKeyboardButton(f"{viagem.saida:%H:%M}", callback_data=f"av:{alertas.guardar(_agora(context), usuario.id, viagem)}")]
        for viagem in viagens
    ]
    await update.effective_message.reply_text(
        f"{viagens[0].linha}\nEscolha o horário da saída:", reply_markup=InlineKeyboardMarkup(botoes)
    )


async def _mostrar_antecedencias(query, token: str, viagem: Viagem, agora: datetime) -> None:
    opcoes = opcoes_antecedencia(viagem.saida, agora)
    if not opcoes:
        await query.edit_message_text(_ALERTA_EXPIRADO)
        return
    texto = "Está em cima da hora. Posso avisar no horário da saída." if opcoes == (0,) else "Quando você quer receber o primeiro aviso?"
    botoes = [InlineKeyboardButton(
        f"{minutos} min" if minutos else "Só no horário da saída", callback_data=f"aa:{token}:{minutos}"
    ) for minutos in opcoes]
    await query.edit_message_text(texto, reply_markup=InlineKeyboardMarkup([botoes]))


async def alerta_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    match = _ALERTA_RE.fullmatch(query.data or "")
    usuario = update.effective_user
    if match is None or usuario is None:
        await query.answer(_ALERTA_EXPIRADO, show_alert=True)
        return
    acao, token, valor = match.groups()
    alertas = context.bot_data["alertas"]
    agora = _agora(context)
    dados = alertas.obter(token, agora, None if acao == "an" else usuario.id)
    if acao == "an" and isinstance(dados, ConsultaAlerta) and valor is None:
        intencao = alertas.guardar(agora, usuario.id, dados)
        await query.answer(url=create_deep_linked_url(context.bot.username, f"alerta_{intencao}"))
        return
    chat = update.effective_chat
    if chat is None or chat.type != "private":
        await query.answer(_ALERTA_EXPIRADO, show_alert=True)
        return
    anterior = None
    if acao == "as" and isinstance(dados, tuple) and valor is None:
        viagem, minutos, anterior = dados
    elif isinstance(dados, Viagem) and ((acao == "av" and valor is None) or (acao == "aa" and valor is not None)):
        viagem, minutos = dados, int(valor) if valor is not None else None
    else:
        await query.answer(_ALERTA_EXPIRADO, show_alert=True)
        return
    if viagem.chat_id != chat.id:
        await query.answer(_ALERTA_EXPIRADO, show_alert=True)
        return
    await query.answer()
    if viagem not in await _viagens(context, viagem.consulta, chat.id):
        await query.edit_message_text(_ALERTA_EXPIRADO)
        return
    agora = _agora(context)
    if alertas.obter(token, agora, usuario.id) is not dados:
        return
    opcoes = opcoes_antecedencia(viagem.saida, agora)
    if minutos not in opcoes:
        token_viagem = alertas.guardar(agora, usuario.id, viagem) if acao == "as" else token
        if acao == "as":
            alertas.etapas.pop(token, None)
        await _mostrar_antecedencias(query, token_viagem, viagem, agora)
        return
    ativo = alertas.ativo(usuario.id, agora)
    if acao == "aa" and ativo:
        consulta_atual = ativo.viagem.consulta
        if (
            ativo.viagem.saida == viagem.saida
            and consulta_atual.numero == viagem.consulta.numero
            and consulta_atual.ponto == viagem.consulta.ponto
        ):
            await query.edit_message_text("Você já tem um alerta ativo para esta viagem.")
            return
        troca = alertas.guardar(agora, usuario.id, (viagem, minutos, ativo.identidade))
        await query.edit_message_text(
            "Você já tem um alerta ativo. Quer acompanhar esta viagem?",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Substituir alerta", callback_data=f"as:{troca}")]]),
        )
        return
    if not alertas.agendar(context.job_queue, usuario.id, viagem, minutos, anterior):
        await query.edit_message_text("Não foi possível ativar o alerta. Consulte a linha novamente.")
        return
    alertas.etapas.pop(token, None)
    aviso = "Você receberá avisos antes da saída." if minutos else "Você receberá um aviso no horário da saída."
    await query.edit_message_text(f"🔔 Alertas ativados para a linha {viagem.linha}.\n{aviso}")


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
    teclado.append([_botao_buscar_outra_linha()])
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


def formato_saidas(consulta: ConsultaSaidas, amanha: ConsultaSaidas | None = None) -> str:
    """
    O que faz: Formata a resposta com o número e nome da linha na primeira linha do cabeçalho,
    seguido do endereço do ponto, data e as próximas saídas no padrão de Brasília.
    Por que foi feito assim: Atende à solicitação de identificar com destaque a linha consultada
    no topo da mensagem antes dos horários.
    """
    linha_cabecalho = f"{consulta.numero:03d} - {consulta.nome}\n" if consulta.numero and consulta.nome else ""
    cabecalho = f"{linha_cabecalho}{consulta.endereco}\n{consulta.data:%d/%m/%Y} — horário de Brasília"
    if consulta.feriados:
        cabecalho += f"\nFeriado(s): {', '.join(consulta.feriados)} ({consulta.data:%d/%m/%Y})"
    if consulta.status == "indisponivel":
        return cabecalho + "\nHorários indisponíveis para este ponto e calendário."
    if consulta.status == "encerrado":
        if amanha and amanha.todos_horarios:
            return (
                cabecalho
                + "\nAs saídas de hoje terminaram. "
                + f"A primeira saída de amanhã é às {amanha.todos_horarios[0]}."
            )
        if amanha:
            return cabecalho + "\nOs horários de hoje terminaram.\nHorários de amanhã indisponíveis para este ponto e calendário."
        return cabecalho + "\nOs horários de hoje terminaram."
    return cabecalho + "\nPróximas saídas:\n" + "\n".join(consulta.horarios)


def _teclado_consulta(
    numero: int, revisao: int, posicao: int, consulta: ConsultaSaidas, amanha: ConsultaSaidas | None = None,
    token_alerta: str | None = None,
) -> InlineKeyboardMarkup:
    teclado = []
    if token_alerta:
        teclado.append([InlineKeyboardButton("Notificar", callback_data=f"an:{token_alerta}")])
    if amanha:
        teclado.append([InlineKeyboardButton(
            "Ver horários de amanhã", callback_data=f"h:{numero}:{revisao}:{posicao}:{amanha.data:%Y%m%d}:0"
        )])
    return InlineKeyboardMarkup(teclado + [
        [InlineKeyboardButton("Ver horários", callback_data=f"h:{numero}:{revisao}:{posicao}:{consulta.data:%Y%m%d}:0")],
        [InlineKeyboardButton("Voltar", callback_data=f"b:{numero}:{revisao}")],
        [_botao_buscar_outra_linha()],
    ])


def _paginas_horarios(consulta: ConsultaSaidas) -> list[str]:
    """Divide a lista sem remover horários e repete a identificação em cada página."""
    cabecalho = (
        f"{consulta.numero:03d} - {consulta.nome}\n{consulta.endereco}\n"
        f"{consulta.data:%d/%m/%Y} — horário de Brasília\n{_CALENDARIOS[consulta.calendario]}"
    )
    if consulta.feriados:
        cabecalho += "\nFeriado(s): " + ", ".join(consulta.feriados)
    if consulta.status == "indisponivel":
        texto = cabecalho + "\nHorários indisponíveis para este ponto e calendário."
        if len(texto) > 4096:
            raise ValueError("Identificação excede o limite da mensagem")
        return [texto]
    total = 1
    while True:
        rotulo = f"\nTodos os horários — Página {total}/{total}:\n"
        limite = 4096 - len(cabecalho) - len(rotulo)
        grupos = []
        atual = ""
        quantidade_atual = 0
        for horario in consulta.todos_horarios:
            if len(horario) > limite:
                raise ValueError("Identificação excede o limite da mensagem")
            candidato = f"{atual}, {horario}" if atual else horario
            if len(candidato) > limite or quantidade_atual >= _HORARIOS_POR_PAGINA:
                grupos.append(atual)
                atual = horario
                quantidade_atual = 1
            else:
                atual = candidato
                quantidade_atual += 1
        grupos.append(atual)
        if len(grupos) == total:
            return [f"{cabecalho}\nTodos os horários — Página {i + 1}/{total}:\n{grupo}" for i, grupo in enumerate(grupos)]
        total = len(grupos)


def _voltar(db_path: str | Path, numero: int, revisao: int) -> tuple[str, InlineKeyboardMarkup] | None:
    with closing(conectar(db_path)) as conn:
        pontos = carregar_pontos(conn, numero)
        if pontos is None or pontos["revisao"] != revisao:
            return None
        artigo = criar_artigo(pontos, pontos)
        return artigo.input_message_content.message_text, artigo.reply_markup


def _consultar(db_path: str | Path, numero: int, revisao: int, posicao: int, agora: datetime) -> ConsultaSaidas | None:
    consulta, _ = _consultar_datas(db_path, numero, revisao, posicao, agora, incluir_amanha=False)
    return consulta


def _consultar_datas(
    db_path: str | Path, numero: int, revisao: int, posicao: int, agora: datetime, *, incluir_amanha: bool
) -> tuple[ConsultaSaidas | None, ConsultaSaidas | None]:
    """
    O que faz: Valida a revisão dos dados e obtém as próximas saídas para o ponto selecionado.
    Por que foi feito assim: Se a linha foi atualizada e a revisão mudou, retorna None para
    que o usuário seja orientado a refazer a busca, evitando exibir dados obsoletos.
    A consulta de amanhã usa a mesma revisão e a mesma transação.
    """
    if posicao not in range(1, 6):
        return None, None
    with closing(conectar(db_path)) as conn:
        # SELECT isolado não mantém snapshot no sqlite3; fixamos a revisão
        # e suas listas na mesma transação até a conexão ser fechada.
        conn.execute("BEGIN")
        pontos = carregar_pontos(conn, numero)
        if pontos is None or pontos["revisao"] != revisao or not pontos[f"ponto{posicao}"]:
            return None, None
        consulta = proximas_saidas(conn, numero, posicao, agora)
        amanha = None
        if incluir_amanha and consulta.status == "encerrado":
            inicio_amanha = datetime.combine(consulta.data + timedelta(days=1), time.min, tzinfo=BRT)
            amanha = proximas_saidas(conn, numero, posicao, inicio_amanha)
        return consulta, amanha


async def ponto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    O que faz: Atende ao clique nos botões de endereço/ponto da linha.
    Por que foi feito assim: Conforme regra D-03, edita a mensagem substituindo o texto
    pelos próximos horários. Funciona perfeitamente com mensagens inline (apenas inline_message_id).
    """
    query = update.callback_query
    if query is None:
        return
    data = query.data if isinstance(query.data, str) else ""
    if data.startswith(("an:", "av:", "aa:", "as:")):
        await alerta_callback(update, context)
        return
    match = _CALLBACK_RE.fullmatch(data)
    horarios_match = _HORARIOS_RE.fullmatch(data)
    voltar_match = _VOLTAR_RE.fullmatch(data)
    if match is None and horarios_match is None and voltar_match is None:
        await query.answer("Seleção inválida. Busque a linha novamente.", show_alert=True)
        return

    agora = _agora(context)
    teclado = None
    if voltar_match:
        resultado = await asyncio.to_thread(_voltar, context.bot_data["db_path"], *map(int, voltar_match.groups()))
        texto, teclado = resultado if resultado else ("Esta seleção expirou. Busque a linha novamente.", None)
    else:
        campos = (match or horarios_match).groups()
        numero, revisao, posicao = map(int, campos[:3])
        if horarios_match:
            try:
                agora = datetime.strptime(campos[3], "%Y%m%d").replace(tzinfo=BRT)
            except ValueError:
                await query.answer("Data inválida. Busque a linha novamente.", show_alert=True)
                return
        db_path = context.bot_data["db_path"]
        amanha = None
        if horarios_match:
            consulta = await asyncio.to_thread(_consultar, db_path, numero, revisao, posicao, agora)
        else:
            consulta, amanha = await asyncio.to_thread(
                _consultar_datas, db_path, numero, revisao, posicao, agora, incluir_amanha=True
            )
        texto = formato_saidas(consulta, amanha) if consulta else "Esta seleção expirou porque os dados foram atualizados. Busque a linha novamente."
        if consulta:
            token_alerta = None
            alertas = context.bot_data.get("alertas")
            if not horarios_match and alertas is not None and consulta.status == "disponivel" and consulta.horarios:
                snapshot = ConsultaAlerta(numero, revisao, posicao, consulta.data, tuple(consulta.horarios))
                token_alerta = alertas.guardar(agora, None, snapshot)
            teclado = _teclado_consulta(numero, revisao, posicao, consulta, amanha, token_alerta)
            if horarios_match:
                try:
                    paginas = _paginas_horarios(consulta)
                except ValueError:
                    await query.answer("Não é possível exibir esta identificação no Telegram. Use Voltar para escolher outro ponto.", show_alert=True)
                    return
                pagina = int(campos[4])
                if pagina >= len(paginas):
                    await query.answer("Página inválida. Busque a linha novamente.", show_alert=True)
                    return
                texto = paginas[pagina]
                botoes = []
                for rotulo, indice in (("Anterior", pagina - 1), ("Próxima", pagina + 1)):
                    if 0 <= indice < len(paginas):
                        botoes.append(InlineKeyboardButton(rotulo, callback_data=f"h:{numero}:{revisao}:{posicao}:{campos[3]}:{indice}"))
                teclado = InlineKeyboardMarkup(
                    ([botoes] if botoes else [])
                    + [
                        [InlineKeyboardButton("Voltar", callback_data=f"b:{numero}:{revisao}")],
                        [_botao_buscar_outra_linha()],
                    ]
                )
    await query.answer()
    try:
        await query.edit_message_text(text=texto, reply_markup=teclado)
    except BadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise
