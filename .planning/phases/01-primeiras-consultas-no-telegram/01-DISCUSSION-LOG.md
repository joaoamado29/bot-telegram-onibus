# Phase 1: Primeiras consultas no Telegram - Discussion Log

> Registro para auditoria humana. Pesquisa e planejamento devem consumir `01-CONTEXT.md`.

**Date:** 2026-11-13
**Phase:** 1-Primeiras consultas no Telegram
**Areas discussed:** Escolha da linha; atualização dos dados

## Escolha da linha

| Pergunta | Alternativas apresentadas | Escolha |
|----------|--------------------------|---------|
| Busca desejada | Resposta livre na seleção das áreas | Número ou parte do nome com autocomplete |
| Experiência Telegram | Sugestões inline / busca enviando mensagem | Inline com `@NomeDoBot` e termo |
| Após escolher linha | Mostrar endereços / resumo e botão Escolher ponto | Mostrar endereços diretamente |
| Acentos e maiúsculas | Ignorar / escrita exata | Ignorar |
| Muitos resultados | Dez e carregar ao rolar / dez e pedir refinamento | Dez por página e mais ao rolar |
| Continuar nesta área | Detalhar mais / seguir atualização | Seguir |

Exemplo fornecido: linha `123 - papicu/rua doidinho da silva`; buscas `12` e `papicu` geram sugestões correspondentes.

## Atualização dos dados

| Pergunta | Alternativas apresentadas | Escolha |
|----------|--------------------------|---------|
| Quando coletar | Resposta livre na seleção das áreas | Domingo às 01:00; confirmado como Brasília |
| Falha de linha | Manter e tentar novamente / manter até domingo / indisponibilizar | Manter últimos dados válidos e tentar mais tarde |
| Mudanças de horários | Substituir após validação / apenas acrescentar | Substituir conjunto válido e remover ausentes na origem |
| Primeira ou segunda lista vazia | Rejeitar linha e continuar / interromper toda coleta | Rejeitar linha, preservar dados válidos e continuar |
| Primeira execução sem horários | Coleta automática / coleta manual | Coleta inicial automática |
| Encerramento da discussão | Detalhar mais / registrar contexto | Registrar contexto |

## Discricionariedade técnica

Não foram aprovados valores específicos para intervalo e limite de retry, esquema de identidade, formato de serialização, ranking de sugestões nem entrada vazia. Esses pontos devem ser resolvidos tecnicamente no planejamento, preservando as preferências registradas.

## Deferred Ideas

Nenhuma nova capacidade fora do escopo foi solicitada.
