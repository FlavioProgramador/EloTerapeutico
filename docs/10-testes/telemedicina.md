# Testes de telemedicina

## Backend

A suíte usa `TELEMEDICINE_PROVIDER=fake` somente dentro do pytest. Nenhuma credencial real ou minuto LiveKit é necessário na CI.

Cobertura principal:

- criação de uma única sala por consulta online;
- isolamento por organização;
- room name opaco;
- convite armazenado somente como hash;
- regeneração e revogação;
- consentimento obrigatório e versionado;
- E2EE key criptografada em repouso;
- emissão de token efêmero;
- ausência de tokens e IDs do provedor nos serializers;
- resposta pública minimizada e `no-store`;
- bloqueio de plano sem entitlement;
- idempotência do webhook;
- presença de participante;
- envio explícito do primeiro convite;
- lembrete agendado duas horas antes;
- substituição do convite e do lembrete ao reagendar;
- revogação e aviso administrativo ao cancelar;
- métricas agregadas sem PII e isoladas por tenant.

Executar os testes específicos:

```bash
cd backend
pytest \
  apps/scheduling/tests/test_agenda_telemedicine.py \
  apps/scheduling/tests/test_telemedicine_communications.py \
  apps/scheduling/tests/test_telemedicine_metrics.py \
  --create-db
```

Validação completa:

```bash
python apps/core/quality/check_backend_architecture.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
ruff check .
mypy .
pytest --create-db
```

O workflow `Django CI` preserva relatórios de check, migrations, Ruff, mypy, pytest e cobertura como artefatos, inclusive quando um gate anterior falha.

## Frontend

`frontend/telemedicine-security.test.mjs` valida estruturalmente:

- leitura pelo fragmento;
- remoção imediata da URL;
- ausência de localStorage, sessionStorage e IndexedDB;
- worker E2EE;
- bloqueio de chat, gravação e compartilhamento de tela;
- cleanup de tracks, sala e worker;
- ausência de links persistidos no painel;
- allowlist pública restrita no BFF.

Executar:

```bash
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```

## Playwright E2E

`frontend/e2e/telemedicine.spec.ts` utiliza organização, assinatura, paciente, consulta e convite sintéticos. Câmera e microfone são simulados pelo Chromium; nenhuma conexão com o LiveKit é realizada nesse cenário.

O teste valida:

- remoção do fragmento antes da primeira interação;
- contexto público mínimo;
- aceite do consentimento;
- chegada à pré-entrada;
- ausência do convite no DOM, URL e storages;
- ausência de JWT e chave E2EE persistidos;
- mensagem genérica quando o convite não existe.

Executar com frontend e backend de teste já iniciados:

```bash
cd frontend/e2e
E2E_TELEMEDICINE_TOKEN=token-sintetico npm run test:telemedicine
```

Na CI, o workflow `Auth E2E` cria todo o contexto determinístico, instala Chromium e executa autenticação, telemedicina e indisponibilidade controlada do gateway.

## Smoke test de staging

A validação com mídia real deve ser manual ou executada em suíte separada, somente quando as credenciais de staging estiverem presentes.

Cenário mínimo:

1. criar consulta online;
2. gerar convite;
3. abrir paciente em navegador ou perfil separado;
4. aceitar termo e testar dispositivos;
5. entrar como profissional autenticado;
6. confirmar áudio e vídeo nos dois sentidos;
7. interromper temporariamente a rede e observar reconexão;
8. encerrar a sala;
9. confirmar revogação do convite;
10. confirmar eventos no webhook e ausência de conteúdo sensível nos logs.

Nunca usar dados reais de paciente em testes, capturas ou gravações.
