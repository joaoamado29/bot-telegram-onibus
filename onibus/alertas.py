from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from secrets import token_urlsafe

from telegram.ext import ContextTypes

LOGGER = logging.getLogger(__name__)
ANTECEDENCIAS = (10, 15, 20, 30)


@dataclass(frozen=True)
class ConsultaAlerta:
    numero: int
    revisao: int
    ponto: int
    dia: date
    horarios: tuple[str, ...]


@dataclass(frozen=True)
class Viagem:
    consulta: ConsultaAlerta
    linha: str
    saida: datetime
    chat_id: int


@dataclass(frozen=True)
class Agendamento:
    identidade: str
    viagem: Viagem
    antecedencia: int
    jobs: tuple


def opcoes_antecedencia(saida: datetime, agora: datetime) -> tuple[int, ...]:
    if agora >= saida:
        return ()
    return tuple(m for m in ANTECEDENCIAS if saida - timedelta(minutes=m) >= agora) or (0,)


class Alertas:
    def __init__(self) -> None:
        self.ativos: dict[int, Agendamento] = {}
        self.etapas: dict[str, tuple[datetime, int | None, object]] = {}

    def guardar(self, agora: datetime, dono: int | None, dados: object) -> str:
        self.etapas = {token: etapa for token, etapa in self.etapas.items() if etapa[0] > agora}
        token = token_urlsafe(16)
        self.etapas[token] = (agora + timedelta(minutes=15), dono, dados)
        return token

    def obter(self, token: str, agora: datetime, dono: int | None = None) -> object | None:
        etapa = self.etapas.get(token)
        if etapa and etapa[0] > agora and etapa[1] == dono:
            return etapa[2]
        return None

    def ativo(self, dono: int, agora: datetime) -> Agendamento | None:
        atual = self.ativos.get(dono)
        if atual and agora > atual.viagem.saida + timedelta(seconds=15):
            del self.ativos[dono]
            self._remover(atual.jobs)
            return None
        return atual

    def agendar(self, fila, dono: int, viagem: Viagem, minutos: int, anterior: str | None) -> bool:
        atual = self.ativos.get(dono)
        if fila is None or (atual.identidade if atual else None) != anterior:
            return False
        identidade = token_urlsafe(16)
        jobs = []
        try:
            for restante in range(minutos, -1, -5):
                jobs.append(fila.run_once(
                    self._entregar,
                    when=viagem.saida - timedelta(minutes=restante),
                    data=(dono, identidade, viagem, restante),
                    job_kwargs={"misfire_grace_time": 15},
                ))
        except Exception:
            LOGGER.exception("Falha ao agendar alertas")
            self._remover(jobs)
            return False
        self.ativos[dono] = Agendamento(identidade, viagem, minutos, tuple(jobs))
        if atual:
            self._remover(atual.jobs)
        return True

    @staticmethod
    def _remover(jobs) -> None:
        for job in jobs:
            if getattr(job, "removed", False):
                continue
            try:
                job.schedule_removal()
            except Exception:
                LOGGER.exception("Falha ao remover tarefa de alerta")

    async def _entregar(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        dono, identidade, viagem, restante = context.job.data
        atual = self.ativos.get(dono)
        if atual is None or atual.identidade != identidade:
            return
        agora = context.bot_data.get("clock", lambda: datetime.now(viagem.saida.tzinfo))()
        if restante and agora >= viagem.saida:
            return
        if restante:
            await context.bot.send_message(viagem.chat_id, f"Faltam {restante} para o onibus!")
            return
        # Libera a vaga antes da chamada de rede, inclusive se a entrega falhar.
        del self.ativos[dono]
        await context.bot.send_message(viagem.chat_id, "Está no horário do ônibus!")
