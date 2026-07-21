# Casos de uso do onboarding

## Profissional individual

1. usuário conclui cadastro e autenticação;
2. escolhe **Trabalho sozinho**;
3. informa nome do consultório, contato e timezone;
4. o sistema cria `Organization(type=individual)`;
5. cria membership `owner`, ativa e padrão;
6. cria configurações e perfil profissional;
7. persiste o progresso por etapa;
8. após revisão válida, marca o onboarding como concluído;
9. redireciona para o dashboard.

O documento é opcional. Não exigir CNPJ de profissional autônomo.

## Clínica ou equipe

1. usuário escolhe **Clínica ou equipe**;
2. o sistema cria `Organization(type=clinic)`;
3. o responsável torna-se owner;
4. conclui dados institucionais e configurações;
5. acessa a gestão de equipe;
6. convida profissionais e colaboradores com papéis específicos.

## Crescimento de individual para clínica

Uma organização individual pode convidar novos membros e posteriormente alterar o tipo para clínica. Pacientes, prontuários, agenda, documentos e financeiro permanecem no mesmo tenant e não são migrados novamente.

## Membro convidado

### Admin, recepção, financeiro ou viewer

- autentica ou cria conta;
- abre `/convites/aceitar/{token}`;
- o backend confirma token, validade, status e e-mail;
- cria ou ativa a membership;
- não permite alteração de dados globais sem capacidade.

### Therapist

Além do aceite:

- preenche perfil profissional específico da organização;
- informa conselho, especialidades e modalidades;
- não recebe acesso automático aos registros confidenciais de outros profissionais.

## Persistência

O frontend não é a fonte do progresso. Cada avanço envia `step` ao backend e pode atualizar:

- `organization`;
- `professional_profile`;
- `settings`.

A conclusão exige validação no backend e grava:

- `onboarding_status=completed`;
- `onboarding_completed_at`;
- evento de auditoria.

## Redirecionamentos

```text
não autenticado -> login
sem organização -> onboarding etapa 1
organização pendente -> onboarding salvo
organização concluída -> dashboard
convite pendente -> aceite -> onboarding do papel
```

Evitar ciclos entre login, onboarding, seleção de organização e dashboard.

## Telemedicina

O onboarding mantém telemedicina indisponível enquanto não existir provedor de vídeo real. A interface não deve sugerir que o recurso funciona apenas por existir uma sala lógica no banco.
