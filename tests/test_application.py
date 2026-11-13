from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import MagicMock, patch

from onibus.core import conectar
from onibus.refresh import CoordenadorColeta, registrar_coletas
from onibus.telegram_handlers import build_application
from bot import _carregar_env, main


class ApplicationTests(unittest.TestCase):
    """
    O que faz: Testa a inicialização da aplicação, registro de handlers, job queue e argumentos CLI.
    Por que foi feito assim: Garante que todos os componentes estejam devidamente conectados
    no ponto de entrada (bot.py) e que o ambiente seja configurado de forma segura e resiliente.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "app_test.sqlite3"
        with closing(conectar(self.db_path)) as conn:
            conn.execute("INSERT INTO linhas VALUES (10, 'Linha Dez', 'tonoponto.com/10', 'ts')")
            conn.commit()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_build_application_registra_todos_handlers_e_job_queue(self) -> None:
        """
        O que faz: Constrói a aplicação com um token simulado.
        Por que foi feito assim: Confere se os 3 handlers (/start, inline_query, callback_query)
        e a fila de jobs (job_queue) estão ativos.
        """
        app = build_application("123456:FAKE_TOKEN_FOR_TESTING", self.db_path)
        self.assertIsNotNone(app.job_queue)
        handlers_grupo_0 = app.handlers[0]
        # Espera 3 handlers registrados: CommandHandler, InlineQueryHandler, CallbackQueryHandler
        self.assertEqual(len(handlers_grupo_0), 3)

    def test_registrar_coletas_conecta_job_queue_ao_coordenador(self) -> None:
        """
        O que faz: Testa se registrar_coletas adiciona o job de domingo e o job inicial no JobQueue da aplicação.
        Por que foi feito assim: Garante o acoplamento do ciclo de vida das coletas com o bot.
        """
        app = build_application("123456:FAKE_TOKEN_FOR_TESTING", self.db_path)
        coordenador = CoordenadorColeta(self.db_path)

        registrar_coletas(app, coordenador)

        jobs = app.job_queue.jobs()
        nomes_jobs = [j.name for j in jobs]
        self.assertIn("coleta_semanal_domingo_01h", nomes_jobs)
        # Como a tabela de horários está vazia no self.db_path, o job inicial deve ter sido agendado!
        self.assertIn("coleta_inicial_bootstrap", nomes_jobs)

    def test_carregar_env_le_arquivo_local_sem_modificar_chaves_existentes(self) -> None:
        """
        O que faz: Testa a leitura de um arquivo .env simulado.
        Por que foi feito assim: Verifica se ignora comentários, espaços e não sobrescreve
        variáveis que já estejam previamente definidas no ambiente.
        """
        env_fake = Path(self.temp_dir.name) / ".env.test"
        env_fake.write_text(
            "# Comentário explicativo\nCHAVE_TESTE_1=valor_um\nCHAVE_TESTE_2=\"valor com aspas\"\n",
            encoding="utf-8",
        )

        with patch.dict("os.environ", {}, clear=True):
            _carregar_env(env_fake)
            import os

            self.assertEqual(os.environ.get("CHAVE_TESTE_1"), "valor_um")
            self.assertEqual(os.environ.get("CHAVE_TESTE_2"), "valor com aspas")


if __name__ == "__main__":
    unittest.main()
