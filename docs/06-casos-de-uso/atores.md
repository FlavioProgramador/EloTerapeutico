# Atores

## Terapeuta

Profissional responsável por pacientes, agenda, registros clínicos, financeiro, documentos, formulários e assinatura do produto. É o principal proprietário lógico dos dados no modelo atual.

## Secretária

Usuária administrativa. Pode consultar e cadastrar dados administrativos conforme permissões, mas não deve acessar prontuário clínico ou conteúdo confidencial por padrão.

## Administrador

Usuário com role administrativa e/ou acesso ao backoffice. Role de domínio não é sinônimo de `is_staff` ou `is_superuser`. Acesso clínico confidencial exige permissão explícita.

## Paciente

Titular dos dados. Não há conta/portal completo de paciente comprovado; participa indiretamente por cadastro, convites, telemedicina, documentos e formulários.

## Worker de exportação

Processo interno que reserva jobs, gera PDF e atualiza o estado da exportação.

## Asaas

Sistema externo que processa assinaturas/cobranças e envia webhooks.

## Operador de suporte/DevOps

Mantém infraestrutura, segredos, banco, storage, logs, backup e incidentes. Deve usar privilégio mínimo e não consultar conteúdo clínico sem base e autorização.

[Voltar](README.md)
