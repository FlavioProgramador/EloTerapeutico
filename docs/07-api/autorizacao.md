# Autorização da API

## Camadas

1. permissão global/autenticação DRF;
2. permission class do endpoint;
3. queryset/selector filtrado;
4. object permission;
5. regra de serviço/modelo;
6. permissão explícita para recursos confidenciais.

Nenhuma camada de frontend substitui essas verificações.

## Roles

- `therapist`: proprietário principal de pacientes e recursos;
- `secretary`: operações administrativas limitadas;
- `admin`: administração de domínio;
- `is_staff`/permissões Django: backoffice;
- `is_superuser`: privilégio técnico máximo, que não deve ser usado no dia a dia.

## Confidencialidade clínica

Evolução confidencial exige ser autor ou possuir codename explícito do app records. A função não usa bypass de superusuário. Exportação confidencial possui codename separado.

## Falha segura

Quando objeto não pertence ao escopo do usuário, prefira 404 ou 403 coerente sem revelar existência. Querysets devem ser filtrados antes de `get_object`.

[Voltar](README.md)
