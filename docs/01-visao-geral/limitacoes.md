# Limitações e riscos conhecidos

## Arquitetura e acesso

1. **Multi-tenancy por clínica não está implementado explicitamente.** O isolamento predominante é por usuário/terapeuta.
2. **JWTs ficam em cookies acessíveis ao JavaScript.** Isso amplia o impacto de uma vulnerabilidade XSS; `HttpOnly` não pode ser definido por código executado no navegador.
3. **O middleware Next.js não substitui autorização backend.** Ele melhora navegação, mas cookies de role podem ser manipulados pelo cliente.
4. **Há rota de billing em dois prefixos:** `/api/v1/billing/` e `/api/billing/`, o que aumenta superfície e risco de documentação divergente.

## Dados e arquivos

5. **Storage local pode permanecer ativo em produção** quando `PRIVATE_MEDIA_STORAGE_REQUIRED` não for habilitado.
6. **Uploads clínicos não passam por antivírus.** Há validação de tamanho, extensão, MIME e assinatura, mas não análise de malware.
7. **Retenção e exclusão não possuem política automática global comprovada.** Arquivamento e anonimização pontuais não equivalem a uma política institucional.
8. **Rotação de chave criptográfica exige procedimento operacional.** O campo suporta versões, mas a migração completa dos dados deve ser planejada e testada.

## Integrações e operação

9. **Webhook Asaas sem token é aceito no desenvolvimento**, com warning; produção rejeita inicialização sem segredo forte.
10. **E-mail síncrono na redefinição de senha** pode afetar latência e disponibilidade.
11. **Fila de exportação depende de processo worker separado.** Sem o worker, jobs permanecem pendentes.
12. **Backup, restauração, monitoramento e alertas dependem da infraestrutura.** Não são garantidos apenas pelo código.
13. **Não há comprovação de deploy ativo no Azure** no repositório.

## Qualidade

14. A suíte backend é extensa, mas números de cobertura devem ser medidos por commit.
15. A suíte frontend automatizada é concentrada no calendário da agenda e não cobre toda a interface.
16. O `mypy` contém vários módulos com `ignore_errors`, reduzindo a garantia de tipagem integral.

## Produto

17. Recursos de IA não devem produzir diagnóstico, prescrição ou decisão clínica autônoma.
18. A conformidade LGPD depende de processos humanos, contratos, base legal, retenção, atendimento ao titular e segurança operacional.

[Voltar](README.md)
