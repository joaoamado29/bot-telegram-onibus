# API Coverage — Telegram Bot API na fase 1

Matriz do adaptador de consulta planejado; decisões de exclusão respeitam o escopo aprovado. Nenhum método foi implementado nesta geração.

| capability | decision | reason |
|------------|----------|--------|
| getMe / validação do bot | INTEGRATE | Bootstrap PTB valida a identidade do token sem expor valor |
| getUpdates / polling | INTEGRATE | Receber /start, inline_query e callback_query |
| sendMessage | INTEGRATE | Instrução inicial e botão de busca inline |
| answerInlineQuery | INTEGRATE | Autocomplete paginado de linhas |
| InlineQueryResultArticle e InputTextMessageContent | INTEGRATE | Endereços diretamente no resultado selecionado |
| InlineKeyboardMarkup / switch_inline_query_current_chat | INTEGRATE | Abrir autocomplete e escolher ponto |
| answerCallbackQuery | INTEGRATE | Encerrar indicador de interação e informar erro de seleção |
| editMessageText com inline_message_id | INTEGRATE | Mostrar próximas saídas na mensagem inline |
| chosen_inline_result / feedback | OPT-OUT | Não é necessário para seleção autocontida e não oferece chat_id garantido |
| setWebhook / webhook server | OPT-OUT | Processo local de desenvolvimento usa polling; sem provedor de produção aprovado |
| sendMessage para notificações proativas | OPT-OUT | Alertas pertencem às fases 4 e5 |
| Chat administration / moderation / member management | OPT-OUT | Bot consulta dados públicos; administração de grupos fora do escopo |
| Media / file upload / download / stickers | OPT-OUT | Interface aprovada é textual com botões |
| Payments / invoices / Stars / paid media | OPT-OUT | Nenhum pagamento no produto aprovado |
| Games / Web Apps / Mini Apps / business accounts | OPT-OUT | Fora da conversa e interação aprovadas |
| Location sharing / live location | OPT-OUT | GPS e rastreamento fora do escopo |
| Passport / identity documents / login widgets | OPT-OUT | Não há autenticação de passageiro adicional |
| Message deletion / forwarding / copying | OPT-OUT | Não necessários ao caminho de consulta aprovado |
| Message reactions / pinning / polls / checklists / stories | OPT-OUT | Não necessários ao caminho de consulta aprovado |

## Data source

Tonoponto é origem HTML, não API JSON/SDK. Integrar GET HTTPS do catálogo e páginas referenciadas; sem automação de formulários, publicação ou serviços não solicitados.
