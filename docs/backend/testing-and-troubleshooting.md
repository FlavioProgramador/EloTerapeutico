# Testes, qualidade e troubleshooting

## Preparação

```bash
cd backend
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Verificações principais

```bash
pytest --create-db
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
mypy .
python manage.py spectacular --file schema.yml --validate
```

Não altere testes ou regras de negócio apenas para obter resultado verde. Corrija a causa ou registre a limitação.

## Estratégia de testes

### Unitários

Cobrem:

- services e transições de estado;
- validators;
- selectors complexos;
- adapters e gateways com doubles;
- funções puras de cálculo e transformação.

### Integração

Cobrem:

- banco de dados e constraints;
- transações e `select_for_update`;
- storage;
- management commands;
- interação entre apps.

### API

Cobrem:

- autenticação;
- permissions;
- validação de payload;
- códigos HTTP;
- paginação e filtros;
- schema OpenAPI;
- isolamento entre usuários.

### Segurança

Prioridades:

- enumeração de conta;
- token expirado ou revogado;
- bloqueio de login;
- relações de outro proprietário;
- evolução confidencial;
- upload inválido;
- download sem autorização;
- webhook sem token;
- idempotência;
- ausência de segredos em logs.

## Fixtures e factories

Factories devem criar explicitamente:

- usuário/profissional proprietário;
- paciente associado;
- estados relevantes;
- timestamps necessários para janela de edição;
- identificadores externos fictícios;
- arquivos mínimos seguros.

Evite fixtures globais que ocultem o proprietário ou criem permissões excessivas.

Testes complexos devem possuir docstring curta explicando cenário, regra protegida e risco de regressão.

## Testes de multi-tenancy

Padrão mínimo:

```python
def test_user_cannot_access_other_users_patient(api_client, user_a, user_b):
    """Impede leitura de paciente por usuário que não é o proprietário."""
```

Repita o padrão para prontuário, agenda, financeiro, documentos, formulários, billing, comunicações, exportações e downloads.

## Testes de concorrência

Recursos críticos:

- sequência documental;
- consumo de pacote;
- recorrência;
- confirmação de pagamento;
- webhook duplicado;
- reserva de job;
- reprocessamento de comunicação.

SQLite não reproduz todas as características de bloqueio do PostgreSQL. Testes de concorrência relevantes devem ser executados também com PostgreSQL.

## Schema OpenAPI

Geração:

```bash
python manage.py spectacular --file schema.yml --validate
```

Verifique:

- paths e métodos;
- serializers corretos;
- parâmetros de filtro;
- autenticação;
- respostas de erro;
- paginação;
- endpoints públicos sem segurança global indevida;
- ausência de segredos e exemplos reais.

## Docker

Subida completa:

```bash
docker compose up --build
```

Verificação dos serviços:

```bash
docker compose ps
docker compose logs backend
docker compose logs worker
docker compose logs communications-worker
docker compose logs communications-scheduler
```

Execução pontual de checks:

```bash
docker compose exec backend python manage.py check
docker compose exec backend pytest --create-db
docker compose exec backend python manage.py makemigrations --check --dry-run
```

## Problemas comuns

### `SECRET_KEY`, `JWT_SECRET` ou `FIELD_ENCRYPTION_KEY` ausente

Sintoma: falha durante import dos settings ou inicialização.

Ação:

1. confirme se está executando via Docker ou diretamente;
2. use o `.env` correto;
3. configure valores diferentes;
4. reinicie o processo para recarregar o ambiente.

### Banco indisponível

Sintomas:

- conexão recusada;
- timeout;
- migrations não executadas.

Ações:

```bash
docker compose ps db
docker compose logs db
```

Confirme `DATABASE_URL`, host e porta. Dentro do Docker, `localhost` aponta para o próprio container e não para o serviço `db`.

### Migration pendente

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

Não gere migration vazia para esconder divergência. Investigue alteração de model ou migration ausente.

### Erro 401

Verifique:

- header `Authorization: Bearer`;
- expiração do access token;
- refresh token rotacionado;
- alteração recente de senha;
- relógio do ambiente;
- assinatura do JWT.

### Erro 403

Verifique:

- permission do endpoint;
- situação da assinatura;
- autoria/confidencialidade;
- perfil administrativo;
- estado ativo do recurso.

### Erro 404 em recurso conhecido

Pode indicar isolamento correto: o recurso existe, mas não pertence ao usuário autenticado. Confirme o proprietário antes de alterar a view.

### Asaas não configurado ou 502 no checkout

Verifique:

- `BILLING_ENABLED`;
- `ASAAS_API_KEY`;
- `ASAAS_BASE_URL`;
- ambiente sandbox versus produção;
- timeout e resposta do gateway;
- logs sanitizados do service;
- se o processo foi reiniciado após alterar o `.env`.

Não imprima a API key para depuração.

### Webhook não processado

Verifique:

- token configurado no backend e no provider;
- URL pública correta;
- identificador único do evento;
- status do evento persistido;
- tentativas e erro sanitizado;
- rotina de reconciliação.

### Exportação parada em `PROCESSING`

Verifique:

- processo `run_export_worker`;
- timeout de job abandonado;
- storage disponível;
- permissões de escrita;
- logs pelo identificador do job.

### Comunicações não enviadas

Verifique:

- `COMMUNICATIONS_ENABLED`;
- worker ativo;
- canal configurado;
- preferências do destinatário;
- limite de tentativas;
- provider e credenciais;
- scheduler para automações e retentativas.

### WeasyPrint falha fora do Docker

Instale as bibliotecas nativas exigidas pelo WeasyPrint no sistema operacional ou execute a geração dentro da imagem Docker do backend.

### Azure Blob não acessível

Verifique:

- connection string;
- nome do container;
- container privado existente;
- permissões da credencial;
- expiração da URL;
- relógio do servidor.

## Antes do Pull Request

- [ ] `python manage.py check`;
- [ ] migrations verificadas;
- [ ] testes relevantes executados;
- [ ] Ruff sem novos erros;
- [ ] mypy avaliado quando configurado;
- [ ] schema OpenAPI validado;
- [ ] documentação atualizada;
- [ ] nenhum segredo no diff;
- [ ] nenhuma regra de negócio alterada por uma tarefa documental.
