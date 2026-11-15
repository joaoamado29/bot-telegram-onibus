---
status: resolved
trigger: "Linha 004 / Terminal do Papicu mostra horários indisponíveis em 15/11/2026."
created: 2026-11-15
updated: 2026-11-15
---

## Current Focus

hypothesis: Confirmado que a indisponibilidade vem da ausência de domingos_feriados no banco; motivo de origem ainda não confirmado.
test: Comparação banco/origem limitada por acesso de rede.
expecting: Nova leitura autorizada da origem pode distinguir dados ausentes na publicação de dados perdidos/desatualizados no coletor.
next_action: Concluir diagnóstico imediato; retomar comparação com origem se GET autorizado retornar.
bug_class: Bohrbug
candidate_causes: data (origem sem calendário); code (parser perde calendário); environment (banco antigo).
and_gate: Não identificado; ausência de calendário basta para produzir indisponibilidade.

## Symptoms

expected: Consulta reflete horários publicados para ponto e data.
actual: 004 Terminal do Papicu retorna indisponível em 15/11/2026, feriado Proclamação da República; 011 e 012 normais.
errors: Nenhuma exceção relatada.
reproduction: Selecionar linha 004 e Terminal do Papicu em 15/11/2026.
started: Detectado durante UAT da fase 02.

## Eliminated

## Evidence

- Banco aberto com URI mode=ro; nenhuma alteração efetuada.
- Linha 004 revisão1 atualizada em 13/11/2026 possui dois pontos: Terminal da Messejana e Terminal do Papicu. Somente uma linha de horários: calendario uteis, 26 e 27 valores. Nenhuma linha domingos_feriados ou sabados.
- Linhas 011 e 012 possuem uteis, sabados e domingos_feriados, com listas não vazias nos dois pontos.
- proximas_saidas seleciona domingos_feriados para feriado/domingo e retorna indisponivel quando SELECT não encontra calendário. Contrato D-04 proíbe substituição por outro calendário.
- SBFL não aplicável: não há teste falhando com cobertura por teste; diagnóstico diferencial por dados.
- GET via ferramenta web recebeu HTTP403. GET pelo fetch do projeto falhou WinError10013 (permissão de socket no sandbox). Uma tentativa GET/parser com require_escalated ficou pendente de aprovação; não há observação do HTML atual e não se afirma que a origem publique apenas úteis.

## Resolution

Usuário confirmou em 2026-11-15 que a linha 004 realmente opera apenas em dias úteis. Comportamento correto, sem falha de coleta comprovada e sem necessidade de alterar banco, parser ou calendário. G-02-1 retirado das falhas do UAT por correção do relato.

root_cause: Causa imediata confirmada: não existe registro domingos_feriados para numero4 em horarios. A consulta de15/11/2026 seleciona domingos_feriados e retorna indisponivel conforme contrato D-04. Motivo upstream (origem ausente versus perda/coleta antiga) inconclusivo sem HTML atual.
fix: Não aplicado; diagnóstico somente.
verification: Reprodução por leitura do banco confirmada.
files_changed: [.planning/debug/linha004-calendario.md]

## Direção recomendada

- Não copiar horários úteis para domingo/feriado; D-04 proíbe fallback inventado.
- Quando a origem estiver acessível, comparar h2/p.title_p/ul.listaHorarios e saída de parse_horarios antes de planejar alteração de parser ou recoleção.
- Melhorar mensagem para explicar especificamente que o calendário de domingos/feriados não está cadastrado, se o usuário desejar clareza adicional.
