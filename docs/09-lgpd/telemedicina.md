# LGPD e telemedicina

Este documento descreve controles técnicos. Não substitui análise jurídica, definição de bases legais, contratos, avisos de privacidade ou orientações dos conselhos profissionais aplicáveis.

## Categorias de dados

O módulo trata:

- identificação mínima do paciente e profissional já existente na Agenda;
- horários e estado operacional da consulta;
- registro de consentimento;
- entradas e saídas da sala;
- identificadores opacos do provedor;
- evidências de envio do convite.

O módulo não persiste:

- áudio;
- vídeo;
- transcrição;
- chat;
- gravação;
- conteúdo do prontuário dentro da chamada;
- localização precisa;
- IP bruto como evidência de consentimento.

## Consentimento

O aceite é registrado por sala, paciente e organização com:

- versão do documento;
- hash do texto;
- data e hora;
- método de aceite;
- nome do responsável legal, quando informado;
- eventual revogação sem apagar o histórico.

A ausência do aceite impede a emissão da credencial de mídia do paciente.

O consentimento para a modalidade online não deve ser confundido automaticamente com a base legal de todos os tratamentos de dados da plataforma.

## Minimização

Antes da entrada, o endpoint público retorna somente:

- nome público do profissional;
- nome da organização;
- data e horário;
- estado da sala;
- termo e versão;
- indicação de E2EE e ausência de gravação.

Não retorna diagnóstico, anotações, documentos, CPF, telefone, e-mail ou informações financeiras.

## Compartilhamento com o provedor

O LiveKit recebe identificadores opacos e metadado operacional de papel. Não recebe nomes reais ou conteúdo clínico pela integração do backend.

A organização deve avaliar contratualmente:

- localização e suboperadores;
- retenção de telemetria;
- mecanismos de transferência internacional, quando aplicáveis;
- resposta a incidentes;
- suporte ao exercício de direitos.

## Retenção

- convite: mantido como hash e revogado ao final do ciclo;
- consentimento: histórico versionado conforme política clínica e jurídica;
- sessão de participante: somente metadados operacionais;
- webhook: hash e resultado de processamento, sem payload bruto;
- mídia: não armazenada pelo Elo Terapêutico.

Os prazos finais devem ser definidos na política de retenção da operação.

## Direitos e transparência

A interface informa:

- finalidade da modalidade online;
- possibilidade de recusa e alternativa;
- orientações de privacidade;
- ausência de gravação;
- procedimento em caso de falha;
- que a sala não substitui serviços de emergência.

Solicitações de acesso, correção, oposição ou eliminação devem seguir o processo geral de privacidade do produto, respeitando obrigações legais e clínicas de conservação.
