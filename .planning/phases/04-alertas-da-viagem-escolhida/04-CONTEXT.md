# Fase 4 — Alertas da viagem escolhida

**Discussão:** 2026-11-16  
**Status:** Pronta para planejamento

<domain>
## Escopo

Em **Notificar**, o passageiro escolhe uma das próximas saídas apresentadas para a linha e o ponto selecionados. Os alertas usam o horário de Brasília. Recuperação após reinício e cancelamento avulso pertencem à Fase 5.
</domain>

<decisions>
## Decisões

- **D-01.** Oferecer os atalhos **10 min**, **15 min**, **20 min** e **30 min**. Mostrar somente os que permitem enviar o primeiro aviso antes da saída. Após o primeiro aviso, enviar a contagem a cada cinco minutos até a mensagem final, usando os textos aprovados nos requisitos.
- **D-02.** Se a viagem ainda estiver no futuro e nenhum atalho couber, oferecer **Só no horário da saída** e informar “Está em cima da hora. Posso avisar no horário da saída.” Essa escolha agenda apenas a mensagem final.
- **D-03.** Manter um alerta ativo por passageiro. Ao tentar agendar outra viagem, oferecer **Substituir alerta**. Manter o alerta atual até que a substituição seja confirmada e a nova viagem possa ser agendada. Navegar pelo bot e tocar novamente em um botão não deve duplicar alertas nem afetar outros passageiros.
- **D-04.** Confirmar um agendamento bem-sucedido com “🔔 Alertas ativados para a linha <Número - Nome>.” Para uma antecedência, acrescentar “Você receberá avisos antes da saída.” Na modalidade final, usar “Você receberá um aviso no horário da saída.”
</decisions>

<canonical_refs>
## Referências

- `.planning/ROADMAP.md` — critérios da Fase 4.
- `.planning/REQUIREMENTS.md` — BOT-03, BOT-07 e ALERT-01 a ALERT-04.
- `.planning/phases/03-consulta-do-dia-seguinte/03-CONTEXT.md` — navegação e consulta do dia seguinte.
</canonical_refs>

<code_context>
## Código existente

- `onibus/telegram_handlers.py` monta o teclado das próximas saídas e valida os callbacks por linha, revisão e ponto.
- `onibus/refresh.py` já usa a fila de tarefas do bot para agendamentos.
</code_context>
