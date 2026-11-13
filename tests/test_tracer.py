from __future__ import annotations

import importlib
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

try:
    core = importlib.import_module("onibus.core")
    handlers = importlib.import_module("onibus.telegram_handlers")
except ModuleNotFoundError:
    core = handlers = None

HTML = """<h2>Terminal Papicu</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>12:00</li><li class="adInList">Anúncio</li><li>12:30</li><li>13:00</li><li>14:00</li></ul>
<h2>Rua São João</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>12:10</li><li>12:40</li><li>13:10</li></ul>"""


class TracerTests(unittest.IsolatedAsyncioTestCase):
    async def test_html_sqlite_inline_callback(self):
        self.assertIsNotNone(core, "O caminho de consulta real deve estar implementado")
        self.assertIsNotNone(handlers)
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "test.sqlite3"
            with core.conectar(db) as conn:
                conn.execute("INSERT INTO linhas VALUES (?, ?, ?, ?)", (123, "Papicu/São João", "tonoponto.com/linha/", "original"))
                conn.commit()
                horarios = core.parse_horarios(HTML, 123, "Papicu/São João")
                core.publicar_linha(conn, horarios)
                self.assertEqual(conn.execute("SELECT created_at FROM linhas").fetchone()[0], "original")
                resultado = core.proximas_saidas(conn, 123, 1, datetime(2026, 11, 13, 11, 0, tzinfo=ZoneInfo("America/Sao_Paulo")))
                self.assertEqual(resultado.horarios, ("12:00", "12:30", "13:00"))
            context = SimpleNamespace(bot_data={"db_path": db, "clock": lambda: datetime(2026, 11, 13, 11, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))})
            query = SimpleNamespace(query="123", offset="", answer=AsyncMock())
            await handlers.inline_query(SimpleNamespace(inline_query=query), context)
            article = query.answer.call_args.kwargs["results"][0]
            self.assertIn("Terminal Papicu", article.input_message_content.message_text)
            callback = SimpleNamespace(data=article.reply_markup.inline_keyboard[0][0].callback_data, inline_message_id="inline-only", message=None, answer=AsyncMock(), edit_message_text=AsyncMock())
            await handlers.ponto_callback(SimpleNamespace(callback_query=callback), context)
            self.assertIn("12:00", callback.edit_message_text.call_args.kwargs["text"])
            callback.answer.assert_awaited()

    async def test_constraints_and_invalid_publication(self):
        self.assertIsNotNone(core, "As restrições reais devem estar implementadas")
        with core.conectar(":memory:") as conn:
            conn.execute("INSERT INTO linhas VALUES (123, 'Papicu', 'tonoponto.com/linha/', 'original')")
            conn.commit()
            valid = core.parse_horarios(HTML, 123, "Papicu")
            core.publicar_linha(conn, valid)
            with self.assertRaises(ValueError):
                core.publicar_linha(conn, core.HorariosLinha(123, "Papicu", (core.PontoHorario("Um", {"uteis": ("12:00",)}),)))
            self.assertEqual(core.carregar_pontos(conn, 123)["revisao"], 1)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE horarios SET horario_ponto1 = '[]'")
            conn.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO pontos (numero,nome,ponto1,ponto2,revisao,updated_at) VALUES (999,'X','A','B',1,'now')")

    async def test_start_and_application_registration(self):
        self.assertIsNotNone(handlers, "O adaptador Telegram deve existir")
        message = SimpleNamespace(reply_text=AsyncMock())
        await handlers.start(SimpleNamespace(effective_message=message), SimpleNamespace())
        markup = message.reply_text.call_args.kwargs["reply_markup"]
        self.assertEqual(markup.inline_keyboard[0][0].switch_inline_query_current_chat, "")
        app = handlers.build_application("123456:development-token", ":memory:")
        self.assertEqual(len(app.handlers[0]), 3)


if __name__ == "__main__":
    unittest.main()
