from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from onibus.core import BRT, HorariosLinha, PontoHorario, conectar, proximas_saidas, publicar_linha
from onibus.holidays import feriados_em


class HolidaysCatalogTests(unittest.TestCase):
    def test_feriados_fixos_nacionais_estaduais_e_municipais(self) -> None:
        casos = (
            (date(2026, 1, 1), "Confraternização Universal", "Brasil"),
            (date(2026, 4, 21), "Tiradentes", "Brasil"),
            (date(2026, 5, 1), "Dia do Trabalho", "Brasil"),
            (date(2026, 9, 7), "Independência do Brasil", "Brasil"),
            (date(2026, 10, 12), "Nossa Senhora Aparecida", "Brasil"),
            (date(2026, 11, 2), "Finados", "Brasil"),
            (date(2026, 11, 15), "Proclamação da República", "Brasil"),
            (date(2026, 11, 20), "Dia Nacional de Zumbi e da Consciência Negra", "Brasil"),
            (date(2026, 12, 25), "Natal", "Brasil"),
            (date(2026, 3, 25), "Data Magna do Ceará", "Ceará"),
            (date(2026, 3, 19), "Dia de São José", "Fortaleza"),
            (date(2026, 8, 15), "Nossa Senhora da Assunção", "Fortaleza"),
        )
        for data, nome, jurisdicao in casos:
            with self.subTest(data=data, nome=nome):
                encontrados = feriados_em(data)
                por_nome = {item.nome: item for item in encontrados}
                self.assertIn(nome, por_nome)
                if nome in por_nome:
                    self.assertEqual(por_nome[nome].jurisdicao, jurisdicao)
                    self.assertTrue(por_nome[nome].fonte.startswith("https://"))

    def test_feriados_moveis_calculados_offline(self) -> None:
        self.assertIn("Sexta-feira da Paixão", [item.nome for item in feriados_em(date(2025, 4, 18))])
        self.assertIn("Corpus Christi", [item.nome for item in feriados_em(date(2025, 6, 19))])

    def test_feriados_coincidentes_preservam_todos_os_nomes(self) -> None:
        nomes = [item.nome for item in feriados_em(date(2079, 4, 21))]
        self.assertEqual(nomes, ["Tiradentes", "Sexta-feira da Paixão"])

    def test_feriado_excepcional_de_2026_nao_se_repete(self) -> None:
        feriado_2026 = feriados_em(date(2026, 4, 13))
        self.assertEqual(len(feriado_2026), 1)
        self.assertEqual(feriado_2026[0].nome, "Aniversário da Cidade de Fortaleza")
        self.assertEqual(feriado_2026[0].ano, 2026)
        self.assertEqual(feriados_em(date(2027, 4, 13)), ())

    def test_ponto_facultativo_nao_e_feriado(self) -> None:
        self.assertEqual(feriados_em(date(2026, 2, 16)), ())

    def test_mudanca_de_ano_e_novas_datas_moveis(self) -> None:
        self.assertEqual(feriados_em(date(2026, 12, 31)), ())
        self.assertEqual(feriados_em(date(2027, 1, 1))[0].nome, "Confraternização Universal")
        self.assertIn("Sexta-feira da Paixão", [f.nome for f in feriados_em(date(2026, 4, 3))])
        self.assertIn("Corpus Christi", [f.nome for f in feriados_em(date(2026, 6, 4))])


