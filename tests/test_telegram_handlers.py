from __future__ import annotations

import tempfile
import re
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from onibus.core import BRT, HorariosLinha, PontoHorario, conectar, publicar_linha, proximas_saidas
from onibus.telegram_handlers import build_application, inline_query, ponto_callback, start, _consultar


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

    async def _clique(self, data):
        callback = SimpleNamespace(data=data, answer=AsyncMock(), edit_message_text=AsyncMock())
        await ponto_callback(SimpleNamespace(callback_query=callback), self.context)
        return callback

    def _assert_buscar_outra_linha(self, markup) -> None:
        botoes = [botao for linha in markup.inline_keyboard for botao in linha]
        busca = [botao for botao in botoes if botao.text == "Buscar outra linha"]
        self.assertEqual(len(busca), 1)
        self.assertEqual(busca[0].switch_inline_query_current_chat, "")
        self.assertIsNone(busca[0].callback_data)

    async def test_buscar_outra_linha_em_pontos_consultas_e_retorno(self) -> None:
        query = SimpleNamespace(query="11", offset="", answer=AsyncMock())
        await inline_query(SimpleNamespace(inline_query=query), self.context)
        artigo = query.answer.call_args.kwargs["results"][0]
        self._assert_buscar_outra_linha(artigo.reply_markup)

        for data in ("p:11:1:1", "b:11:1", "h:11:1:1:20261113:0", "h:11:1:1:20261114:0"):
            with self.subTest(data=data):
                callback = await self._clique(data)
                self._assert_buscar_outra_linha(callback.edit_message_text.call_args.kwargs["reply_markup"])

        for instante in (datetime(2026, 11, 13, 23, tzinfo=BRT), datetime(2026, 11, 14, 9, tzinfo=BRT)):
            with self.subTest(instante=instante):
                self.context.bot_data["clock"] = lambda: instante
                callback = await self._clique("p:11:1:1")
                self._assert_buscar_outra_linha(callback.edit_message_text.call_args.kwargs["reply_markup"])

    async def test_ver_horarios_inclui_passados_e_preserva_data(self) -> None:
        self.context.bot_data["clock"] = lambda: datetime(2026, 11, 13, 11, 15, tzinfo=BRT)
        callback = await self._clique("p:11:1:1")
        resposta = callback.edit_message_text.call_args.kwargs
        botoes = [b for row in resposta.get("reply_markup", SimpleNamespace(inline_keyboard=[])).inline_keyboard for b in row]
        self.assertIn("Ver horários", [b.text for b in botoes])
        data = next(b.callback_data for b in botoes if b.text == "Ver horários")
        self.context.bot_data["clock"] = lambda: datetime(2026, 11, 14, 1, tzinfo=BRT)
        completo = await self._clique(data)
        texto = completo.edit_message_text.call_args.kwargs["text"]
        self.assertEqual(re.findall(r"\b\d{2}:\d{2}\b", texto), ["10:00", "11:00", "12:00"])
        self.assertIn("13/11/2026", texto)
        self.assertIn("Dias úteis", texto)

    async def test_lista_extensa_pagina_sem_perdas(self) -> None:
        valores = tuple(f"{h:02d}:{m:02d}" for h in range(24) for m in range(60))
        with closing(conectar(self.db_path)) as conn:
            publicar_linha(conn, HorariosLinha(11, "Circular Centro", (PontoHorario("Terminal A", {"uteis": valores}), PontoHorario("Terminal B", {"uteis": valores}))))
        callback = await self._clique("p:11:2:1")
        resposta = callback.edit_message_text.call_args.kwargs
        botoes = [b for row in resposta.get("reply_markup", SimpleNamespace(inline_keyboard=[])).inline_keyboard for b in row]
        self.assertIn("Ver horários", [b.text for b in botoes])
        data = next(b.callback_data for b in botoes if b.text == "Ver horários")
        encontrados = []
        for _ in range((len(valores) + 27) // 28):
            pagina = await self._clique(data)
            resposta = pagina.edit_message_text.call_args.kwargs
            self.assertLessEqual(len(resposta["text"]), 4096)
            self.assertIn("Terminal A", resposta["text"])
            horarios_pagina = re.findall(r"\b\d{2}:\d{2}\b", resposta["text"])
            self.assertLessEqual(len(horarios_pagina), 28)
            encontrados.extend(horarios_pagina)
            botoes = [b for row in resposta["reply_markup"].inline_keyboard for b in row]
            self._assert_buscar_outra_linha(resposta["reply_markup"])
            self.assertIn("Voltar", [botao.text for botao in botoes])
            proximo = next((b for b in botoes if b.text == "Próxima"), None)
            if proximo is None:
                break
            data = proximo.callback_data
        self.assertEqual(encontrados, list(valores))

    async def test_voltar_reconstroi_enderecos_e_permite_outro_ponto(self) -> None:
        inicio = await self._clique("p:11:1:1")
        botoes = [b for row in inicio.edit_message_text.call_args.kwargs["reply_markup"].inline_keyboard for b in row]
        retorno = await self._clique(next(b.callback_data for b in botoes if b.text == "Voltar"))
        resposta = retorno.edit_message_text.call_args.kwargs
        self.assertIn("Terminal A", resposta["text"])
        self.assertIn("Terminal B", resposta["text"])
        outro = await self._clique(resposta["reply_markup"].inline_keyboard[1][0].callback_data)
        self.assertIn("Terminal B", outro.edit_message_text.call_args.kwargs["text"])
        self.assertNotIn("Terminal A", outro.edit_message_text.call_args.kwargs["text"])

    async def test_callbacks_navegacao_invalidos_nao_editam(self) -> None:
        for data in ("p:11:1:0", "p:11:1:6", "h:11:1:1:20261113:-1", "h:11:1:1:20261113:9999", "h:11:1:1:20260231:0", "x:11:1", "b:11:1:extra", None, 123):
            with self.subTest(data=data):
                callback = await self._clique(data)
                callback.edit_message_text.assert_not_awaited()

    async def test_data_e_pagina_invalidas_explicam_erro(self) -> None:
        for data in ("h:11:1:1:20260231:0", "h:11:1:1:20261113:9999"):
            callback = await self._clique(data)
            callback.answer.assert_awaited_once()
            self.assertTrue(callback.answer.call_args.args)
            self.assertTrue(callback.answer.call_args.kwargs["show_alert"])

    async def test_cabecalho_longo_que_cabe_abre_lista(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            conn.execute("UPDATE pontos SET ponto1=? WHERE numero=11", ("A" * 3950,))
            conn.commit()
        inicial = await self._clique("p:11:1:1")
        self.assertLessEqual(len(inicial.edit_message_text.call_args.kwargs["text"]), 4096)
        lista = await self._clique("h:11:1:1:20261113:0")
        lista.edit_message_text.assert_awaited_once()
        self.assertLessEqual(len(lista.edit_message_text.call_args.kwargs["text"]), 4096)
        self.assertIn("A" * 3950, lista.edit_message_text.call_args.kwargs["text"])

    async def test_identificacao_excessiva_informa_erro(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            conn.execute("UPDATE pontos SET ponto1=? WHERE numero=11", ("A" * 4100,))
            conn.commit()
        callback = await self._clique("h:11:1:1:20261113:0")
        callback.edit_message_text.assert_not_awaited()
        callback.answer.assert_awaited_once()
        self.assertTrue(callback.answer.call_args.args)
        self.assertTrue(callback.answer.call_args.kwargs["show_alert"])

    def test_consulta_mantem_snapshot_durante_publicacao(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
        def publicar_durante_consulta(conn, numero, posicao, agora):
            with closing(conectar(self.db_path)) as escrita:
                publicar_linha(escrita, HorariosLinha(11, "Nova linha", (
                    PontoHorario("Terminal NOVO", {"uteis": ("13:00",)}),
                    PontoHorario("Outro NOVO", {"uteis": ("13:30",)}),
                )))
            return proximas_saidas(conn, numero, posicao, agora)
        with patch("onibus.telegram_handlers.proximas_saidas", side_effect=publicar_durante_consulta):
            consulta = _consultar(self.db_path, 11, 1, 1, datetime(2026, 11, 13, 9, tzinfo=BRT))
        self.assertEqual(consulta.endereco, "Terminal A")
        self.assertEqual(consulta.horarios, ("10:00", "11:00", "12:00"))

    async def test_navegacao_obsoleta_nao_exibe_horarios_ou_enderecos(self) -> None:
        for data in ("b:11:0", "h:11:0:1:20261113:0", "h:999:1:1:20261113:0", "h:11:1:5:20261113:0"):
            with self.subTest(data=data):
                callback = await self._clique(data)
                texto = callback.edit_message_text.call_args.kwargs["text"]
                self.assertIn("expirou", texto)
                self.assertNotIn("Terminal", texto)

    async def test_ver_horarios_feriado_e_indisponibilidade(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            conn.execute("INSERT INTO horarios (numero,nome,calendario,horario_ponto1,horario_ponto2) VALUES (11,'Circular Centro','domingos_feriados','[\"08:00\",\"14:00\"]','[\"08:30\"]')")
            conn.commit()
        feriado = await self._clique("h:11:1:1:20260325:0")
        texto = feriado.edit_message_text.call_args.kwargs["text"]
        self.assertIn("Data Magna do Ceará", texto)
        self.assertEqual(re.findall(r"\b\d{2}:\d{2}\b", texto), ["08:00", "14:00"])
        ausente = await self._clique("h:11:1:1:20261114:0")
        texto = ausente.edit_message_text.call_args.kwargs["text"]
        self.assertIn("indisponíveis", texto)
        self.assertNotIn("terminaram", texto)

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
        # Dois pontos preservados e uma ação adicional para buscar outra linha.
        botoes = artigo.reply_markup.inline_keyboard
        self.assertEqual(len(botoes), 3)
        self.assertEqual(botoes[0][0].callback_data, "p:11:1:1")
        self.assertEqual(botoes[1][0].callback_data, "p:11:1:2")
        self._assert_buscar_outra_linha(artigo.reply_markup)

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

    async def test_callback_em_feriado_mostra_nome_e_data(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO horarios
                (numero, nome, calendario, horario_ponto1, horario_ponto2)
                VALUES (?, ?, ?, ?, ?)""",
                (11, "Circular Centro", "domingos_feriados", '["08:00", "14:00"]', '["08:30", "14:30"]'),
            )
        self.context.bot_data["clock"] = lambda: datetime(2026, 3, 25, 11, 0, tzinfo=BRT)
        callback = SimpleNamespace(
            data="p:11:1:1",
            inline_message_id="msg-inline-feriado",
            message=None,
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )

        await ponto_callback(SimpleNamespace(callback_query=callback), self.context)

        texto = callback.edit_message_text.call_args.kwargs["text"]
        self.assertIn("Data Magna do Ceará", texto)
        self.assertIn("25/03/2026", texto)

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
