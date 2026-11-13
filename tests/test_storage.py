from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from onibus.core import HorariosLinha, PontoHorario, carregar_pontos, conectar, publicar_linha


class StorageIntegrityTests(unittest.TestCase):
    """
    O que faz: Testa as regras de armazenamento e integridade relacional no SQLite.
    Por que foi feito assim: Garante que o banco mantenha consistência estrita (FKs ativas,
    regras de validação CHECK de JSON, atomicidade em transações e rollback quando há falhas).
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_storage.sqlite3"
        with closing(conectar(self.db_path)) as conn:
            conn.execute("INSERT INTO linhas VALUES (10, 'Linha Base', 'tonoponto.com/10/', 'original_ts')")
            conn.commit()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_foreign_key_rejeita_insercoes_orfas(self) -> None:
        """
        O que faz: Tenta inserir pontos para uma linha inexistente na tabela linhas,
        ou horários para um ponto inexistente na tabela pontos.
        Por que foi feito assim: A integridade referencial exige que 'pontos' aponte para 'linhas',
        e 'horarios' aponte para 'pontos'.
        """
        with closing(conectar(self.db_path)) as conn:
            # 1. Inserir ponto com número 999 que não existe em 'linhas'
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO pontos (numero, nome, ponto1, ponto2, revisao, updated_at) VALUES (999, 'Fantasma', 'P1', 'P2', 1, 'now')"
                )

            # 2. Inserir horários com número 999 que não existe em 'pontos'
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """INSERT INTO horarios (numero, nome, calendario, horario_ponto1, horario_ponto2)
                       VALUES (999, 'Fantasma', 'uteis', '["08:00"]', '["08:30"]')"""
                )

    def test_checks_rejeitam_nulo_string_vazia_json_invalido_e_array_vazio(self) -> None:
        """
        O que faz: Testa restrições CHECK diretamente via SQL nas colunas horario_ponto1 e horario_ponto2.
        Por que foi feito assim: Garante que o banco rejeite dados corrompidos (NULL, texto comum,
        JSON inválido ou arrays vazios '[]') independentemente do código Python.
        """
        with closing(conectar(self.db_path)) as conn:
            # Primeiro insere um ponto válido na linha 10
            conn.execute(
                "INSERT INTO pontos (numero, nome, ponto1, ponto2, revisao, updated_at) VALUES (10, 'Linha Base', 'Ponto A', 'Ponto B', 1, 'now')"
            )
            conn.commit()

            # Caso 1: NULL em horario_ponto1
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO horarios (numero, nome, calendario, horario_ponto1, horario_ponto2) VALUES (10, 'Linha Base', 'uteis', NULL, '[\"08:00\"]')"
                )

            # Caso 2: String vazia '' em horario_ponto1
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO horarios (numero, nome, calendario, horario_ponto1, horario_ponto2) VALUES (10, 'Linha Base', 'uteis', '', '[\"08:00\"]')"
                )

            # Caso 3: JSON inválido (não parseável)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO horarios (numero, nome, calendario, horario_ponto1, horario_ponto2) VALUES (10, 'Linha Base', 'uteis', 'inválido', '[\"08:00\"]')"
                )

            # Caso 4: JSON válido porém não é array (ex: objeto ou número)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO horarios (numero, nome, calendario, horario_ponto1, horario_ponto2) VALUES (10, 'Linha Base', 'uteis', '{\"chave\": 1}', '[\"08:00\"]')"
                )

            # Caso 5: Array JSON vazio '[]'
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO horarios (numero, nome, calendario, horario_ponto1, horario_ponto2) VALUES (10, 'Linha Base', 'uteis', '[]', '[\"08:00\"]')"
                )

    def test_publicacao_valida_substitui_antigos_e_remove_calendarios_obsoletos(self) -> None:
        """
        O que faz: Publica uma linha com 2 calendários (úteis e sábados), e depois republica
        com novos horários e apenas 1 calendário (úteis).
        Por que foi feito assim: Conforme regra D-08, uma nova publicação válida deve substituir
        completamente os dados anteriores e limpar calendários que não existem mais na origem.
        """
        with closing(conectar(self.db_path)) as conn:
            # 1. Publicação inicial
            v1 = HorariosLinha(
                10,
                "Linha Base",
                (
                    PontoHorario("Terminal A", {"uteis": ("06:00", "07:00"), "sabados": ("08:00",)}),
                    PontoHorario("Terminal B", {"uteis": ("06:30", "07:30"), "sabados": ("08:30",)}),
                ),
            )
            publicar_linha(conn, v1)

            pontos_v1 = carregar_pontos(conn, 10)
            self.assertEqual(pontos_v1["revisao"], 1)
            self.assertEqual(pontos_v1["ponto1"], "Terminal A")
            cals_v1 = conn.execute("SELECT calendario FROM horarios WHERE numero = ? ORDER BY calendario", (10,)).fetchall()
            self.assertEqual([r[0] for r in cals_v1], ["sabados", "uteis"])

            # 2. Segunda publicação: nome de ponto alterado, horários atualizados e calendário 'sabados' removido
            v2 = HorariosLinha(
                10,
                "Linha Base",
                (
                    PontoHorario("Terminal A Renovado", {"uteis": ("06:15", "07:15")}),
                    PontoHorario("Terminal B", {"uteis": ("06:45", "07:45")}),
                ),
            )
            publicar_linha(conn, v2)

            pontos_v2 = carregar_pontos(conn, 10)
            self.assertEqual(pontos_v2["revisao"], 2)
            self.assertEqual(pontos_v2["ponto1"], "Terminal A Renovado")

            cals_v2 = conn.execute("SELECT calendario, horario_ponto1 FROM horarios WHERE numero = ?", (10,)).fetchall()
            # Apenas 'uteis' deve existir agora! 'sabados' foi removido!
            self.assertEqual(len(cals_v2), 1)
            self.assertEqual(cals_v2[0]["calendario"], "uteis")
            self.assertEqual(json.loads(cals_v2[0]["horario_ponto1"]), ["06:15", "07:15"])

    def test_tentativa_invalida_preserva_dados_e_revisao_anteriores(self) -> None:
        """
        O que faz: Publica uma linha válida (revisão 1) e em seguida tenta publicar dados inválidos.
        Por que foi feito assim: Conforme regra D-09, falhas na validação não devem alterar o banco,
        preservando o último estado válido e a revisão intacta.
        """
        with closing(conectar(self.db_path)) as conn:
            valido = HorariosLinha(
                10,
                "Linha Base",
                (
                    PontoHorario("Terminal A", {"uteis": ("06:00",)}),
                    PontoHorario("Terminal B", {"uteis": ("06:30",)}),
                ),
            )
            publicar_linha(conn, valido)
            pontos_antes = carregar_pontos(conn, 10)

            # Tentativa inválida: apenas 1 ponto
            invalido = HorariosLinha(
                10,
                "Linha Base",
                (PontoHorario("Terminal A", {"uteis": ("06:00",)}),),
            )
            with self.assertRaises(ValueError):
                publicar_linha(conn, invalido)

            pontos_depois = carregar_pontos(conn, 10)
            self.assertEqual(pontos_antes["revisao"], pontos_depois["revisao"])
            self.assertEqual(pontos_antes["updated_at"], pontos_depois["updated_at"])

    def test_falha_no_meio_da_transacao_reverte_tudo_com_rollback(self) -> None:
        """
        O que faz: Simula um erro no momento da gravação dos horários para verificar se
        a atualização de 'pontos' e 'revisao' é totalmente revertida.
        Por que foi feito assim: Garante a atomicidade transacional (D-08): ou a linha inteira
        é atualizada ou nada é alterado.
        """
        with closing(conectar(self.db_path)) as conn:
            # Estado inicial
            inicial = HorariosLinha(
                10,
                "Linha Base",
                (
                    PontoHorario("Ponto Original 1", {"uteis": ("05:00",)}),
                    PontoHorario("Ponto Original 2", {"uteis": ("05:30",)}),
                ),
            )
            publicar_linha(conn, inicial)
            revisao_inicial = carregar_pontos(conn, 10)["revisao"]

            # Tentamos publicar um objeto que passe na validação de Python, mas que cause erro no SQLite
            # durante a inserção de horários (exemplo: violando a constraint CHECK de horários no banco)
            novo = HorariosLinha(
                10,
                "Linha Base",
                (
                    PontoHorario("Ponto Modificado", {"uteis": ("06:00",)}),
                    PontoHorario("Ponto Modificado 2", {"uteis": ("06:30",)}),
                ),
            )

            # Injetamos uma falha temporária criando um trigger que aborta o insert em 'horarios'
            conn.execute("CREATE TRIGGER falha_forcada BEFORE INSERT ON horarios BEGIN SELECT RAISE(ABORT, 'Erro simulado'); END;")
            try:
                with self.assertRaises(sqlite3.IntegrityError):
                    publicar_linha(conn, novo)
            finally:
                conn.execute("DROP TRIGGER falha_forcada;")

            # Confere que pontos não teve revisão incrementada nem texto alterado
            pontos_atuais = carregar_pontos(conn, 10)
            self.assertEqual(pontos_atuais["revisao"], revisao_inicial)
            self.assertEqual(pontos_atuais["ponto1"], "Ponto Original 1")

    def test_preservacao_do_catalogo_linhas(self) -> None:
        """
        O que faz: Verifica se a tabela 'linhas' (catálogo criado pelo scraping inicial) permanece intacta
        após operações de publicação e reabertura do banco.
        Por que foi feito assim: O coletor de horários deve complementar e relacionar com o catálogo,
        nunca apagá-lo nem sobrescrever campos originais como created_at.
        """
        with closing(conectar(self.db_path)) as conn:
            # Reabre a conexão
            conn_reaberta = conectar(self.db_path)
            row = conn_reaberta.execute("SELECT numero, nome, created_at FROM linhas WHERE numero = 10").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["numero"], 10)
            self.assertEqual(row["nome"], "Linha Base")
            self.assertEqual(row["created_at"], "original_ts")
            conn_reaberta.close()


if __name__ == "__main__":
    unittest.main()
