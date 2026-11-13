# Project Research Summary

**Project:** Bot Telegram Ônibus
**Domain:** Scraping de horários de ônibus, consulta Telegram e alertas por viagem
**Researched:** 2026-11-13
**Confidence:** MEDIUM

## Executive Summary

O projeto estende o coletor Python e o SQLite existentes com consulta de horários por linha e endereço e lembretes pelo Telegram. Recomenda-se um monólito modular: coleta independente dos handlers, parser testado com HTML real, consultas com relógio/calendário explícitos e um serviço de alertas. Python, requests e Beautiful Soup podem ser mantidos; python-telegram-bot com JobQueue cobre a interação e os disparos. Nenhuma dessas recomendações representa código implementado ou dependências já instaladas.

A inspeção real registrada em `ARCHITECTURE.md` confirmou 379 links no catálogo de Fortaleza/ETUFOR. Nas linhas 004, 011 e 012, os dados seguem `h2` de ponto, `p.title_p` de calendário e `ul.listaHorarios > li`; existem itens de publicidade que devem ser descartados. A linha 004 publica 26 horários em um ponto e 27 no outro. Portanto, listas de pontos diferentes não podem ser combinadas pelo índice como se cada posição identificasse uma mesma viagem. A amostra cobre três páginas, sem garantir uniformidade de todo o catálogo.

O principal gate de modelagem é preservar as duas tabelas amplas solicitadas e os dois primeiros campos de horário obrigatórios sem fabricar correspondências. Recomenda-se discutir coleções independentes por ponto e calendário, possivelmente JSON validado em cada coluna; essa representação ainda depende de aprovação do usuário. Calendário de feriados, recuperação de alertas após reinício e antecedências fora de múltiplos de cinco também exigem decisões explícitas antes de fechar os requisitos. O roadmap deve resolver essas dependências antes de prometer precisão das consultas e dos avisos.

## Key Findings

### Recommended Stack

Detalhes e fontes: [STACK.md](STACK.md). Preservar a base existente reduz migração desnecessária; separar coleta síncrona do atendimento assíncrono evita travar consultas e notificações.

**Core technologies:**

- **Python 3.11:** manter a linha do ambiente atual e atualizar o patch dentro do suporte; não migrar linguagem.
- **requests + Beautiful Soup:** aproveitar o coletor existente e interpretar contêineres de ponto/calendário, com fixtures reais.
- **SQLite via sqlite3:** persistir catálogo e tabelas detalhadas com transações curtas e foreign keys habilitadas por conexão.
- **python-telegram-bot 22.8 + extra job-queue:** candidato verificado na pesquisa para handlers assíncronos, botões e execução de alertas; deixar o extra resolver APScheduler compatível.
- **datetime + zoneinfo + tzdata:** construir datas conscientes de fuso e assegurar base IANA no Windows; usar `America/Sao_Paulo` para BRT.
- **unittest, mocks, relógio injetável e banco temporário:** testar o contrato da origem e os limites temporais sem depender de envios Telegram ou rede ao executar a suíte.

As versões de requests 2.34.2, Beautiful Soup 4.15.0 e tzdata 2026.6 são candidatas registradas em `STACK.md`; ainda é necessário validar resolução conjunta e compatibilidade antes de congelar dependências. Não houve instalação ou teste integrado das versões durante a pesquisa.

### Expected Features

Detalhes e distinção entre escopo confirmado e sugestões: [FEATURES.md](FEATURES.md).

**Must have — escopo confirmado:**

- Extrair endereços e horários nas páginas já referenciadas pelo catálogo, preservando ponto e calendário.
- Manter as duas tabelas relacionadas com `numero`, `nome`, cinco colunas de horários e cinco de pontos; os horários 1 e 2 devem estar preenchidos.
- `/start` → escolher linha → escolher endereço → próximos três horários, com calendário automático e horário de Brasília.
- Oferecer notificar, ver todos os horários e voltar à escolha do endereço.
- Avisar que os horários de hoje terminaram e oferecer amanhã separadamente.
- Selecionar viagem e antecedência em minutos; avisar a cada cinco minutos com a contagem restante.
- Enviar a mensagem final no horário da saída e encerrar o acompanhamento daquela viagem.

