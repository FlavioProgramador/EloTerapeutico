# Funcionalidades

## ✅ Implementadas

### Identidade e acesso

- cadastro, login e logout;
- access e refresh tokens JWT;
- rotação e blacklist de refresh tokens;
- alteração e redefinição de senha;
- bloqueio temporário após falhas consecutivas;
- perfil e horários de atendimento;
- papéis `therapist`, `secretary` e `admin`.

### Operação clínica

- cadastro e arquivamento lógico de pacientes;
- responsáveis legal e financeiro;
- consultas, recorrências, salas e bloqueios;
- evoluções com janela de edição de 48 horas;
- aditivos, versões, anamnese, metas e formulários clínicos;
- documentos e anexos clínicos com validações de upload;
- exportações clínicas em fila persistida no banco.

### Administração e receita

- receitas, despesas, pagamentos e mensalidades;
- modelos e documentos gerados;
- construtor e submissões de formulários;
- relatórios por domínio;
- planos, assinatura e checkout Asaas;
- auditoria e backoffice Unfold.

## 🟡 Parcialmente implementadas ou dependentes do ambiente

- telemedicina: existem modelos, rotas e tokens de acesso, mas operação em produção depende de infraestrutura e validação de privacidade;
- storage Azure: há configuração, mas o repositório não comprova conta ou container implantado;
- e-mail: console no desenvolvimento e SMTP configurável em produção;
- observabilidade: logging JSON está configurado, mas integração efetiva com serviço de monitoramento não é comprovada;
- IA clínica: há endpoint de status/resumo no prontuário, porém não deve ser tratado como diagnóstico ou automação clínica autônoma.

## 🔴 Não comprovadas

- tenant/clínica explícito e isolamento multi-clínica completo;
- política automática de retenção e descarte de dados;
- backup e restauração automatizados pelo repositório;
- antivírus/antimalware para uploads;
- gestão de consentimento jurídico completa;
- implantação em produção comprovada.

[Voltar](README.md)
