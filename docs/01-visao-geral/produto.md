# Produto

## Problema tratado

Profissionais que realizam atendimentos terapêuticos costumam administrar agenda, dados cadastrais, registros clínicos, documentos e cobranças em ferramentas separadas. O Elo Terapêutico reúne esses fluxos em uma aplicação única e relaciona cada operação ao profissional autenticado.

## Público-alvo

- terapeutas e profissionais de saúde com agenda própria;
- secretárias com acesso administrativo limitado;
- administradores responsáveis pelo backoffice;
- equipes de suporte, implantação e desenvolvimento.

O código não restringe tecnicamente o produto a uma única especialidade. Há campos como especialidade, registro profissional e tipos de atendimento, mas regras regulatórias específicas precisam ser avaliadas para cada profissão.

## Proposta funcional

O sistema disponibiliza:

- cadastro e acompanhamento administrativo de pacientes;
- agenda com recorrências, bloqueios, salas e telemedicina;
- prontuário com conteúdo clínico criptografado e confidencialidade;
- controle financeiro do profissional;
- emissão de documentos e formulários;
- relatórios gerenciais;
- planos, assinaturas e pagamentos via Asaas;
- backoffice em Django Admin/Unfold;
- trilha de auditoria para operações sensíveis.

## Limite da proposta

A aplicação auxilia organização e registro. Ela não substitui julgamento clínico, avaliação jurídica, política institucional, consentimento adequado nem processo profissional de segurança da informação.

Implementação relacionada:

- `backend/apps/`
- `frontend/src/features/`
- `backend/config/urls.py`

[Voltar](README.md)
