# Checklist de Segurança para Produção

Use este documento antes de cada implantação do Elo Terapêutico em ambiente que processe dados reais.

## Bloqueadores de implantação

- [ ] O workflow `Backend Security` foi concluído sem falhas em Django check, migrations, Ruff e pytest.
- [ ] Vulnerabilidades críticas ou altas encontradas pelo Bandit e pip-audit foram corrigidas ou formalmente aceitas.
- [ ] `DEBUG=False` foi confirmado no processo em execução.
- [ ] `SECRET_KEY`, `JWT_SECRET` e `FIELD_ENCRYPTION_KEY` são exclusivos do ambiente e não utilizam valores de exemplo.
- [ ] `ASAAS_API_KEY` e `ASAAS_WEBHOOK_TOKEN` estão configurados no cofre de segredos.
- [ ] `ASAAS_BASE_URL` aponta para produção somente após homologação completa no sandbox.
- [ ] O banco de dados não está exposto publicamente.
- [ ] O Redis não está exposto publicamente.
- [ ] A aplicação não utiliza `runserver` ou `npm run dev` em produção.
- [ ] O container Azure utilizado para mídia não permite acesso público.
- [ ] Arquivos já existentes foram migrados e validados antes de ativar storage obrigatório.
- [ ] `PRIVATE_MEDIA_STORAGE_REQUIRED=True` está configurado.
- [ ] O isolamento por organização está implementado antes de operar com múltiplas clínicas.

## Variáveis e segredos

- [ ] `ALLOWED_HOSTS` contém somente hosts reais.
- [ ] `CORS_ALLOWED_ORIGINS` contém somente origens HTTPS aprovadas.
- [ ] `CSRF_TRUSTED_ORIGINS` contém somente origens HTTPS aprovadas.
- [ ] `TRUST_PROXY_CLIENT_IP_HEADERS=True` somente quando o backend não pode ser acessado fora do proxy confiável.
- [ ] `DATABASE_URL` exige TLS quando o provedor suporta.
- [ ] `REDIS_URL` utiliza autenticação e TLS quando disponível.
- [ ] `AZURE_STORAGE_CONNECTION_STRING` não aparece em logs, arquivos ou histórico Git.
- [ ] `AZURE_URL_EXPIRATION_SECS` utiliza janela curta, preferencialmente 300 segundos ou menos.
- [ ] Credenciais antigas foram revogadas após qualquer suspeita de exposição.
- [ ] Existe procedimento documentado de rotação da chave de criptografia de campos.

## HTTP, cookies e proxy

- [ ] HTTPS é obrigatório e o redirecionamento funciona no proxy real.
- [ ] HSTS foi testado antes de habilitar preload.
- [ ] `SECURE_PROXY_SSL_HEADER` corresponde ao cabeçalho enviado pelo proxy.
- [ ] Cookies de sessão e CSRF possuem os atributos previstos.
- [ ] O frontend não toma decisões de autorização como única barreira.
- [ ] Respostas com dados clínicos usam `Cache-Control: private, no-store`.
- [ ] Downloads clínicos usam `nosniff` e exigem autorização por objeto.
- [ ] O proxy ou CDN não remove os cabeçalhos de segurança da aplicação.

## Autenticação

- [ ] Login com usuário válido, senha inválida e usuário inexistente foi testado.
- [ ] Bloqueio por tentativas falhas foi testado.
- [ ] Rate limit utiliza cache compartilhado entre instâncias.
- [ ] Refresh tokens rotacionam e entram em blacklist.
- [ ] Tokens anteriores deixam de funcionar após troca ou redefinição de senha.
- [ ] Logout não aceita refresh token de outra conta.
- [ ] Usuários inativos e bloqueados não autenticam.
- [ ] O risco de tokens acessíveis ao JavaScript foi resolvido ou formalmente aceito.
- [ ] A recuperação de senha utiliza fila persistida ou mitigação equivalente contra timing de SMTP.

## Autorização e dados clínicos

- [ ] Todo endpoint sensível exige autenticação.
- [ ] Querysets aplicam escopo do usuário ou tenant.
- [ ] IDs enviados pelo cliente nunca definem automaticamente proprietário, autor ou organização.
- [ ] Secretárias não visualizam conteúdo clínico restrito.
- [ ] Evoluções confidenciais não aparecem em listagens, documentos, relatórios ou exportações indevidas.
- [ ] Regra de edição de 48 horas foi testada.
- [ ] Aditivos preservam o conteúdo original.
- [ ] Visualização, edição, retificação, exportação e download são auditados.
- [ ] Exclusão física de prontuários consolidados não é permitida sem política específica.

## Billing e Asaas

- [ ] O preço utilizado vem do plano no backend.
- [ ] Checkout não retorna payload bruto do gateway.
- [ ] Webhook com segredo inválido retorna 403 e não persiste dados.
- [ ] Mesmo `event_id` não é processado duas vezes.
- [ ] CPF, tokens e dados PIX são mascarados em payloads brutos.
- [ ] Replays e eventos fora de ordem foram testados.
- [ ] Existe reconciliação entre assinaturas locais e o Asaas.
- [ ] Mensagens internas do gateway não são expostas ao usuário final.

## Arquivos e exportações

- [ ] Extensão, MIME declarado e assinatura real dos arquivos são validados.
- [ ] Tamanho e quantidade de anexos são limitados.
- [ ] Nomes físicos não são previsíveis.
- [ ] Downloads exigem autorização no momento da solicitação.
- [ ] URLs assinadas possuem expiração curta.
- [ ] Exportações expiradas são removidas.
- [ ] Jobs travados são recuperados ou marcados como falha.
- [ ] Existe quota por usuário ou organização.
- [ ] Existe estratégia de scanner antimalware para uploads.

## Banco, backup e recuperação

- [ ] O usuário do banco não é superusuário.
- [ ] Backups são criptografados.
- [ ] Retenção de backup está definida.
- [ ] Backups ficam em conta ou local separado do ambiente principal.
- [ ] Um teste de restauração completo foi executado e documentado.
- [ ] RPO e RTO foram definidos.
- [ ] Migrations destrutivas possuem plano de rollback.
- [ ] Constraints de integridade e índices foram revisados.

## Logs, auditoria e monitoramento

- [ ] Logs não contêm senha, JWT, refresh token, cookie, chave de API, CPF completo ou conteúdo clínico.
- [ ] O pipeline de observabilidade aplica redaction.
- [ ] AuditLog não pode ser alterado ou removido pela aplicação comum.
- [ ] Alertas existem para falhas repetidas de login e webhook.
- [ ] Alertas existem para erros de exportação e storage.
- [ ] Request IDs permitem correlacionar erros sem expor detalhes internos.
- [ ] A retenção dos logs está documentada.

## LGPD e operação

- [ ] O inventário de dados está atualizado.
- [ ] Finalidade e base legal estão documentadas para cada categoria de dado.
- [ ] Política de retenção está implementada.
- [ ] Solicitação de correção, exportação, anonimização ou bloqueio possui procedimento.
- [ ] Termos e consentimentos, quando aplicáveis, possuem versão e data.
- [ ] Existe canal de atendimento ao titular.
- [ ] Existe plano de resposta a incidentes.
- [ ] Responsáveis por segurança, privacidade e comunicação estão definidos.

## Aprovação

- Data da revisão:
- Commit implantado:
- Ambiente:
- Responsável técnico:
- Responsável pela aprovação:
- Pendências aceitas:
- Data prevista para correção das pendências:
