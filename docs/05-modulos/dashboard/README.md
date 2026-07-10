# Módulo de dashboard

**Status: parcialmente implementado.**

## Finalidade

Apresentar visão operacional resumida após o login, agregando dados de agenda, pacientes, financeiro, assinatura e ações rápidas.

## Implementação

O frontend possui `features/dashboard/dashboard-home.tsx` e rota `/dashboard`. Os dados não formam uma entidade própria: são obtidos de endpoints dos módulos.

O dashboard do paciente é exposto por `/api/v1/patients/{id}/dashboard/` e reúne:

- dados cadastrais permitidos;
- próxima sessão;
- última evolução para usuários autorizados;
- documentos recentes permitidos;
- presença, faltas e metas;
- indicação de IA indisponível quando não configurada.

Métricas gerais de pacientes estão em `/api/v1/patients/dashboard-metrics/`.

## Permissões

A interface deve respeitar role e recursos do plano, mas a API continua responsável por filtrar dados. Secretárias não recebem conteúdo clínico no dashboard do paciente.

## Segurança

- não exibir conteúdo clínico em widgets administrativos sem necessidade;
- evitar cache compartilhado entre usuários;
- mascarar identificadores nos resumos;
- não usar mocks em produção para representar métricas reais.

## Testes e limitações

Há testes de dashboard em pacientes e financeiro. Não foi localizada uma suíte frontend abrangente e dedicada ao dashboard. Métricas podem ficar indisponíveis quando endpoints dependentes falham; a interface deve tratar loading, vazio e erro separadamente.

[Voltar aos módulos](../README.md)
