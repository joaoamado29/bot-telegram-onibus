from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from onibus.core import conectar
from onibus.search import PaginaSugestoes, buscar_sugestoes, normalizar_busca


class SearchTests(unittest.TestCase):
    """
    O que faz: Testa as funções de busca textual e normalização de linhas de ônibus.
    Por que foi feito assim: Garante que os passageiros encontrem linhas facilmente digitando
    apenas números ou partes do nome sem se preocupar com acentos ou maiúsculas/minúsculas (D-01 e D-04).
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "search_test.sqlite3"
        with closing(conectar(self.db_path)) as conn:
            # Insere linhas no catálogo
            conn.execute("INSERT INTO linhas VALUES (12, 'Linha Doze', 'tonoponto.com/12', 'ts')")
            conn.execute("INSERT INTO linhas VALUES (123, 'São João / Papicu Express', 'tonoponto.com/123', 'ts')")
            conn.execute("INSERT INTO linhas VALUES (300, 'Circular São Cristóvão', 'tonoponto.com/300', 'ts')")
            conn.execute("INSERT INTO linhas VALUES (400, 'Linha Sem Pontos', 'tonoponto.com/400', 'ts')")

            # Apenas 12, 123 e 300 têm pontos publicados; 400 não tem pontos!
            conn.execute(
                "INSERT INTO pontos (numero, nome, ponto1, ponto2, revisao, updated_at) VALUES (12, 'Linha Doze', 'P1', 'P2', 1, 'now')"
            )
            conn.execute(
                "INSERT INTO pontos (numero, nome, ponto1, ponto2, revisao, updated_at) VALUES (123, 'São João / Papicu Express', 'Ponto A', 'Ponto B', 1, 'now')"
            )
            conn.execute(
                "INSERT INTO pontos (numero, nome, ponto1, ponto2, revisao, updated_at) VALUES (300, 'Circular São Cristóvão', 'Ponto C', 'Ponto D', 1, 'now')"
            )
            conn.commit()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_normalizar_busca_remove_acentos_e_minusculas(self) -> None:
        """
        O que faz: Testa a normalização com caracteres acentuados, maiúsculas e cedilha.
        Por que foi feito assim: Verifica se 'São João' vira 'sao joao' para permitir buscas tolerantes a acentuação.
        """
        self.assertEqual(normalizar_busca("São João"), "sao joao")
        self.assertEqual(normalizar_busca("PAPICU"), "papicu")
        self.assertEqual(normalizar_busca("  Atenção! Ônibus  "), "atencao! onibus")

    def test_busca_por_numero_parcial(self) -> None:
        """
        O que faz: Busca pelo termo '12'.
        Por que foi feito assim: Deve encontrar tanto a linha 12 quanto a linha 123 que contém '12'.
        """
        pagina = buscar_sugestoes(self.db_path, "12", offset=0, limit=10)
        numeros = [r["numero"] for r in pagina.itens]
        self.assertIn(12, numeros)
        self.assertIn(123, numeros)
        self.assertNotIn(300, numeros)

    def test_busca_por_nome_sem_acentos_e_case_insensitive(self) -> None:
        """
        O que faz: Busca por 'joao' e 'JOAO' sem acentos para encontrar 'São João / Papicu Express'.
        Por que foi feito assim: Cumpre a decisão D-04 de busca agnóstica a maiúsculas e acentos.
        """
        pagina_min = buscar_sugestoes(self.db_path, "joao", offset=0, limit=10)
        self.assertEqual(len(pagina_min.itens), 1)
        self.assertEqual(pagina_min.itens[0]["numero"], 123)
        # O nome retornado deve preservar os acentos originais para exibição
        self.assertEqual(pagina_min.itens[0]["nome"], "São João / Papicu Express")

        pagina_mai = buscar_sugestoes(self.db_path, "JOAO", offset=0, limit=10)
        self.assertEqual(len(pagina_mai.itens), 1)
        self.assertEqual(pagina_mai.itens[0]["numero"], 123)

    def test_ignora_linhas_sem_pontos_publicados(self) -> None:
        """
        O que faz: Busca termo que corresponde a uma linha que existe no catálogo mas não tem pontos gravados.
        Por que foi feito assim: Linhas sem pontos não podem ser consultadas no Telegram, logo não devem
        aparecer nas sugestões inline.
        """
        pagina = buscar_sugestoes(self.db_path, "Sem Pontos", offset=0, limit=10)
        self.assertEqual(len(pagina.itens), 0)

    def test_termo_vazio_retorna_todas_linhas_com_pontos(self) -> None:
        """
        O que faz: Realiza a busca com termo vazio ''.
        Por que foi feito assim: Quando o usuário apenas aciona o bot sem digitar nada, deve mostrar
        a lista padrão de linhas disponíveis.
        """
        pagina = buscar_sugestoes(self.db_path, "", offset=0, limit=10)
        numeros = [r["numero"] for r in pagina.itens]
        self.assertEqual(numeros, [12, 123, 300])

    def test_paginacao_dez_por_pagina_com_next_offset(self) -> None:
        """
        O que faz: Cria 25 linhas com pontos e verifica se a paginação entrega 10, 10 e 5 itens,
        com next_offset adequado e vazio na última página.
        Por que foi feito assim: Cumpre a decisão D-05 de exibir 10 resultados por página com
        rolagem infinita no Telegram.
        """
        with closing(conectar(self.db_path)) as conn:
            for i in range(1001, 1026):  # 25 novas linhas
                conn.execute(f"INSERT INTO linhas VALUES ({i}, 'Linha Extra {i}', 'tonoponto.com/{i}', 'ts')")
                conn.execute(
                    f"INSERT INTO pontos (numero, nome, ponto1, ponto2, revisao, updated_at) VALUES ({i}, 'Linha Extra {i}', 'P1', 'P2', 1, 'now')"
                )
            conn.commit()

        # Página 1: offset 0 -> 10 itens, next_offset '10'
        p1 = buscar_sugestoes(self.db_path, "Extra", offset=0, limit=10)
        self.assertEqual(len(p1.itens), 10)
        self.assertEqual(p1.next_offset, "10")

        # Página 2: offset 10 -> 10 itens, next_offset '20'
        p2 = buscar_sugestoes(self.db_path, "Extra", offset=10, limit=10)
        self.assertEqual(len(p2.itens), 10)
        self.assertEqual(p2.next_offset, "20")

        # Página 3: offset 20 -> 5 itens restantes, next_offset vazio ""
        p3 = buscar_sugestoes(self.db_path, "Extra", offset=20, limit=10)
        self.assertEqual(len(p3.itens), 5)
        self.assertEqual(p3.next_offset, "")

    def test_offset_invalido_trata_com_seguranca(self) -> None:
        """
        O que faz: Envia offsets negativos ou strings maliciosas.
        Por que foi feito assim: Garante que offsets incorretos não causem erros de SQL nem travem o bot.
        """
        p_neg = buscar_sugestoes(self.db_path, "12", offset=-5, limit=10)
        self.assertEqual(len(p_neg.itens), 0)

        p_str = buscar_sugestoes(self.db_path, "12", offset="invalido", limit=10)
        self.assertEqual(len(p_str.itens), 0)


if __name__ == "__main__":
    unittest.main()
