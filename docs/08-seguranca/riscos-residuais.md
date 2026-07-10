# Riscos residuais

| Risco | Severidade indicativa | Situação | Tratamento recomendado |
| --- | --- | --- | --- |
| JWT acessível ao JavaScript | Alta | Pendente | cookies HttpOnly/BFF + CSP |
| Ausência de tenant explícito | Alta para multi-clínica | Pendente | modelar tenant e memberships |
| Storage local permitido em prod | Alta | Configurável | exigir Azure privado |
| Antivírus ausente | Média/Alta | Pendente | pipeline de quarentena |
| Auditoria fail-open | Média | Aceito no código | alerta e trilha externa |
| Cobertura de auditoria incompleta | Média | Possível | inventário por endpoint |
| Admin/SQL Explorer | Alta | Implementado | restrição, MFA, menor privilégio |
| Webhook sem token em dev | Alta se exposto | Dev only | nunca publicar dev settings |
| Retenção não automatizada | Alta regulatória | Pendente | política + jobs + aprovação |
| Backup/restauração não codificados | Alta | Operacional | serviço gerenciado e exercícios |
| Frontend com testes limitados | Média | Pendente | unit/integration/E2E |
| Muitos ignores de mypy | Baixa/Média | Conhecido | redução incremental |
| Dependência de Asaas | Média | Aceito | retry, reconciliação e alertas |
| IA clínica incompleta | Alta se mal utilizada | Indisponível/planejada | revisão humana e limites claros |

Severidade é uma triagem técnica, não uma avaliação formal. Reavalie com contexto de implantação, volume, exposição e controles compensatórios.

[Voltar](README.md)