**Should have — recomendações a validar no escopo:**

- Mostrar somente uma ou duas saídas quando não houver três, sem completar com amanhã.
- Diferenciar calendário ausente, falha de coleta e fim efetivo das saídas.
- Isolar estado por chat/usuário e impedir agendamentos idênticos por clique repetido.
- Persistir e recuperar alertas futuros após reinício; pular contagens já vencidas segundo política aprovada.
- Permitir cancelar alerta ativo e informar a atualidade dos dados.

**Defer — fora do escopo ou evolução opcional:**

- GPS e previsão em tempo real, consulta inicial por endereço agregando todas as linhas e alertas diários recorrentes não fazem parte do escopo confirmado.
- Favoritos, múltiplas cidades/fontes e Mini App não são necessários para validar o fluxo inicial.
- Busca/paginação pode ser um detalhe de interface para o catálogo de 379 linhas; não apresentar centenas de botões de uma só vez sem avaliar a navegação.

### Architecture Approach

Detalhes: [ARCHITECTURE.md](ARCHITECTURE.md). Coleta publica um conjunto validado em transação; o bot consulta os dados locais. Falhas de origem preservam o último conjunto válido e produzem diagnóstico distinto de ausência de ônibus. A consulta opera sobre a coleção do ponto e a data de serviço; o alerta guarda um instante de viagem que não muda ao navegar para outro ponto.

**Major components:**

1. **Coletor e parser:** reconstruir URLs HTTPS válidas, validar domínio e percorrer ponto/calendário/listas sem capturar anúncios.
2. **Validador e repositórios SQLite:** conferir obrigatoriedade, identidade e relacionamento; atualizar endereços e horários atomicamente.
3. **Relógio/calendário e consultas:** resolver a data BRT, exceções por data e horários futuros de hoje ou de amanhã.
4. **Handlers Telegram:** controlar seleção de linha/ponto/ação por usuário, sem scraping bloqueante no event loop.
5. **Serviço de alertas e entrega:** derivar instantes absolutos da saída e antecedência, executar mensagens e encerrar na saída; persistência operacional adicional depende de aceite.

**Contrato de dados ainda não aprovado:** `enderecos` pode ter uma chave estável referenciada por `horarios`, que também precisa distinguir calendário e eventual sentido/variante. `numero` sozinho não distingue calendários. A proposta mais compatível com a amostra é um registro por conjunto/calendário e coleções independentes em `horario_ponto1..5`. Não trocar silenciosamente a estrutura pedida por tabelas normalizadas, nem gerar uma linha por índice das listas. Uma representação por viagem exigiria evidência externa de correspondência que não apareceu na amostra.

### Critical Pitfalls

Detalhes: [PITFALLS.md](PITFALLS.md), atualizados pela evidência real de `ARCHITECTURE.md`.

1. **Misturar pontos, calendários ou anúncios:** percorrer os contêineres em ordem e aceitar apenas horários válidos; capturar fixtures com calendários ausentes e `li.adInList`.
2. **Inventar associação entre viagens:** não usar `zip` nas listas dos pontos; o caso 26/27 deve preservar todos os dados sem produzir pareamentos falsos.
3. **Aceitar campos vazios ou FK inativa:** `NOT NULL` não rejeita string ou coleção vazia; validar conteúdo e ativar `PRAGMA foreign_keys=ON` em cada conexão antes da transação.
4. **Escolher data/calendário incorretos:** usar datetime com fuso e resolver amanhã novamente; ausência de calendário publicado não autoriza reutilizar dias úteis.
5. **Perder, duplicar ou atrasar alertas:** separar intenção durável de JobQueue, ancorar eventos na saída, tratar 429 e definir recuperação de eventos vencidos. Envio Telegram e commit local não são transação única; não prometer entrega exatamente uma vez.

## Implications for Roadmap

Estrutura sugerida de seis fases, sujeita ao escopo e ao modo de estrutura que o usuário aprovar. A numeração abaixo não é um roadmap confirmado.

### Phase 1: Contrato da origem e coleta detalhada

