# Organizações, acesso e LGPD

## Escopo

`Organization` representa o ambiente de tratamento de dados utilizado pelo profissional individual ou pela clínica. A membership define a necessidade de acesso operacional de cada usuário.

## Minimização por papel

- **Owner/Admin:** administração da organização; acesso clínico ainda depende das regras do prontuário.
- **Therapist:** pacientes e registros permitidos pelo vínculo profissional e confidencialidade.
- **Receptionist:** dados cadastrais e de agenda estritamente necessários; sem conteúdo clínico.
- **Finance:** dados mínimos para cobrança, recebimento e relatório financeiro; sem conteúdo clínico.
- **Viewer:** leitura mínima autorizada, sem escrita ou exportação sensível.

A interface pode ocultar ações, mas a autorização definitiva é aplicada pela API.

## Rastreabilidade

Eventos sensíveis devem registrar:

- organização;
- ator;
- ação;
- tipo e identificador técnico do recurso quando compatível;
- data/hora;
- IP e user agent minimizados conforme política atual.

Não registrar conteúdo de evolução, anamnese, documento, mensagem, senha, token ou CPF completo.

## Convites

O convite utiliza token aleatório de uso único. Somente o hash é persistido. A aceitação exige:

- convite pendente;
- validade não expirada;
- organização ativa;
- e-mail autenticado compatível;
- ausência de membership duplicada.

Respostas públicas não devem facilitar enumeração de usuários.

## Direitos do titular e ciclo de vida

O tenant não altera as regras de:

- acesso e correção de dados;
- exportação autorizada;
- retenção clínica obrigatória;
- anonimização quando legalmente permitida;
- arquivamento não destrutivo;
- resposta a incidente.

A exclusão de uma organização não é exposta como remoção física comum. O status `archived` preserva integridade e rastreabilidade.

## Compartilhamento interno

A presença de um usuário na mesma clínica não concede acesso automático a todo prontuário. Registros confidenciais continuam limitados por autor e pelas capacidades clínicas aplicáveis.

## Storage e exportação

Arquivos privados devem utilizar caminhos com organização e identificadores não previsíveis:

```text
organizations/{organization_uuid}/patients/{patient_uuid}/...
```

Downloads e exportações exigem membership ativa e autorização no momento da geração e do download. URLs temporárias não substituem a validação do tenant.
