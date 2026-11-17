from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from onibus.alertas import Alertas, ConsultaAlerta, Viagem, opcoes_antecedencia
from onibus.core import BRT


class AlertasTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.saida = datetime(2026, 11, 13, 12, tzinfo=BRT)
        consulta = ConsultaAlerta(11, 1, 1, self.saida.date(), ("12:00", "12:30"))
        self.viagem = Viagem(consulta, "011 - Circular Centro", self.saida, 101)
        self.outra = Viagem(consulta, self.viagem.linha, self.saida + timedelta(minutes=30), 101)
        self.alertas = Alertas()
        self.jobs = []
        self.fila = SimpleNamespace(run_once=self._adicionar)

    def _adicionar(self, callback, **kwargs):
        job = SimpleNamespace(callback=callback, schedule_removal=Mock(), **kwargs)
        self.jobs.append(job)
        return job

    def test_atalhos_limites_e_sequencias(self) -> None:
        self.assertEqual(opcoes_antecedencia(self.saida, self.saida - timedelta(minutes=17)), (10, 15))
        self.assertEqual(opcoes_antecedencia(self.saida, self.saida - timedelta(minutes=30)), (10, 15, 20, 30))
        self.assertEqual(opcoes_antecedencia(self.saida, self.saida - timedelta(minutes=10, seconds=-1)), (0,))
        self.assertEqual(opcoes_antecedencia(self.saida, self.saida), ())
        for minutos in (0, 15, 20, 30):
            with self.subTest(minutos=minutos):
                self.jobs.clear()
                self.assertTrue(self.alertas.agendar(self.fila, minutos, self.viagem, minutos, None))
                self.assertEqual(
                    [job.when for job in self.jobs],
                    [self.saida - timedelta(minutes=m) for m in range(minutos, -1, -5)],
                )

    async def test_substituicao_reverte_falha_e_descarta_jobs_obsoletos(self) -> None:
        self.assertTrue(self.alertas.agendar(self.fila, 1, self.viagem, 10, None))
        self.assertTrue(self.alertas.agendar(self.fila, 2, self.viagem, 0, None))
        anterior = self.alertas.ativos[1]
        independente = self.alertas.ativos[2]
        novo = SimpleNamespace(schedule_removal=Mock())
        fila_com_falha = SimpleNamespace(run_once=Mock(side_effect=[novo, RuntimeError("fila indisponível")]))
        with self.assertLogs("onibus.alertas", level="ERROR"):
            self.assertFalse(self.alertas.agendar(fila_com_falha, 1, self.outra, 10, anterior.identidade))
        novo.schedule_removal.assert_called_once()
        self.assertIs(self.alertas.ativos[1], anterior)
        for job in anterior.jobs:
            job.schedule_removal.assert_not_called()
        self.assertTrue(self.alertas.agendar(self.fila, 1, self.outra, 10, anterior.identidade))
        self.assertFalse(self.alertas.agendar(self.fila, 1, self.viagem, 10, anterior.identidade))
        self.assertIs(self.alertas.ativos[2], independente)
        bot = SimpleNamespace(send_message=AsyncMock())
        job = anterior.jobs[-1]
        job.schedule_removal.assert_called_once()
        await job.callback(SimpleNamespace(bot=bot, bot_data={}, job=job))
        bot.send_message.assert_not_called()
        self.assertEqual(self.alertas.ativos[1].viagem, self.outra)

    async def test_falha_no_aviso_final_libera_vaga(self) -> None:
        self.alertas.agendar(self.fila, 1, self.viagem, 0, None)
        bot = SimpleNamespace(send_message=AsyncMock(side_effect=RuntimeError("falha de envio")))
        job = self.jobs[0]
        with self.assertRaises(RuntimeError):
            await job.callback(SimpleNamespace(bot=bot, bot_data={}, job=job))
        self.assertNotIn(1, self.alertas.ativos)