class SchedulesTemporalTests(unittest.TestCase):
    """
    O que faz: Testa as consultas temporais de próximas saídas de ônibus.
    Por que foi feito assim: Garante que os horários sejam calculados estritamente no fuso
    de Brasília (America/Sao_Paulo), respeitando o calendário do dia (úteis, sábados ou domingos),
    retornando saídas futuras sem misturar com o dia seguinte.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "schedules.sqlite3"
        with closing(conectar(self.db_path)) as conn:
            conn.execute("INSERT INTO linhas VALUES (100, 'Expresso Teste', 'tonoponto.com/100/', 'data')")
            # Linha com 3 pontos e calendários úteis, sábados e domingos
            ponto1 = PontoHorario(
                "Terminal 1",
                {
                    "uteis": ("06:00", "08:00", "12:00", "12:30", "13:00", "18:00", "23:50"),
                    "sabados": ("07:00", "12:00", "15:00"),
                    "domingos_feriados": ("08:00", "14:00"),
                },
            )
            ponto2 = PontoHorario(
                "Terminal 2",
                {
                    "uteis": ("06:30", "08:30", "12:15", "12:45", "18:30"),
                    "sabados": ("07:30", "12:30"),
                    "domingos_feriados": ("08:30", "14:30"),
                },
            )
            # Ponto 3 só opera em dias úteis
            ponto3 = PontoHorario(
                "Parada Intermediária",
                {
                    "uteis": ("07:00", "09:00", "12:30"),
                },
            )
            linha = HorariosLinha(100, "Expresso Teste", (ponto1, ponto2, ponto3))
            publicar_linha(conn, linha)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_instante_estritamente_futuro_limite_12(self) -> None:
        """
        O que faz: Testa o instante exato da saída 12:00 em 11:59:59, 12:00:00 e 12:00:01.
        Por que foi feito assim: O critério técnico estrito determina que às 12:00:00 a saída de 12:00
        já expirou (deve ser estritamente maior que o instante atual).
        """
        with closing(conectar(self.db_path)) as conn:
            # Sexta-feira útil: 2026-11-13
            # 11:59:59 -> 12:00 ainda é futuro
            agora_antes = datetime(2026, 11, 13, 11, 59, 59, tzinfo=BRT)
            res_antes = proximas_saidas(conn, 100, 1, agora_antes)
            self.assertEqual(res_antes.horarios[:3], ("12:00", "12:30", "13:00"))
            self.assertEqual(res_antes.status, "disponivel")

            # 12:00:00 -> 12:00 não é mais futuro; próxima é 12:30
            agora_exato = datetime(2026, 11, 13, 12, 0, 0, tzinfo=BRT)
            res_exato = proximas_saidas(conn, 100, 1, agora_exato)
            self.assertEqual(res_exato.horarios[:3], ("12:30", "13:00", "18:00"))

            # 12:00:01 -> próxima é 12:30
            agora_depois = datetime(2026, 11, 13, 12, 0, 1, tzinfo=BRT)
            res_depois = proximas_saidas(conn, 100, 1, agora_depois)
            self.assertEqual(res_depois.horarios[:3], ("12:30", "13:00", "18:00"))

    def test_quantidade_de_saidas_retorna_ate_tres(self) -> None:
        """
        O que faz: Testa quando restam 2, 1 ou 0 saídas para hoje.
        Por que foi feito assim: A regra D-13 diz que se houver menos de 3 saídas,
        deve exibir apenas as restantes de hoje, sem buscar horários do dia seguinte.
        """
        with closing(conectar(self.db_path)) as conn:
            # Às 15:00 em dia útil, restam apenas duas saídas: 18:00 e 23:50
            agora_15h = datetime(2026, 11, 13, 15, 0, tzinfo=BRT)
            res_2 = proximas_saidas(conn, 100, 1, agora_15h)
            self.assertEqual(res_2.horarios, ("18:00", "23:50"))
            self.assertEqual(res_2.status, "disponivel")

            # Às 20:00, resta apenas uma saída: 23:50
            agora_20h = datetime(2026, 11, 13, 20, 0, tzinfo=BRT)
            res_1 = proximas_saidas(conn, 100, 1, agora_20h)
            self.assertEqual(res_1.horarios, ("23:50",))
            self.assertEqual(res_1.status, "disponivel")

            # Às 23:55 (final do dia), não há mais saídas hoje -> status 'encerrado'
            agora_fim = datetime(2026, 11, 13, 23, 55, tzinfo=BRT)
            res_0 = proximas_saidas(conn, 100, 1, agora_fim)
            self.assertEqual(res_0.horarios, ())
            self.assertEqual(res_0.status, "encerrado")

    def test_relogio_utc_converte_corretamente_para_brt(self) -> None:
        """
        O que faz: Fornece um datetime em UTC e confere se a consulta respeita o dia e horário em BRT.
        Por que foi feito assim: Servidores ou containers podem rodar com timezone UTC; a consulta
        não pode mudar de dia nem errar o cálculo em Brasília (UTC-3).
        """
        with closing(conectar(self.db_path)) as conn:
            # 2026-11-14 01:30 UTC equivale a 2026-11-13 22:30 BRT (ainda sexta-feira dia útil!)
            agora_utc = datetime(2026, 11, 14, 1, 30, tzinfo=ZoneInfo("UTC"))
            res = proximas_saidas(conn, 100, 1, agora_utc)
            self.assertEqual(res.data.isoformat(), "2026-11-13")
            self.assertEqual(res.calendario, "uteis")
            self.assertEqual(res.horarios, ("23:50",))

    def test_ponto_sem_calendario_retorna_indisponivel(self) -> None:
        """
        O que faz: Consulta o ponto 3 em um domingo (o ponto 3 só opera em dias úteis).
        Por que foi feito assim: Deve retornar status 'indisponivel' (pois o ponto não tem
        operação cadastrada nesse calendário), sem fingir que o serviço encerrou viagens existentes.
        """
        with closing(conectar(self.db_path)) as conn:
            # 2026-11-15 é Domingo
            domingo = datetime(2026, 11, 15, 10, 0, tzinfo=BRT)
            res = proximas_saidas(conn, 100, 3, domingo)
            self.assertEqual(res.calendario, "domingos_feriados")
            self.assertEqual(res.horarios, ())
            self.assertEqual(res.status, "indisponivel")

    def test_data_magna_em_dia_util_seleciona_domingo_feriado(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            quarta_data_magna = datetime(2026, 3, 25, 11, 0, tzinfo=BRT)
            res = proximas_saidas(conn, 100, 1, quarta_data_magna)

            self.assertEqual(res.calendario, "domingos_feriados")
            self.assertEqual(res.horarios, ("14:00",))
            self.assertEqual(getattr(res, "feriados", ()), ("Data Magna do Ceará",))

    def test_feriado_em_sabado_prevalece_sobre_calendario_de_sabados(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            sabado_feriado = datetime(2026, 8, 15, 9, 0, tzinfo=BRT)
            res = proximas_saidas(conn, 100, 1, sabado_feriado)

            self.assertEqual(res.calendario, "domingos_feriados")
            self.assertEqual(res.horarios, ("14:00",))
            self.assertEqual(res.feriados, ("Nossa Senhora da Assunção",))

    def test_lista_publicada_vazia_e_indisponivel_nao_encerrada(self) -> None:
        with closing(conectar(self.db_path)) as conn:
            conn.execute(
                "UPDATE horarios SET horario_ponto3 = '[]' WHERE numero = ? AND calendario = ?",
                (100, "uteis"),
            )
            res = proximas_saidas(conn, 100, 3, datetime(2026, 11, 13, 15, 0, tzinfo=BRT))

            self.assertEqual(res.status, "indisponivel")

    def test_valida_posicao_fechada_ponto(self) -> None:
        """
        O que faz: Passa posição de ponto inválida (ex: 0 ou 6).
        Por que foi feito assim: Garante que apenas posições válidas de 1 a 5 sejam aceitas.
        """
        with closing(conectar(self.db_path)) as conn:
            agora = datetime(2026, 11, 13, 10, 0, tzinfo=BRT)
            with self.assertRaises(ValueError):
                proximas_saidas(conn, 100, 0, agora)
            with self.assertRaises(ValueError):
                proximas_saidas(conn, 100, 6, agora)


if __name__ == "__main__":
    unittest.main()
