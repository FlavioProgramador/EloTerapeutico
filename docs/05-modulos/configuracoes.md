# Configurações

## Situação anterior

A rota `/dashboard/configuracoes` exibia apenas um estado vazio. Os dados de perfil, horários de atendimento e sessões já possuíam APIs isoladas, porém não estavam reunidos em um fluxo funcional. As preferências institucionais e de comunicação não possuíam persistência própria.

A área chamada de comunicação interna correspondia a avisos e notificações in-app. O projeto não possui, neste momento, chat entre profissionais, grupos, anexos de conversa ou criptografia ponta a ponta.

## Implementação

O módulo passou a concentrar:

- perfil profissional;
- dados do consultório;
- regras de agenda;
- horários de atendimento;
- avisos internos;
- preferências de notificações;
- sessões autenticadas;
- alteração de senha;
- acesso à saúde das integrações.

## Propriedade dos dados

O código-base ainda não possui uma entidade `Clinic` nem vínculos de equipe. Por isso:

- perfil pertence ao usuário autenticado;
- `PracticeSettings` pertence à conta autenticada por relação `OneToOne`;
- horários pertencem ao terapeuta autenticado;
- sessões pertencem ao usuário autenticado;
- notificações pertencem ao destinatário autenticado.

O frontend nunca envia o identificador de proprietário. O backend resolve o proprietário por `request.user`.

## Endpoints

| Método | Endpoint | Uso |
| --- | --- | --- |
| GET/PATCH | `/api/v1/auth/me/` | Perfil profissional |
| GET/PATCH | `/api/v1/auth/settings/` | Consultório, agenda e comunicação interna |
| GET/POST | `/api/v1/auth/working-hours/` | Horários de atendimento |
| PATCH/DELETE | `/api/v1/auth/working-hours/{id}/` | Alteração de horário próprio |
| GET | `/api/v1/auth/sessions/` | Sessões ativas |
| POST | `/api/v1/auth/sessions/{public_id}/revoke/` | Revogação de sessão própria |
| POST | `/api/v1/auth/password/change/` | Alteração de senha e revogação das sessões |

## Regras aplicadas à agenda

As configurações deixam de ser apenas visuais:

- `appointment_interval_minutes` altera o passo entre horários sugeridos;
- `minimum_booking_notice_hours` bloqueia novos agendamentos sem antecedência;
- `allow_overbooking` remove apenas o conflito do profissional, preservando conflitos de paciente, sala e bloqueios;
- os horários de atendimento delimitam a disponibilidade;
- duração, valor e modalidade padrão são disponibilizados pelo perfil.

A preferência `consider_holidays` é persistida, mas depende de uma futura fonte de feriados para produzir bloqueios automáticos.

## Comunicação interna

A seção controla o canal de avisos internos:

- habilitação do canal;
- prévia de mensagem;
- marcação ao abrir;
- preparação para menções;
- horário de silêncio;
- política de comunicação.

Essas opções não criam um chat de equipe. A interface informa essa limitação para não prometer uma capacidade inexistente.

## Segurança

- BFF e cookies HttpOnly preservados;
- mutações protegidas por CSRF;
- nenhuma preferência é salva em `localStorage` ou `sessionStorage`;
- sessões expõem apenas `public_id`, agente, datas e indicador da sessão atual;
- refresh token e JTI nunca são retornados;
- atualizações são auditadas;
- objetos de outro usuário não são retornados.

## Frontend

A feature está organizada em:

```text
frontend/src/features/settings/
├── settings-page.tsx
├── settings.service.ts
├── types.ts
└── use-settings.ts
```

Componentes visuais não acessam Axios diretamente. Estado remoto e invalidação são controlados pelo TanStack Query.

## Limitações

- ainda não existe entidade de clínica, equipe ou vínculo multi-tenant;
- logo e avatar continuam usando os uploads já existentes, sem editor dedicado nesta entrega;
- feriados precisam de fonte externa ou cadastro próprio;
- 2FA está fora do escopo da infraestrutura atual;
- direitos LGPD continuam documentados e operacionalizados pelos fluxos já existentes, sem exclusão automática pela tela de configurações.
