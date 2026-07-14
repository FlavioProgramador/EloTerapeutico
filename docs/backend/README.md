# Documentação do backend

Este diretório concentra a documentação técnica do backend do Elo Terapêutico. A fonte da verdade continua sendo o código, as migrations, os testes e as configurações do repositório.

## Conteúdo

| Documento | Conteúdo |
| --- | --- |
| [architecture.md](architecture.md) | Arquitetura, camadas, dependências e fluxo de requisição |
| [apps.md](apps.md) | Inventário dos apps e responsabilidades |
| [api.md](api.md) | Convenções HTTP, autenticação, paginação, erros e OpenAPI |
| [authentication-and-permissions.md](authentication-and-permissions.md) | JWT, bloqueio, recuperação de senha, assinatura e autorização |
| [multi-tenancy.md](multi-tenancy.md) | Isolamento atual por profissional e limitações de tenant explícito |
| [clinical-records.md](clinical-records.md) | Prontuário, confidencialidade, autoria, auditoria e exportação |
| [billing-and-integrations.md](billing-and-integrations.md) | Billing, Asaas, storage, e-mail e provedores externos |
| [asynchronous-tasks.md](asynchronous-tasks.md) | Workers persistidos, estados, retries e operação |
| [environment-variables.md](environment-variables.md) | Variáveis de ambiente e configuração segura |
| [testing-and-troubleshooting.md](testing-and-troubleshooting.md) | Testes, qualidade, diagnóstico e problemas comuns |
| [documentation-report.md](documentation-report.md) | Relatório da implementação desta documentação |

## Padrão de documentação no código

As docstrings novas ou alteradas devem seguir Google Style, em português, descrevendo responsabilidade, argumentos, retorno, exceções e efeitos colaterais quando relevantes.

```python
def refresh_gateway_payment(*, user, payment_id: int, gateway=None):
    """Sincroniza uma cobrança do usuário com o gateway configurado.

    Args:
        user: Usuário autenticado que delimita o escopo da consulta.
        payment_id: Identificador interno da cobrança.
        gateway: Cliente opcional usado para integração ou testes.

    Returns:
        Cobrança local atualizada a partir do payload do gateway.

    Raises:
        PaymentRefreshUnavailable: Quando a cobrança não pertence ao usuário
            ou não possui os vínculos necessários para sincronização.
    """
```

Evite docstrings que apenas repitam o nome da função e comentários linha a linha. Comentários devem explicar decisões, concorrência, segurança, idempotência ou limitações não evidentes.

## Regras de manutenção

1. Atualize a documentação no mesmo Pull Request da mudança funcional.
2. Não documente endpoints, estados, providers ou comandos inexistentes.
3. Não inclua credenciais, dados pessoais ou conteúdo clínico real.
4. Preserve contratos públicos de API ao realizar mudanças exclusivamente documentais.
5. Registre riscos e inconsistências no relatório técnico em vez de alterar regras de negócio fora do escopo.
