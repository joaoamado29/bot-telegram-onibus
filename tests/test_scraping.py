from __future__ import annotations

import unittest
from pathlib import Path

from onibus.core import HorariosLinha, PontoHorario, parse_horarios

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class ScrapingParserTests(unittest.TestCase):
    """
    O que faz: Testa o extrator de dados HTML da página de horários da linha de ônibus.
    Por que foi feito assim: Garante que os horários, pontos e calendários sejam extraídos
    com exatidão da página web, ignorando anúncios e descartando formatos inválidos.
    """

    def setUp(self) -> None:
        fixture_path = FIXTURES_DIR / "horarios.html"
        self.html = fixture_path.read_text(encoding="utf-8")

    def test_parse_fixture_preserva_pontos_e_descarta_anuncios(self) -> None:
        """
        O que faz: Valida a extração completa da fixture representativa.
        Por que foi feito assim: Testa se os 3 pontos são extraídos na ordem correta,
        se anúncios (li.adInList) e textos inválidos foram excluídos, e se os 26 e 27
        horários dos terminais foram preservados sem truncamento.
        """
        linha = parse_horarios(self.html, 4, "Linha Expressa")

        # Verifica número e nome da linha
        self.assertEqual(linha.numero, 4)
        self.assertEqual(linha.nome, "Linha Expressa")

        # Verifica que exatamente 3 pontos com horários foram extraídos (h2 alheio sem horários foi ignorado)
        self.assertEqual(len(linha.pontos), 3)
        self.assertEqual(linha.pontos[0].endereco, "Terminal Papicu")
        self.assertEqual(linha.pontos[1].endereco, "Terminal Messejana")
        self.assertEqual(linha.pontos[2].endereco, "Rua São João")

        # Ponto 1 (Terminal Papicu): lista com exatamente 26 horários úteis (o item inválido e o anúncio foram descartados)
        uteis_ponto1 = linha.pontos[0].calendarios["uteis"]
        self.assertEqual(len(uteis_ponto1), 26)
        self.assertNotIn("INVALIDO", uteis_ponto1)
        self.assertNotIn("Publicidade", uteis_ponto1)
        self.assertEqual(uteis_ponto1[0], "05:00")
        self.assertEqual(uteis_ponto1[-1], "15:00")

        # Ponto 2 (Terminal Messejana): lista com exatamente 27 horários úteis
        uteis_ponto2 = linha.pontos[1].calendarios["uteis"]
        self.assertEqual(len(uteis_ponto2), 27)
        self.assertNotIn("Anúncio do patrocinador", uteis_ponto2)
        self.assertEqual(uteis_ponto2[0], "05:10")
        self.assertEqual(uteis_ponto2[-1], "15:40")

        # Ponto 3 (Rua São João): possui úteis e sábados, mas não possui domingos_feriados
        self.assertIn("uteis", linha.pontos[2].calendarios)
        self.assertIn("sabados", linha.pontos[2].calendarios)
        self.assertNotIn("domingos_feriados", linha.pontos[2].calendarios)

    def test_rejeita_menos_de_dois_pontos(self) -> None:
        """
        O que faz: Tenta analisar um HTML com apenas 1 ponto.
        Por que foi feito assim: A regra de negócio exige no mínimo 2 pontos obrigatórios.
        """
        html_um_ponto = """
        <h2>Ponto Único</h2>
        <p class="title_p">Dias úteis</p>
        <ul class="listaHorarios"><li>06:00</li><li>07:00</li></ul>
        """
        with self.assertRaises(ValueError) as ctx:
            parse_horarios(html_um_ponto, 10, "Linha Um Ponto")
        self.assertIn("dois a cinco pontos", str(ctx.exception))

    def test_rejeita_mais_de_cinco_pontos(self) -> None:
        """
        O que faz: Tenta analisar um HTML com 6 pontos.
        Por que foi feito assim: A estrutura de banco suporta até 5 pontos; mais de 5 deve
        gerar um erro estrutural observável para não truncar dados silenciosamente.
        """
        pontos_html = ""
        for i in range(1, 7):
            pontos_html += f"""
            <h2>Ponto {i}</h2>
            <p class="title_p">Dias úteis</p>
            <ul class="listaHorarios"><li>06:00</li><li>07:00</li></ul>
            """
        with self.assertRaises(ValueError) as ctx:
            parse_horarios(pontos_html, 99, "Linha Seis Pontos")
        self.assertIn("dois a cinco pontos", str(ctx.exception))

    def test_rejeita_primeiras_duas_colecoes_vazias_ou_ausentes(self) -> None:
        """
        O que faz: Tenta publicar quando o segundo ponto não tem horários para um calendário publicado.
        Por que foi feito assim: Cada calendário existente na linha exige obrigatoriamente os horários
        nos pontos 1 e 2.
        """
        html_sem_ponto2_domingo = """
        <h2>Ponto 1</h2>
        <p class="title_p">Dias úteis</p>
        <ul class="listaHorarios"><li>06:00</li></ul>
        <p class="title_p">Domingos e feriados</p>
        <ul class="listaHorarios"><li>08:00</li></ul>

        <h2>Ponto 2</h2>
        <p class="title_p">Dias úteis</p>
        <ul class="listaHorarios"><li>06:30</li></ul>
        """
        with self.assertRaises(ValueError) as ctx:
            parse_horarios(html_sem_ponto2_domingo, 50, "Linha Incompleta")
        self.assertIn("duas primeiras coleções são obrigatórias", str(ctx.exception))

    def test_deduplica_e_ordena_horarios(self) -> None:
        """
        O que faz: Passa horários repetidos e desordenados para verificar a normalização.
        Por que foi feito assim: Garante que horários repetidos sejam removidos e a lista
        fique estritamente cronológica.
        """
        html_desordenado = """
        <h2>Ponto Alpha</h2>
        <p class="title_p">Dias úteis</p>
        <ul class="listaHorarios"><li>14:00</li><li>08:00</li><li>14:00</li><li>10:00</li></ul>
        <h2>Ponto Beta</h2>
        <p class="title_p">Dias úteis</p>
        <ul class="listaHorarios"><li>09:00</li><li>07:00</li></ul>
        """
        linha = parse_horarios(html_desordenado, 20, "Linha Desordenada")
        self.assertEqual(linha.pontos[0].calendarios["uteis"], ("08:00", "10:00", "14:00"))


if __name__ == "__main__":
    unittest.main()
