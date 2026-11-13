from __future__ import annotations

import asyncio
import logging
import sqlite3
from contextlib import closing
from datetime import datetime, time
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from onibus.core import BRT, LinhaOnibus, coletar_linha, conectar, publicar_linha
from scraping import SOURCE_URL, extract_linhas, insert_if_new

logger = logging.getLogger(__name__)


class CoordenadorColeta:
    """
    O que faz: Gerencia as atualizações de dados das linhas de ônibus (coleta inicial, atualização semanal
    e tentativas de recuperação com retry em caso de falhas).
    Por que foi feito assim: Conforme regras D-06 a D-10, o bot deve funcionar sem intervenção manual contínua,
    preservando sempre o último estado válido caso ocorra instabilidade na página web da operadora.
    """

    def __init__(
        self,
        db_path: str | Path,
        fetcher: Callable[[str], str] | None = None,
        clock: Callable[[], datetime] | None = None,
        delays: tuple[float, ...] = (300.0, 900.0, 3600.0),
        max_retries: int = 3,
    ) -> None:
        self.db_path = str(db_path)
        self.fetcher = fetcher
        self.clock = clock or (lambda: datetime.now(BRT))
        self.delays = delays
        self.max_retries = max_retries
        self._lock = asyncio.Lock()
        self._retries_ativos: set[int] = set()

    def inicializar_se_necessario(self, job_queue) -> bool:
        """
        O que faz: Verifica se o banco de horários está vazio e, se estiver, agenda uma coleta inicial.
        Por que foi feito assim: Regra D-10: não deixa o usuário sem dados na primeira execução,
        disparando a coleta em segundo plano sem travar o início imediato do bot.
        """
        with closing(conectar(self.db_path)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM horarios")
            total_horarios = cur.fetchone()[0]

        if total_horarios == 0 and job_queue is not None:
            job_queue.run_once(self._job_inicial, when=1.0, name="coleta_inicial_bootstrap")
            return True
        return False

    async def _job_inicial(self, context) -> None:
        """Dispara a coleta inicial agendada."""
        logger.info("Iniciando coleta automática inicial de horários...")
        await self.refresh_all(job_queue=context.job_queue)

    async def _job_semanal(self, context) -> None:
        """Dispara a coleta semanal de domingo às 01h."""
        logger.info("Iniciando ciclo semanal de atualização de horários...")
        await self.refresh_all(job_queue=context.job_queue)

    async def _job_retry(self, context) -> None:
        """Executa uma nova tentativa de coleta para uma linha com falha anterior."""
        data = context.job.data or {}
        numero = data.get("numero")
        attempt = data.get("attempt", 1)
        if numero is not None:
            await self.refresh_line(numero, attempt=attempt, job_queue=context.job_queue)

    async def refresh_all(self, job_queue=None) -> tuple[int, int]:
        """
        O que faz: Atualiza o catálogo geral de linhas e em seguida cada linha individualmente.
        Por que foi feito assim: Serializa a execução via lock assíncrono para evitar concorrência no SQLite,
        executa as requisições em threads separadas e agenda retries para as linhas que falharem (D-07/D-08).
        """
        async with self._lock:
            # 1. Atualiza o catálogo geral de linhas se possível
            linhas = await asyncio.to_thread(self._sincronizar_catalogo)
            sucessos = 0
            falhas = 0

            # 2. Atualiza os horários de cada linha
            for linha in linhas:
                ok = await asyncio.to_thread(self._coletar_e_publicar_uma_linha, linha["numero"], linha["nome"], linha["link"])
                if ok:
                    sucessos += 1
                    self._retries_ativos.discard(linha["numero"])
                else:
                    falhas += 1
                    if job_queue is not None and linha["numero"] not in self._retries_ativos:
                        self._retries_ativos.add(linha["numero"])
                        delay = self.delays[0] if self.delays else 300.0
                        job_queue.run_once(
                            self._job_retry,
                            when=delay,
                            data={"numero": linha["numero"], "attempt": 1},
                            name=f"retry_{linha['numero']}_1",
                        )

            logger.info("Ciclo de coleta finalizado: %d sucessos, %d falhas.", sucessos, falhas)
            return sucessos, falhas

    async def refresh_line(self, numero: int, attempt: int = 1, job_queue=None) -> bool:
        """
        O que faz: Atualiza uma única linha específica e gerencia os retries finitos.
        Por que foi feito assim: Conforme D-07, tenta até o limite configurado (padrão 3 tentativas a 5, 15 e 60 min)
        e limpa a fila de retries assim que a linha obtém sucesso.
        """
        async with self._lock:
            with closing(conectar(self.db_path)) as conn:
                row = conn.execute("SELECT numero, nome, link FROM linhas WHERE numero = ?", (numero,)).fetchone()

            if row is None:
                self._retries_ativos.discard(numero)
                return False

            ok = await asyncio.to_thread(self._coletar_e_publicar_uma_linha, row["numero"], row["nome"], row["link"])

            if ok:
                self._retries_ativos.discard(numero)
                logger.info("Linha %03d atualizada com sucesso no retry %d.", numero, attempt)
                return True

            logger.warning("Falha na tentativa %d da linha %03d.", attempt, numero)
            if attempt < self.max_retries and job_queue is not None:
                delay = self.delays[attempt] if attempt < len(self.delays) else self.delays[-1]
                job_queue.run_once(
                    self._job_retry,
                    when=delay,
                    data={"numero": numero, "attempt": attempt + 1},
                    name=f"retry_{numero}_{attempt + 1}",
                )
            else:
                self._retries_ativos.discard(numero)
                logger.error("Tentativas esgotadas para a linha %03d. Mantendo dados anteriores.", numero)
            return False

    def _sincronizar_catalogo(self) -> list[sqlite3.Row]:
        """
        O que faz: Baixa a página principal do Tonoponto e insere novas linhas encontradas no catálogo.
        Por que foi feito assim: Garante que novas linhas que surgirem no sistema sejam incluídas no banco
        sem sobrescrever a data de criação (created_at) das linhas preexistentes.
        """
        with closing(conectar(self.db_path)) as conn:
            if self.fetcher is not None:
                try:
                    html = self.fetcher(SOURCE_URL)
                    novas = extract_linhas(html, base_url=SOURCE_URL)
                    for l in novas:
                        insert_if_new(conn, l)
                except Exception as exc:
                    logger.warning("Não foi possível atualizar o catálogo geral: %s", exc)
            return conn.execute("SELECT numero, nome, link FROM linhas ORDER BY numero").fetchall()

    def _coletar_e_publicar_uma_linha(self, numero: int, nome: str, link: str) -> bool:
        """
        O que faz: Baixa o HTML dos horários de uma linha e grava no SQLite em transação atômica.
        Por que foi feito assim: Se o download falhar ou os dados forem inválidos (menos de 2 pontos,
        coleções obrigatórias vazias), o SQLite faz rollback e preserva os dados antigos da linha (D-08/D-09).
        """
        try:
            linha_obj = LinhaOnibus(numero=numero, nome=nome, link=link)
            if self.fetcher is not None:
                horarios = coletar_linha(linha_obj, fetcher=self.fetcher)
            else:
                horarios = coletar_linha(linha_obj)

            with closing(conectar(self.db_path)) as conn:
                publicar_linha(conn, horarios)
            return True
        except Exception as exc:
            logger.warning("Linha %03d falhou na coleta/publicação (%s); mantendo estado anterior.", numero, exc)
            return False


def registrar_coletas(application, coordenador: CoordenadorColeta) -> None:
    """
    O que faz: Conecta o coordenador de coleta ao ciclo de vida e ao JobQueue do bot Telegram.
    Por que foi feito assim: Registra o job semanal (domingo às 01:00 horário de Brasília)
    e dispara a verificação de inicialização automática se o banco estiver sem horários (D-06 e D-10).
    """
    if application.job_queue is not None:
        # Domingo às 01:00 horário de Brasília (America/Sao_Paulo)
        application.job_queue.run_daily(
            coordenador._job_semanal,
            time=time(1, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
            days=(0,),
            name="coleta_semanal_domingo_01h",
        )
        coordenador.inicializar_se_necessario(application.job_queue)
