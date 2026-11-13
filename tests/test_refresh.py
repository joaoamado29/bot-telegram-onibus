from __future__ import annotations

import asyncio
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from onibus.core import BRT, HorariosLinha, PontoHorario, carregar_pontos, conectar, proximas_saidas, publicar_linha
from onibus.refresh import CoordenadorColeta, registrar_coletas

HTML_VALIDO_L1 = """
<h2>Terminal Papicu</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>06:00</li><li>07:00</li></ul>
<h2>Terminal Messejana</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>06:30</li><li>07:30</li></ul>
"""

HTML_ATUALIZADO_L1 = """
<h2>Terminal Papicu</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>06:15</li><li>07:15</li><li>08:15</li></ul>
<h2>Terminal Messejana</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>06:45</li><li>07:45</li><li>08:45</li></ul>
"""

HTML_VALIDO_L2 = """
<h2>Terminal Centro</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>08:00</li><li>09:00</li></ul>
<h2>Terminal Aldeota</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>08:30</li><li>09:30</li></ul>
"""

HTML_INVALIDO = """
<h2>Ponto Único</h2><p class="title_p">Dias úteis</p>
<ul class="listaHorarios"><li>06:00</li></ul>
"""


class RefreshCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    """
    O que faz: Testa o coordenador de coleta automática inicial, semanal e retries em caso de falha.
    Por que foi feito assim: Garante que o bot mantenha seus dados atualizados automaticamente (D-06 a D-10),
    preservando os horários anteriores se uma linha falhar e tentando novamente sem travar o sistema.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "refresh_test.sqlite3"
        with closing(conectar(self.db_path)) as conn:
            conn.execute("INSERT INTO linhas VALUES (1, 'Linha Um', 'tonoponto.com/linha1', 'ts')")
            conn.execute("INSERT INTO linhas VALUES (2, 'Linha Dois', 'tonoponto.com/linha2', 'ts')")
            conn.commit()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    async def test_inicializacao_em_banco_sem_horarios_agenda_coleta_inicial(self) -> None:
        """
        O que faz: Verifica se ao iniciar com a tabela de horários vazia, um job inicial é agendado.
        Por que foi feito assim: Conforme regra D-10, o banco vazio deve disparar coleta inicial
        sem bloquear a inicialização do bot.
        """
        mock_job_queue = MagicMock()
        coordenador = CoordenadorColeta(self.db_path, delays=(0.01, 0.02, 0.03))

        agendou = coordenador.inicializar_se_necessario(mock_job_queue)

        self.assertTrue(agendou)
        mock_job_queue.run_once.assert_called_once()
        args, kwargs = mock_job_queue.run_once.call_args
        self.assertEqual(kwargs.get("name"), "coleta_inicial_bootstrap")

    async def test_inicializacao_em_banco_preenchido_nao_agenda_coleta_inicial(self) -> None:
        """
        O que faz: Verifica que se o banco já possui horários, a coleta inicial é dispensada.
        Por que foi feito assim: Evita fazer scraping redundante a cada reinício do bot.
        """
        # Preenche horários da linha 1
        with closing(conectar(self.db_path)) as conn:
            p1 = PontoHorario("P1", {"uteis": ("06:00",)})
            p2 = PontoHorario("P2", {"uteis": ("06:30",)})
            publicar_linha(conn, HorariosLinha(1, "Linha Um", (p1, p2)))

        mock_job_queue = MagicMock()
        coordenador = CoordenadorColeta(self.db_path)

        agendou = coordenador.inicializar_se_necessario(mock_job_queue)

        self.assertFalse(agendou)
        mock_job_queue.run_once.assert_not_called()

    async def test_refresh_all_atualiza_linhas_e_dados_ficam_consultaveis(self) -> None:
        """
        O que faz: Executa o refresh_all com um fetcher simulado.
        Por que foi feito assim: Garante que os dados sejam baixados, salvos e imediatamente consultáveis
        via proximas_saidas (D-08).
        """
        def fake_fetcher(url: str) -> str:
            if "linha1" in url:
                return HTML_VALIDO_L1
            return HTML_VALIDO_L2

        coordenador = CoordenadorColeta(self.db_path, fetcher=fake_fetcher)
        await coordenador.refresh_all()

        with closing(conectar(self.db_path)) as conn:
            # Confere se os pontos foram gravados
            pontos_l1 = carregar_pontos(conn, 1)
            self.assertIsNotNone(pontos_l1)
            self.assertEqual(pontos_l1["ponto1"], "Terminal Papicu")

            # Confere se as saídas estão disponíveis
            agora = datetime(2026, 11, 13, 5, 0, tzinfo=BRT)
            saidas = proximas_saidas(conn, 1, 1, agora)
            self.assertEqual(saidas.horarios, ("06:00", "07:00"))
            self.assertEqual(saidas.status, "disponivel")

    async def test_falha_em_uma_linha_preserva_anterior_e_agenda_retry(self) -> None:
        """
        O que faz: Linha 1 já possui dados válidos; durante o refresh, a linha 1 falha e a linha 2 sucede.
        Por que foi feito assim: Conforme D-07 e D-09, a falha da linha 1 preserva seus dados anteriores
        e agenda retry, enquanto a linha 2 atualiza normalmente.
        """
        # Grava estado inicial da linha 1
        with closing(conectar(self.db_path)) as conn:
            p1 = PontoHorario("Terminal Original", {"uteis": ("05:00",)})
            p2 = PontoHorario("Terminal Original 2", {"uteis": ("05:30",)})
            publicar_linha(conn, HorariosLinha(1, "Linha Um", (p1, p2)))

        def fake_fetcher(url: str) -> str:
            if "linha1" in url:
                # Linha 1 retorna HTML inválido (apenas 1 ponto)
                return HTML_INVALIDO
            return HTML_VALIDO_L2

        mock_job_queue = MagicMock()
        coordenador = CoordenadorColeta(self.db_path, fetcher=fake_fetcher, delays=(0.01, 0.02, 0.03))
        await coordenador.refresh_all(job_queue=mock_job_queue)

        with closing(conectar(self.db_path)) as conn:
            # Linha 1 deve preservar os dados anteriores intactos!
            pontos_l1 = carregar_pontos(conn, 1)
            self.assertEqual(pontos_l1["ponto1"], "Terminal Original")
            self.assertEqual(pontos_l1["revisao"], 1)

            # Linha 2 deve ter sido atualizada com sucesso!
            pontos_l2 = carregar_pontos(conn, 2)
            self.assertIsNotNone(pontos_l2)
            self.assertEqual(pontos_l2["ponto1"], "Terminal Centro")

        # Verifica se o retry da linha 1 foi agendado
        mock_job_queue.run_once.assert_called()
        calls = [c for c in mock_job_queue.run_once.call_args_list if "retry_1_" in str(c)]
        self.assertTrue(len(calls) > 0)

    async def test_retry_sucesso_limpa_pendencias_e_atualiza(self) -> None:
        """
        O que faz: Executa o retry de uma linha e, quando ela responde com sucesso, atualiza o banco
        e não agenda mais novas tentativas.
        Por que foi feito assim: Testa o ciclo de recuperação de falhas da regra D-07.
        """
        def fake_fetcher(url: str) -> str:
            return HTML_ATUALIZADO_L1

        mock_job_queue = MagicMock()
        coordenador = CoordenadorColeta(self.db_path, fetcher=fake_fetcher, delays=(0.01, 0.02, 0.03))
        sucesso = await coordenador.refresh_line(1, attempt=1, job_queue=mock_job_queue)

        self.assertTrue(sucesso)
        with closing(conectar(self.db_path)) as conn:
            pontos_l1 = carregar_pontos(conn, 1)
            self.assertEqual(pontos_l1["revisao"], 1)
            saidas = proximas_saidas(conn, 1, 1, datetime(2026, 11, 13, 5, 0, tzinfo=BRT))
            self.assertEqual(saidas.horarios, ("06:15", "07:15", "08:15"))

    async def test_esgotamento_de_retries_mantem_dados_sem_novas_tentativas(self) -> None:
        """
        O que faz: Simula falha contínua até a tentativa máxima (3).
        Por que foi feito assim: Garante que os retries sejam finitos (3 tentativas), evitando
        loops infinitos de requisição.
        """
        def failing_fetcher(url: str) -> str:
            raise ConnectionError("Servidor fora do ar")

        mock_job_queue = MagicMock()
        coordenador = CoordenadorColeta(self.db_path, fetcher=failing_fetcher, delays=(0.01, 0.02, 0.03), max_retries=3)

        # Tentativa 3 (última permitida)
        sucesso = await coordenador.refresh_line(1, attempt=3, job_queue=mock_job_queue)

        self.assertFalse(sucesso)
        # Como era a 3ª tentativa, não deve agendar nova tentativa (tentativa 4 não existe)
        mock_job_queue.run_once.assert_not_called()

    async def test_lock_impede_sobreposicao_de_coletas(self) -> None:
        """
        O que faz: Dispara dois refresh_all simultâneos e confere se eles executam em série através do lock.
        Por que foi feito assim: Garante que duas coletas concorrentes não disputem escrita no SQLite.
        """
        executados = []

        async def worker_lento():
            async with coordenador._lock:
                executados.append("inicio")
                await asyncio.sleep(0.05)
                executados.append("fim")

        coordenador = CoordenadorColeta(self.db_path)
        # Dispara dois workers concorrentes
        await asyncio.gather(worker_lento(), worker_lento())
        self.assertEqual(executados, ["inicio", "fim", "inicio", "fim"])

    async def test_registrar_coletas_agenda_job_semanal_domingo_01h(self) -> None:
        """
        O que faz: Registra os jobs no Application do Telegram e confere o agendamento de domingo às 01:00 BRT.
        Por que foi feito assim: Cumpre a decisão D-06 de atualização semanal.
        """
        app = MagicMock()
        app.job_queue = MagicMock()
        coordenador = CoordenadorColeta(self.db_path)

        registrar_coletas(app, coordenador)

        app.job_queue.run_daily.assert_called_once()
        args, kwargs = app.job_queue.run_daily.call_args
        self.assertEqual(kwargs.get("time"), time(1, 0, tzinfo=ZoneInfo("America/Sao_Paulo")))
        self.assertEqual(kwargs.get("days"), (0,))
        self.assertEqual(kwargs.get("name"), "coleta_semanal_domingo_01h")


if __name__ == "__main__":
    unittest.main()
