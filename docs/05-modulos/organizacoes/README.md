# Módulo de organizações

## Finalidade

Permitir que o Elo Terapêutico seja usado tanto por um profissional individual quanto por uma clínica com equipe, usando o mesmo modelo de isolamento de dados.

## Funcionalidades

- criação de consultório individual, clínica ou empresa;
- membership por usuário e organização;
- papéis e capacidades centralizadas;
- convite seguro por e-mail;
- organização ativa por contexto validado;
- perfil profissional específico por vínculo;
- configurações institucionais e de atendimento;
- onboarding persistido em seis etapas;
- seletor de organização no dashboard;
- auditoria e comandos de integridade;
- backfill idempotente de dados legados.

## Fluxo individual

```text
cadastro
  -> organização individual
    -> membership owner
      -> perfil profissional
        -> onboarding
          -> dashboard
```

O documento é opcional. O profissional pode convidar equipe posteriormente sem migrar pacientes ou prontuários.

## Fluxo clínica

```text
cadastro do responsável
  -> organização clínica
    -> owner
      -> configurações
        -> convites
          -> memberships por papel
```

## Papéis

- owner;
- admin;
- therapist;
- receptionist;
- finance;
- viewer.

## Telas

- `/onboarding`;
- `/dashboard/configuracoes/organizacao`;
- `/dashboard/configuracoes/equipe`;
- `/dashboard/configuracoes/perfil-profissional`;
- `/dashboard/configuracoes/atendimento`;
- `/convites/aceitar/{token}`.

## Segurança

- tokens de convite persistidos apenas como hash;
- autorização no backend;
- recursos tenant-owned filtrados por organização;
- relações cruzadas rejeitadas;
- cache invalidado ao trocar de tenant;
- organização suspensa ou arquivada sem escrita operacional;
- logs sem conteúdo clínico ou credenciais.

## Limitação temporária

O Billing continua resolvendo a assinatura pelo owner da organização. A implementação não cria cobrança por membro nem duplica assinaturas existentes.

Telemedicina permanece indicada como indisponível enquanto não houver provedor real de vídeo configurado.
