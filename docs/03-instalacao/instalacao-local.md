# Instalação local sem Docker

## 1. Clonar

```bash
git clone https://github.com/FlavioProgramador/EloTerapeutico.git
cd EloTerapeutico
```

## 2. Backend

Linux/macOS:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
Copy-Item .env.example .env
```

Edite `.env`. Para desenvolvimento simples, `DATABASE_URL=sqlite:///local.sqlite3` é suficiente. Defina placeholders locais para `SECRET_KEY`, `JWT_SECRET` e `FIELD_ENCRYPTION_KEY`; nunca reutilize esses valores em produção.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Em outro terminal:

```bash
cd backend
# ative o mesmo ambiente virtual
python manage.py run_export_worker
```

## 3. Frontend

```bash
cd frontend
npm ci
```

Crie `.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/
```

Execute:

```bash
npm run dev
```

## 4. Endereços

- aplicação: `http://localhost:3000`;
- API: `http://localhost:8000/api/v1/`;
- Swagger: `http://localhost:8000/api/docs/`;
- admin: `http://localhost:8000/admin/`;
- health check: `http://localhost:8000/api/health/`.

[Voltar](README.md)