**Rationale:** A estrutura real determina como preservar horários antes de projetar o banco.
**Delivers:** Fixtures representativas, parser de pontos/calendários e relatório de dados válidos e incompatíveis.
**Addresses:** Endereços e horários das páginas por linha; descarte de publicidade; calendários publicados.
**Avoids:** Achatar todos os `li`, tratar dados ausentes como ausência de serviço ou presumir que todas as páginas têm dois pontos.

### Phase 2: Persistência relacionada e atualização íntegra

**Rationale:** Consultas precisam de um contrato de armazenamento aprovado que preserve listas independentes.
**Delivers:** Duas tabelas solicitadas, identidade/FK/calendário, migração e atualização atômica sem apagar o conjunto válido em falha.
**Addresses:** Cinco pontos possíveis e obrigatoriedade dos horários 1 e 2.
**Avoids:** Pareamento por índice, perda de horários extras, campos obrigatórios vazios e referências órfãs.

### Phase 3: Consulta temporal e calendário

**Rationale:** A regra de próximos horários deve ser verificável sem depender do chat.
**Delivers:** Consulta por linha/ponto/data, seleção automática de calendário, até três saídas futuras, todos os horários e amanhã.
**Addresses:** BRT, calendário semanal e exceções de feriados conforme política aprovada.
**Avoids:** Mistura de hoje e amanhã, fuso do servidor e fallback indevido para calendários ausentes.

### Phase 4: Fluxo de consulta no Telegram

**Rationale:** O serviço de consulta pronto permite entregar a navegação completa com poucas regras nos handlers.
**Delivers:** `/start`, seleção de linha e endereço, próximos horários, ver horários e voltar; mensagens de término/indisponibilidade.
**Uses:** PTB, estado por usuário/chat e consultas SQLite locais.
**Avoids:** Estado compartilhado entre passageiros e requests síncrono dentro de handlers.

### Phase 5: Alertas da viagem selecionada

**Rationale:** Alertas dependem da identidade do ponto, da saída e da data calculadas pelas fases anteriores.
**Delivers:** Seleção da viagem/antecedência, sequência de cinco em cinco minutos e mensagem final, com política de duplicidade e reinício se aprovada.
**Addresses:** Exemplo confirmado 12h/10 minutos → 11h50, 11h55 e 12h.
**Avoids:** Agendamento relativo ao clique, contagens negativas e perda silenciosa de jobs.

### Phase 6: Verificação operacional e uso completo

**Rationale:** Dados, navegação e alertas precisam funcionar juntos sob falhas e reinícios.
**Delivers:** Verificação integrada com relógio controlado, falha de coleta/envio, isolamento de usuários e documentação de execução/configuração.
**Addresses:** Experiência completa de consulta e notificação; validação da política operacional aprovada.
**Avoids:** Declarar pronto com apenas o caminho feliz ou prometer alertas garantidos com processo desligado.

### Phase Ordering Rationale

- A prova do HTML antecede schema porque as listas desiguais invalidam uma correspondência automática por viagem.
- O banco precede consulta; o motor temporal precede handlers; os alertas usam todos esses contratos.
- É possível reestruturar fases como fatias verticais após a escolha do modo do projeto, preservando essas dependências.
- Testes pertencem às fases que introduzem as regras; a fase operacional complementa a integração, sem adiar toda validação para o fim.

### Research Flags

**Precisam de pesquisa/validação adicional no planejamento:**

- **Fases 1–2:** ampliar amostra de páginas, confirmar linhas com mais pontos/variantes e aprovar coleções por coluna versus outra representação.
- **Fase 3:** fonte de feriados de Fortaleza/CE e exceções efetivas da operação; um calendário civil não comprova a tabela aplicada pelo operador.
- **Fase 5:** antecedência arbitrária, ativação tardia, recuperação após reinício e limite de alertas simultâneos.

**Padrões bem documentados, com implementação testada:**

