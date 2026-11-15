# Bot Telegram Ônibus (ETUFOR / Tonoponto)

Bot de Telegram para consultar horários de ônibus a partir dos dados do Tonoponto, com busca inline inteligente, seleção de endereço/ponto e cálculo em tempo real das próximas saídas no horário de Brasília (`America/Sao_Paulo`).

---

## 🛠 Requisitos

- Python 3.10+
- Virtualenv configurado (`.venv`)

---

## 📦 Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## ⚙️ Configuração do Telegram

1. **Obtenha um token no Telegram:**
   * Crie seu bot com o [@BotFather](https://t.me/BotFather) e guarde o token de acesso.
2. **Ative a busca inline:**
   * No `@BotFather`, envie o comando `/setinline`.
   * Escolha o bot criado e defina um texto de placeholder (exemplo: `Buscar linha de ônibus...`).
3. **Configure o token no ambiente local:**
   * Crie um arquivo `.env` na raiz do projeto (**nunca versione este arquivo nem compartilhe seu token**):
     ```env
     TELEGRAM_BOT_TOKEN=seu_token_aqui
     ```
   * *O arquivo `.env` já está incluído no `.gitignore` e não será rastreado pelo Git.*

---

## 🚀 Como Executar

### 1. Iniciar o Bot do Telegram
Para iniciar o bot em modo polling contínuo com agendador de tarefas ativo:

```powershell
.\.venv\Scripts\python.exe bot.py
```

### 2. Atualizar Manualmente uma Linha Específica (CLI)
Para coletar ou atualizar manualmente os pontos e horários de uma linha do catálogo:

```powershell
.\.venv\Scripts\python.exe bot.py --coletar-linha 11
```

### 3. Coleta Inicial do Catálogo de Linhas (Legado)
Para atualizar apenas a lista geral de linhas disponíveis:

```powershell
.\.venv\Scripts\python.exe scraping.py
```

---

## 🔄 Rotina de Coletas e Atualizações Automáticas

- **Coleta Inicial Automática:** Se o bot for iniciado com a tabela de horários vazia, ele agenda e executa a coleta dos horários em segundo plano sem travar o atendimento.
- **Ciclo Semanal:** As linhas têm seus horários atualizados todo **domingo às 01:00 (horário de Brasília)**. Para que essa atualização ocorra, o processo do bot deve permanecer em execução contínua.
- **Recuperação de Falhas (Retry):**
  - Se uma linha apresentar falha de rede ou dados incompletos (menos de 2 pontos ou coleções obrigatórias ausentes), a atualização daquela linha é revertida e seus dados anteriores válidos são rigorosamente preservados.
  - O bot programa automaticamente até **3 tentativas de recuperação** para a linha com falha (após 5, 15 e 60 minutos), sem interromper a consulta das outras linhas.

---

## 🗄 Estrutura do Banco de Dados (SQLite)

O banco de dados relacional é mantido em `onibus.sqlite3` com integridade referencial ativa (`PRAGMA foreign_keys = ON`):

1. **`linhas`**: Catálogo base de linhas cadastradas.
   - `numero` (INTEGER PRIMARY KEY)
   - `nome` (TEXT)
   - `link` (TEXT)
   - `created_at` (TEXT)
2. **`pontos`**: Endereços dos pontos de parada da linha (de 2 a 5 pontos) e controle de versão.
   - `numero` (INTEGER PRIMARY KEY REFERENCES `linhas(numero)`)
   - `nome` (TEXT)
   - `ponto1` a `ponto5` (TEXT)
   - `revisao` (INTEGER)
   - `updated_at` (TEXT)
3. **`horarios`**: Matriz de horários estruturados em formato JSON array por calendário.
   - `numero` (INTEGER REFERENCES `pontos(numero)`)
   - `nome` (TEXT)
   - `calendario` (TEXT: `uteis`, `sabados`, `domingos_feriados`)
   - `horario_ponto1` a `horario_ponto5` (TEXT com validação CHECK `json_valid` e `json_array_length > 0` para as duas primeiras colunas)
   - PRIMARY KEY (`numero`, `calendario`)

---

## Calendário de operação e feriados

As consultas usam `America/Sao_Paulo`. Em qualquer feriado cadastrado, inclusive quando cai em sábado ou domingo, o bot seleciona o calendário `domingos_feriados` e informa o nome e a data do feriado. O catálogo é local e a consulta do passageiro não acessa a internet. Pontos facultativos, como Carnaval, não são tratados como feriados.

O catálogo em `onibus/holidays.py` registra as normas que definem cada regra:

- Feriados nacionais recorrentes: [Lei 662/1949 e alterações](https://legislacao.presidencia.gov.br/atos/?ano=1949&ato=3deoXUE5EMBRVT165&numero=662&tipo=LEI), [Lei 6.802/1980](https://www.planalto.gov.br/ccivil_03/leis/l6802.htm) (12 de outubro) e [Lei 14.759/2023](https://legislacao.presidencia.gov.br/atos/?ano=2023&ato=264k3ZE90MZpWTeac&numero=14759&tipo=LEI) (20 de novembro).
- Data Magna do Ceará: [Emenda Constitucional estadual 73/2011](https://www2.al.ce.gov.br/legislativo/tramit2011/ec73.htm), em 25 de março.
- Feriados religiosos de Fortaleza: [Lei municipal 8.796/2003](https://legislacao.pgm.fortaleza.ce.gov.br/images/6/6d/Lei8796-03.pdf), com São José, Nossa Senhora da Assunção, Sexta-feira da Paixão e Corpus Christi. As duas datas móveis são calculadas localmente a partir da Páscoa.
- Exceção de 2026: [Lei municipal 11.649/2026](https://sapl.fortaleza.ce.leg.br/norma/14390), que declarou feriado em 13 de abril somente naquele ano pelo tricentenário da cidade.

Revise o catálogo anualmente, antes do início de cada ano civil, consultando a legislação federal, estadual e o [sistema de normas da Câmara Municipal de Fortaleza](https://sapl.fortaleza.ce.leg.br/norma/pesquisar). Registre novas regras recorrentes ou exceções apenas quando houver lei que as declare; não transforme ponto facultativo nem feriado de ano específico em regra recorrente.

O responsável pela manutenção do bot deve fazer essa revisão e versionar as mudanças antes de disponibilizar o novo calendário. A revisão de 15/11/2026 conferiu as normas municipais e o [calendário oficial do TRE-CE](https://www.tre-ce.jus.br/legislacao/compilada/portaria-conjunta/2026/portaria-conjunta-no-3-de-9-de-abril-de-2026), usando somente os feriados civis/religiosos aplicáveis ao município; recessos e feriados específicos do Judiciário não integram a operação do bot. A exceção municipal encontrada foi a de 13/04/2026, mantida separada das regras recorrentes.

---

## 🧪 Execução dos Testes Automatizados

Para rodar toda a suíte de testes unitários e de integração:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

---

## 🗺 Roadmap de Fases Seguintes

- **Fase 1 (Atual):** Primeiras consultas no Telegram, busca inline, paginação e atualização semanal.
- **Fase 2:** Calendário completo com feriados nacionais, estaduais (Ceará) e municipais (Fortaleza).
- **Fase 3:** Navegação de todos os horários e consulta de saídas do dia seguinte.
- **Fase 4:** Lembretes e alertas com antecedência configurável e contagem regressiva antes do embarque.
- **Fase 5:** Monitoramento, logs estruturados e resiliência em produção.
