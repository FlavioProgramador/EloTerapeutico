# Limitações e riscos conhecidos

## Arquitetura e acesso

1. **Multi-tenancy por clínica não está implementado explicitamente.** O isolamento predominante é por usuário/terapeuta.
2. **Access e refresh tokens são protegidos por cookies HttpOnly no BFF**, mas XSS ainda pode executar ações em nome do usuário. CSP, sanitização, dependências atualizadas e CSRF continuam obrigatórios.
3. **O middleware Next.js não substitui autorização backend.** A navegação pode usar sinais de sessão, mas role, assinatura, tenant e permissão de objeto devem ser confirmados pelo Django.
4. **Há rota de billing em dois prefixos:** `/api/v1/billing/` e `/api/billing/`, o que aumenta superfície e risco de documentação divergente.
5. **A validação E2E de autenticação depende dos workflows do PR.** Não considerar a estabilização concluída enquanto os jobs não passarem.

## Dados e arquivos

6. **Storage local não é adequado para produção clínica.** O settings de produção pode exigir Azure Blob, mas a infraestrutura precisa estar configurada e validada.
7. **Uploads clínicos não passam por antivírus.** Há validação de tamanho, extensão, MIME e assinatura, mas não análise de malware.
8. **Retenção e exclusão não possuem política automática global comprovada.** Arquivamento e anonimização pontuais não equivalem a uma política institucional.
9. **Rotação de chave criptográfica exige procedimento operacional.** O campo suporta versões, mas a migração completa dos dados deve ser planejada e testada.

## Integrações e operação

10. **Webhook Asaas sem token é aceito no desenvolvimento**, com warning; produção rejeita inicialização sem segredo forte.
11. **E-mail síncrono na redefinição de senha** pode afetar latência e disponibilidade.
12. **Filas assíncronas dependem de Redis, workers e Celery Beat.** Sem esses processos, jobs permanecem pendentes.
13. **Backup, restauração, monitoramento e alertas dependem da infraestrutura.** Não são garantidos apenas pelo código.
14. **Não há comprovação de deploy ativo no Azure** no repositório.
15. **Telemedicina não possui mídia em tempo real.** A implementação atual cobre sala lógica, tokens e acesso, não áudio/vídeo.
16. **IA não possui integração funcional.** Existe somente preparação comercial e placeholder de interface.

## Qualidade

17. A suíte backend é extensa, mas números de cobertura devem ser medidos por commit.
18. A cobertura frontend continua menor que a backend, apesar dos novos testes unitários e E2E de autenticação.
19. O `mypy` contém módulos historicamente configurados com `ignore_errors`, reduzindo a garantia de tipagem integral. Esta revisão torna o gate obrigatório sem ampliar os ignores.
20. O CI principal passa a usar PostgreSQL 15, mas cenários de carga, failover e alta concorrência ainda exigem ambiente dedicado.

## Produto e conformidade

21. Recursos de IA não devem produzir diagnóstico, prescrição ou decisão clínica autônoma.
22. A conformidade LGPD depende de processos humanos, contratos, base legal, retenção, atendimento ao titular e segurança operacional.
23. Portal do paciente, consentimentos completos e agendamento público ponta a ponta ainda não estão concluídos.

[Voltar](README.md)