- **Fase 4:** handlers, teclados e callbacks PTB; ajustar busca/paginação ao catálogo real.
- **Fase 6:** testes com mocks, banco temporário e relógio controlado; reabrir pesquisa se a hospedagem escolhida mudar as condições operacionais.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Documentação oficial e versões verificadas pelos pesquisadores; resolução conjunta ainda não testada. |
| Features | MEDIUM | Fluxo central confirmado pelo usuário; políticas de borda e extensões operacionais pendentes. |
| Architecture | MEDIUM | Três páginas reais e mecanismos oficiais; amostra limitada e schema ainda sujeito a decisão. |
| Pitfalls | MEDIUM | Riscos concretos sustentados por HTML e documentação; sem benchmark nem operação real de bot. |

**Overall confidence:** MEDIUM. As fontes primárias sustentam os mecanismos técnicos; escolhas de produto e a cobertura completa da origem ainda precisam de validação.

### Gaps to Address

- **Unidade do registro de horários:** aprovar coleções independentes por ponto/calendário ou outro modelo que preserve dados sem associação inventada.
- **Dois horários obrigatórios:** definir rejeição/quarentena e mensagem para páginas ou calendários que não satisfaçam a regra; não inserir placeholders.
- **Calendários ausentes:** decidir como explicar ao usuário a ausência de sábado/domingo sem presumir operação.
- **Feriados:** confirmar abrangência Fortaleza/CE, fonte atualizável e exceções operacionais.
- **Bordas temporais:** decidir inclusão de saída exatamente agora e horários de serviço que atravessem meia-noite, se aparecerem na origem.
- **Alertas:** definir minutos aceitos, ativação após início da antecedência, cancelamento e recuperação de eventos futuros/vencidos.
- **Armazenamento operacional:** aprovar tabela adicional de alertas, que não substitui as duas tabelas solicitadas.
- **Operação:** escolher hospedagem e disponibilidade; alertas exigem processo em funcionamento e rede, com tratamento explícito de falhas.
- **Cobertura da coleta:** ampliar fixtures além das três páginas e definir política de atualização; a pesquisa não alterou dados da aplicação.

## Sources

### Primary — documentação oficial e dos mantenedores

- [PTB no PyPI](https://pypi.org/project/python-telegram-bot/) — versão e extras; detalhes em `STACK.md`.
- [PTB ConversationHandler](https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html) — estado de conversa e processamento de updates.
- [PTB JobQueue](https://docs.python-telegram-bot.org/en/stable/telegram.ext.jobqueue.html) e [BasePersistence](https://docs.python-telegram-bot.org/en/stable/telegram.ext.basepersistence.html) — agendamento e separação de persistência.
- [Telegram Bot API](https://core.telegram.org/bots/api), [Features](https://core.telegram.org/bots/features) e [FAQ](https://core.telegram.org/bots/faq) — interações, callbacks e limites de entrega.
- [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html) — fiscalização e chaves referenciadas.
- [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html) e [asyncio.to_thread](https://docs.python.org/3.11/library/asyncio-task.html#asyncio.to_thread) — fuso e I/O bloqueante.
- [APScheduler 3.x User guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) — execuções perdidas e coalescência.
- [Beautiful Soup docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) — navegação estrutural do HTML.
- [GTFS Schedule Reference](https://gtfs.org/documentation/schedule/reference/) — referência conceitual para calendários e exceções; não comprova a estrutura Tonoponto nem obriga adoção de GTFS.

### Primary — origem do scraping observada

- [Catálogo Fortaleza/ETUFOR](https://tonoponto.com/itinerario-horarios-de-onibus/ce-fortaleza-etufor/) — 379 links na inspeção de 2026-11-13.
- [Linha 004](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-004-messejana-papicu-cambeba-tj/) — dois pontos com 26/27 horários úteis.
- [Linha 011](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-011-circular-i/) e [linha 012](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-012-circular-ii/) — calendários por ponto e publicidade nas listas.

O Tonoponto é a fonte observada pelo projeto, não evidência de cumprimento real de cada viagem. A inspeção Python autorizada funcionou embora a ferramenta web recebesse 403. A correção de `SOURCE_URL` já foi conferida e o placeholder anterior não é um bloqueio atual. As quatro pesquisas detalhadas contêm fontes e limitações específicas; esta síntese não fez nova coleta.

---
*Research completed: 2026-11-13*
*Ready for roadmap: após aprovação dos requisitos e resolução dos gates de modelagem e comportamento.*
