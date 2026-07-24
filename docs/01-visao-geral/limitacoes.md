# Limitações e riscos conhecidos

Este documento registra somente limitações ainda vigentes. Relatórios históricos podem descrever estados anteriores e não devem substituir o código, as migrations, os testes e as matrizes canônicas.

## Arquitetura e acesso

1. **O tenant explícito existe, mas o isolamento transversal ainda precisa de comprovação contínua.** `apps.organizations` implementa organizações, memberships, contexto ativo e autenticação tenant-aware; o risco residual está em ownership legado, tasks, caches, relatórios, exports, storage e integrações que ainda devem ser auditados por módulo.
2. **Access e refresh tokens são protegidos por cookies HttpOnly no BFF**, mas XSS ainda pode executar ações em nome do usuário. CSP, sanitização, dependências atualizadas, CSRF e revisão de frontend permanecem obrigatórios.
3. **O proxy do Next.js não substitui autorização backend.** A navegação pode usar sinais de sessão, mas role, assinatura, tenant e permissão de objeto devem ser confirmados pelo Django.
4. **A rota legada de Billing pode ser habilitada em `/api/billing/` além de `/api/v1/billing/`.** A feature flag deve permanecer desabilitada em produção quando não houver consumidor legado comprovado.
5. **Os fluxos E2E atuais cobrem autenticação, gateway indisponível e telemedicina**, mas ainda não abrangem todos os módulos críticos, papéis, fluxos mobile e operações multi-tenant.

## Dados e arquivos

6. **Storage local não é adequado para produção clínica.** O settings de produção pode exigir Azure Blob privado, porém a infraestrutura, as permissões e a restauração precisam ser validadas no ambiente implantado.
7. **Uploads clínicos possuem validação estrutural, quarentena e scanner configurável em modo fail-closed.** O arquivo não é liberado quando o scanner está indisponível; ainda falta comprovar um provider antimalware externo ativo em staging e produção.
8. **Existem limpezas específicas para quarentena, exports, tokens e notificações**, mas não há uma política institucional global de retenção e descarte comprovada para todos os domínios.
9. **Rotação de chave criptográfica exige procedimento operacional.** O campo suporta versões, porém a migração completa dos dados e o rollback precisam ser ensaiados.

## Integrações e operação

10. **Webhook Asaas sem token pode ser aceito apenas em desenvolvimento controlado.** Produção rejeita inicialização sem segredo forte, mas idempotência, replay e reconciliação devem continuar validados em sandbox.
11. **Alguns fluxos de e-mail ainda podem executar envio síncrono**, afetando latência e disponibilidade quando o SMTP estiver degradado.
12. **Filas assíncronas dependem de Redis, quatro workers e Celery Beat.** Sem esses processos, jobs permanecem pendentes ou entram em recuperação.
13. **Backup, restauração, monitoramento e alertas dependem da infraestrutura.** Não são garantidos apenas pelo código ou pelos runbooks.
14. **Não há comprovação de deploy ativo no Azure** no repositório.
15. **Telemedicina possui áudio e vídeo com LiveKit, E2EE, convites e webhooks**, mas continua desativada por padrão e depende de HTTPS/WSS, credenciais, webhook público protegido e smoke test em staging.
16. **IA não possui integração funcional.** Enquanto não houver provider, consentimento, governança, auditoria e revisão humana, promessas comerciais de IA devem permanecer indisponíveis.

## Qualidade

17. No baseline da estabilização de 24/07/2026, a suíte backend cobriu **67,61% das linhas instrumentadas**; o número pertence ao commit e ao ambiente medidos, não constitui garantia permanente.
18. O frontend possui testes estruturais e cobertura alta sobre os arquivos atualmente instrumentados, porém essa instrumentação não representa os 330 arquivos de `frontend/src`.
19. O baseline do ESLint contém **91 warnings reais**: efeitos com atualização síncrona de estado, `any`, variáveis não utilizadas, dependências de hooks e acessibilidade. O CI ainda não usa `--max-warnings=0`.
20. O `mypy` contém exclusões e um override amplo com `ignore_errors`, reduzindo a garantia de tipagem integral.
21. O CI principal usa PostgreSQL 15, mas cenários de carga, failover e alta concorrência ainda exigem ambiente dedicado.

## Produto e conformidade

22. Recursos de IA não devem produzir diagnóstico, prescrição ou decisão clínica autônoma.
23. A conformidade LGPD depende de processos humanos, contratos, base legal, retenção, atendimento ao titular e segurança operacional.
24. Portal autenticado do paciente e agendamento público ponta a ponta ainda não estão concluídos como domínios completos.
25. Integrações externas somente podem ser classificadas como operacionais após validação em sandbox ou staging com credenciais próprias.

[Voltar](README.md)
