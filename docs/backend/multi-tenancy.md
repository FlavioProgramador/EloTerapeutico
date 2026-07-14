# Isolamento de dados e multi-tenancy

## Situação atual

O backend implementa isolamento principalmente por profissional autenticado, proprietário, autoria e relações autorizadas. Não existe uma entidade explícita de clínica ou tenant que permita afirmar suporte completo a múltiplas clínicas com equipes, unidades e administradores próprios.

Por isso, o termo correto para o estado atual é **isolamento por usuário/profissional**, e não multi-tenancy por clínica concluído.

## Como o escopo é identificado

O escopo normalmente parte de `request.user` e é aplicado em:

- querysets das views;
- selectors;
- managers e querysets customizados;
- validações de serializers;
- permissions por objeto;
- services que recebem o usuário como parâmetro;
- filtros de autoria e confidencialidade.

Exemplo conceitual:

```python
def get_patient_for_user(*, user, patient_id):
    return Patient.objects.filter(professional=user, id=patient_id).first()
```

Retornar `None` para um identificador fora do escopo reduz a possibilidade de enumeração de recursos.

## Recursos que exigem isolamento

- pacientes e responsáveis;
- prontuários, anamneses, evoluções e anexos;
- consultas, bloqueios, salas e pacotes;
- transações e relatórios financeiros;
- templates e documentos gerados;
- formulários e submissões;
- assinatura e cobranças SaaS;
- comunicações, preferências, tentativas e notificações;
- exportações e arquivos temporários.

## Regras obrigatórias

### Filtrar antes de resolver o identificador

Evite:

```python
resource = Resource.objects.get(id=resource_id)
if resource.owner_id != request.user.id:
    raise PermissionDenied
```

Prefira:

```python
resource = get_object_or_404(
    Resource.objects.filter(owner=request.user),
    id=resource_id,
)
```

A segunda forma evita revelar se o objeto existe para outro usuário.

### Validar relações recebidas

Um objeto principal filtrado corretamente ainda pode receber referências alheias no payload. Exemplos:

- consulta do terapeuta A associada ao paciente do terapeuta B;
- documento do terapeuta A criado com template do terapeuta B;
- transação vinculada a consulta fora do escopo;
- formulário associado a paciente não autorizado.

Serializers e services devem validar todas as relações no mesmo escopo.

### Preservar o escopo em tarefas e exportações

Workers não possuem `request.user`. O job persistido deve armazenar de forma segura o proprietário ou usuário solicitante e o worker deve reaplicar o escopo ao carregar os dados.

### Proteger arquivos

O UUID ou caminho do arquivo não é autorização. Antes do download:

1. carregue o registro pelo proprietário;
2. valide autoria ou permission adicional;
3. confirme que o arquivo pertence ao registro;
4. gere URL temporária ou resposta privada;
5. audite o acesso quando necessário.

## Administradores

Acesso administrativo ampliado deve ser explícito. Não use `is_staff` ou `is_superuser` como bypass implícito em toda consulta sem registrar a decisão.

Para cada exceção administrativa, documente:

- quem pode usar;
- em qual interface;
- quais recursos são visíveis;
- se o conteúdo clínico é exibido;
- como o acesso é auditado;
- quais exportações são permitidas.

## Confidencialidade por autor

Prontuários podem exigir uma camada adicional além do proprietário. Evoluções confidenciais devem ser filtradas por autor ou permission específica, mesmo quando mais de um profissional tiver acesso administrativo ao mesmo paciente no futuro.

## Billing

Planos, assinaturas, ordens e pagamentos devem ser resolvidos pelo usuário titular. Eventos de webhook não partem de um usuário autenticado; nesse caso, o escopo deve ser reconstruído a partir de identificadores externos previamente vinculados e validados.

## Comunicações públicas

Links públicos devem usar tokens:

- aleatórios e suficientemente fortes;
- persistidos apenas como hash;
- com expiração;
- com finalidade e escopo limitados;
- de uso único quando aplicável;
- sujeitos a rate limiting.

O token nunca transforma o endpoint em acesso amplo ao paciente ou prontuário.

## Testes mínimos de isolamento

Para cada domínio sensível, crie pelo menos dois usuários e confirme:

- usuário A lista apenas seus registros;
- usuário A recebe `404` ou negação equivalente ao consultar registro de B;
- usuário A não consegue criar vínculo com registro de B;
- filtros e busca não removem o escopo;
- exportação de A não contém dados de B;
- worker de A não processa dados de B;
- arquivos de B não são acessíveis por UUID conhecido;
- administradores seguem a regra explícita definida.

## Limitação arquitetural

Para suportar clínicas como tenants reais, será necessário introduzir um modelo organizacional, possivelmente com:

- clínica/organização;
- membros e papéis;
- profissionais vinculados;
- unidades;
- proprietário do recurso por organização;
- política de migração dos dados atuais;
- constraints compostas por tenant;
- auditoria e administração por clínica.

Essa evolução é funcional e não deve ser realizada em uma tarefa exclusivamente documental.
