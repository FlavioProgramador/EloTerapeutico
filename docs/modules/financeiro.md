# Especificação Técnica — Módulo Financeiro

Este documento descreve a arquitetura, regras de negócio, endpoints e modelo de dados implementado no **Módulo Financeiro** do Elo Terapêutico.

---

## 1. Arquitetura do Módulo

O módulo financeiro segue o padrão multi-tenant do projeto, isolando todos os lançamentos financeiros pelo terapeuta autenticado no backend. Ele é composto por:

* **Backend (Django):**
  * **Model (`FinancialTransaction`):** Representa lançamentos manuais ou integrados de receitas e despesas.
  * **Views & Actions (`TransactionViewSet`):** Exposição de rotas REST, incluindo controle de transições (`pay/`, `cancel/`, `refund/`), exportação de relatórios CSV (`export/`), e descoberta de consultas pendentes de faturamento (`unbilled-appointments/`).
  * **Filtros (`FinancialTransactionFilter`):** Filtros avançados por tipo, status, categoria e paciente.
* **Frontend (Next.js & TypeScript):**
  * **Hooks (React Query):** Mapeamento do ciclo de vida das transações (`useTransactions`, `useCreateTransaction`, `useCancelTransaction`, `useRefundTransaction`, etc.).
  * **UI Pages & Components:** Interface de fluxo financeiro, incluindo cards de resumo analítico, gráficos de barras dinâmicos em CSS responsivo, filtros e painel de faturamento rápido.

---

## 2. Modelo de Dados e Relacionamentos

### Entidade: `FinancialTransaction`
* **id** (IntegerField, PK)
* **therapist** (ForeignKey para User, FK): O terapeuta dono do lançamento.
* **patient** (ForeignKey para Patient, opcional, FK): Paciente associado.
* **appointment** (ForeignKey para Appointment, opcional, FK): Consulta associada.
* **transaction_type** (CharField): `"income"` (Receita) ou `"expense"` (Despesa).
* **category** (CharField): `"session"` (Sessão), `"subscription"` (Plano), `"material"` (Material), `"refund"` (Reembolso) ou `"other"` (Outro).
* **amount** (DecimalField): Valor monetário preciso com 2 casas decimais.
* **payment_status** (CharField): `"pending"`, `"paid"`, `"cancelled"` ou `"refunded"`.
* **payment_method** (CharField): `"pix"`, `"credit_card"`, `"debit_card"`, `"cash"`, `"bank_transfer"` ou `"other"`.
* **due_date** (DateField): Data de vencimento.
* **paid_at** (DateTimeField, opcional): Data/hora da compensação.
* **description** (TextField): Descrição ou observações.
* **receipt_url** (URLField): Link do recibo guardado em Azure Blob Storage.
* **created_at** e **updated_at**: Timestamps de auditoria.

### Propriedades Calculadas
* **is_overdue (Boolean):** Retorna `True` se `payment_status == "pending"` e a data atual for maior que `due_date`.

### Índices de Performance
* `fin_therapist_status_idx`: Busca eficiente por status de pagamento (ex: listar pendentes).
* `fin_therapist_created_idx`: Consultas cronológicas rápidas para resumos mensais e fluxos de caixa.

---

## 3. Estados e Transições Válidas

Para assegurar a consistência dos dados financeiros, transições de status inconsistentes são validadas e travadas a nível de modelo e API:

```
                  ┌──────────────┐
                  │   PENDENTE   │ (ou Vencido)
                  └──────┬───────┘
                         │
           ┌─────────────┼─────────────┐
           ▼                           ▼
      (pay action)              (cancel action)
           │                           │
           ▼                           ▼
     ┌───────────┐               ┌───────────┐
     │   PAGO    │               │ CANCELADO │
     └─────┬─────┘               └───────────┘
           │
     (refund action)
           │
           ▼
     ┌───────────┐
     │ ESTORNADO │
     └───────────┘
```

* **Transições Permitidas:**
  * `pending` ➔ `paid` (via endpoint `/pay/` ou `/pay`)
  * `pending` ➔ `cancelled` (via endpoint `/cancel/`)
  * `paid` ➔ `refunded` (via endpoint `/refund/`)
* **Transições Bloqueadas (Retorna HTTP 400 Bad Request):**
  * Pagar transação já paga ou cancelada.
  * Cancelar transação paga ou estornada.
  * Estornar transação pendente ou cancelada.

---

## 4. Endpoints da API (v1)

### Transações Financeiras (`/api/v1/financeiro/`)
* `GET /`: Lista transações filtradas do terapeuta logado.
* `POST /`: Cria um lançamento manual.
* `GET /{id}/`: Detalha uma transação.
* `PATCH /{id}/`: Edita uma transação.
* `DELETE /{id}/`: Remove um lançamento.
* `PATCH /{id}/pay/`: Quita a transação (registra pagamento).
* `POST /{id}/cancel/`: Cancela transação pendente.
* `POST /{id}/refund/`: Estorna transação paga.
* `GET /summary/`: Resumo analítico mensal.
* `GET /export/`: Baixa relatório de fluxo em CSV respeitando filtros.
* `GET /unbilled-appointments/`: Lista consultas finalizadas prontas para faturar.

---

## 5. Fórmulas de Indicadores Analíticos

Os indicadores exibidos na interface do terapeuta são calculados da seguinte forma:

* **Faturamento (Pago):**
  $$\text{Faturamento} = \sum \text{Receitas Pagas no Período}$$
* **Despesas Totais:**
  $$\text{Despesas} = \sum \text{Despesas Pagas no Período}$$
* **Saldo Líquido Realizado:**
  $$\text{Saldo Realizado} = \text{Receitas Pagas} - \text{Despesas Pagas}$$
* **A Receber (Pendentes):**
  $$\text{A Receber} = \sum \text{Receitas Pendentes (e Atrasadas) no Período}$$
* **Saldo Líquido Previsto:**
  $$\text{Saldo Previsto} = (\text{Receitas Pagas} + \text{Receitas Pendentes}) - (\text{Despesas Pagas} + \text{Despesas Pendentes})$$

---

## 6. Segurança e Isolamento Multi-Tenant

* **Garantia de Tenant:** O `therapist_id` do payload é ignorado e sobrescrito pelo backend com `request.user` durante o `create`.
* **Isolamento de CRUD:** O `get_queryset()` do viewset restringe todas as consultas ativamente usando `filter(therapist=request.user)`.
* **Validação de Associações:** Ao criar/editar, o serializer valida que o `patient` e o `appointment` associados pertencem ao mesmo terapeuta autenticado, bloqueando IDOR horizontal.
* **Segurança no CSV:** A exportação sanitiza descrições que começam com caracteres especiais (`=`, `+`, `-`, `@`) inserindo um caractere de escape (`'`) para evitar ataques de CSV Injection.
* **Logs Limpos:** Dados clínicos ou anotações sigilosas nunca são expostos em logs financeiros ou exportações.

---

## 7. Cobertura de Testes

Os testes automatizados foram criados em `apps/financeiro/tests/test_financeiro.py` utilizando o pytest. Eles validam:
1. Criação de transação com sucesso.
2. Sobrescrita de terapeuta no payload para impedir roubo de dados.
3. Impedimento de associação de paciente ou consulta de outros terapeutas.
4. Transições de status válidas e tratamento de exceções em inválidas.
5. Isolamento de listagem e detalhes (garantindo retorno 404 para dados alheios).
6. Exportação de relatório CSV com escape de fórmulas.
7. Listagem de consultas concluídas não faturadas.
