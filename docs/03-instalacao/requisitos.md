# Requisitos

## Docker

- Docker Desktop ou Docker Engine com Compose v2;
- pelo menos 4 GB de memória livre recomendados;
- portas 3000, 8000 e 5432 disponíveis localmente.

## Sem Docker

| Componente | Recomendação derivada do repositório |
| --- | --- |
| Python | 3.12 |
| Node.js | 24 |
| npm | compatível com o lockfile |
| PostgreSQL | 15+ |
| Git | versão atual suportada |
| WeasyPrint | Pango e bibliotecas do sistema |

SQLite é aceito no desenvolvimento, mas não representa o comportamento de concorrência e locking do PostgreSQL.

## Windows

Use PowerShell, Python Launcher quando necessário e Docker Desktop com WSL2. WeasyPrint pode exigir instalação específica de bibliotecas; Docker reduz essa diferença.

[Voltar](README.md)
