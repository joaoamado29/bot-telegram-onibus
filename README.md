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
