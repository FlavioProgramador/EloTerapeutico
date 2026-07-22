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
- presença de participante.

Executar:

```bash
cd backend
pytest apps/scheduling/tests/test_agenda_telemedicine.py --create-db
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
