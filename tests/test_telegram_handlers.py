from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

from onibus.core import BRT, HorariosLinha, PontoHorario, conectar, publicar_linha
from onibus.telegram_handlers import build_application, inline_query, ponto_callback, start


class TelegramHandlersTests(unittest.IsolatedAsyncioTestCase):
    """
    O que faz: Testa os adaptadores e handlers de mensagens do Telegram (/start, busca inline e callbacks).
    Por que foi feito assim: Garante que as interações do usuário no Telegram funcionem corretamente,
    inclusive em mensagens inline sem chat_id ou message regular, e rejeitem callbacks inválidos ou expirados.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "bot_test.sqlite3"
        with closing(conectar(self.db_path)) as conn:
            # Insere 2 linhas
            conn.execute("INSERT INTO linhas VALUES (11, 'Circular Centro', 'tonoponto.com/11', 'ts')")
            conn.execute("INSERT INTO linhas VALUES (22, 'Papicu / Aldeota', 'tonoponto.com/22', 'ts')")
            # Publica linha 11 com 2 pontos
            p1 = PontoHorario("Terminal A", {"uteis": ("10:00", "11:00", "12:00")})
            p2 = PontoHorario("Terminal B", {"uteis": ("10:30", "11:30", "12:30")})
            publicar_linha(conn, HorariosLinha(11, "Circular Centro", (p1, p2)))

        self.context = SimpleNamespace(
            bot_data={
                "db_path": self.db_path,
                "clock": lambda: datetime(2026, 11, 13, 9, 30, tzinfo=BRT),
            }
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    async def test_start_envia_botao_de_busca_inline(self) -> None:
        """
        O que faz: Testa o comando /start.
        Por que foi feito assim: Verifica se o bot responde ao /start com o botão switch_inline_query_current_chat
        para abrir imediatamente a busca inline no chat atual (D-02).
        """
        message = SimpleNamespace(reply_text=AsyncMock())
        update = SimpleNamespace(effective_message=message)

        await start(update, self.context)

        message.reply_text.assert_awaited_once()
        markup = message.reply_text.call_args.kwargs["reply_markup"]
        botao = markup.inline_keyboard[0][0]
        self.assertEqual(botao.text, "Buscar linha")
        self.assertEqual(botao.switch_inline_query_current_chat, "")

    async def test_inline_query_com_paginacao_e_artigos(self) -> None:
        """
        O que faz: Simula a digitação de busca inline '@bot 11'.
        Por que foi feito assim: Deve retornar artigos formatados contendo os endereços nos botões
        e o next_offset para rolagem de página (D-01 e D-05).
        """
        query = SimpleNamespace(query="11", offset="", answer=AsyncMock())
        update = SimpleNamespace(inline_query=query)

        await inline_query(update, self.context)

        query.answer.assert_awaited_once()
        args = query.answer.call_args.kwargs
        results = args["results"]
        self.assertEqual(len(results), 1)
        artigo = results[0]
        self.assertIn("011 - Circular Centro", artigo.title)
        self.assertIn("Terminal A", artigo.input_message_content.message_text)
        # Teclado do artigo possui 2 botões para os 2 pontos
        botoes = artigo.reply_markup.inline_keyboard
        self.assertEqual(len(botoes), 2)
        self.assertEqual(botoes[0][0].callback_data, "p:11:1:1")
        self.assertEqual(botoes[1][0].callback_data, "p:11:1:2")

    async def test_ponto_callback_inline_sem_message_retorna_saidas(self) -> None:
        """
        O que faz: Dispara o clique no botão de ponto quando a mensagem é puramente inline (sem query.message).
        Por que foi feito assim: Garante compatibilidade total com mensagens enviadas via inline query,
        onde apenas inline_message_id está presente (D-03).
        """
        callback = SimpleNamespace(
            data="p:11:1:1",
            inline_message_id="msg-inline-1234",
            message=None,
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        update = SimpleNamespace(callback_query=callback)

        await ponto_callback(update, self.context)

        callback.answer.assert_awaited_once()
        callback.edit_message_text.assert_awaited_once()
        texto_editado = callback.edit_message_text.call_args.kwargs["text"]
        linhas_texto = texto_editado.splitlines()
        self.assertEqual(linhas_texto[0], "011 - Circular Centro")
        self.assertIn("Terminal A", texto_editado)
        self.assertIn("10:00", texto_editado)

    async def test_ponto_callback_com_revisao_desatualizada_informa_expiracao(self) -> None:
        """
        O que faz: Clica em um botão que tem revisão antiga (ex: revisão 0 quando o banco está na 1).
        Por que foi feito assim: Impede que botões antigos exibam horários incorretos após atualizações da linha.
        """
        callback = SimpleNamespace(
            data="p:11:0:1",  # Revisão 0 é obsoleta (banco está na revisão 1)
            inline_message_id="msg-inline-antiga",
            message=None,
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        update = SimpleNamespace(callback_query=callback)

        await ponto_callback(update, self.context)

        callback.answer.assert_awaited_once()
        callback.edit_message_text.assert_awaited_once()
        texto_editado = callback.edit_message_text.call_args.kwargs["text"]
        self.assertIn("expirou", texto_editado.lower())

    async def test_ponto_callback_malformado_ou_invalido_rejeita_com_seguranca(self) -> None:
        """
        O que faz: Envia callback_data corrompido ou apontando para linha inexistente.
        Por que foi feito assim: Evita exceções não tratadas e responde adequadamente ao usuário.
        """
        # Formato malformado
        cb_malformado = SimpleNamespace(
            data="dados_invalidos",
            inline_message_id="msg-inline-err",
            message=None,
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        await ponto_callback(SimpleNamespace(callback_query=cb_malformado), self.context)
        cb_malformado.answer.assert_awaited_once()
        cb_malformado.edit_message_text.assert_not_called()

        # Linha inexistente (999)
        cb_inexistente = SimpleNamespace(
            data="p:999:1:1",
            inline_message_id="msg-inline-err2",
            message=None,
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        await ponto_callback(SimpleNamespace(callback_query=cb_inexistente), self.context)
        cb_inexistente.answer.assert_awaited_once()
        cb_inexistente.edit_message_text.assert_awaited_once()
        self.assertIn("expirou", cb_inexistente.edit_message_text.call_args.kwargs["text"].lower())


if __name__ == "__main__":
    unittest.main()
