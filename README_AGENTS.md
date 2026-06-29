# Agentes Antigravity — Elo Terapêutico

Pacote de personas, Skills e Workflows para o Google Antigravity.

## Instalação

1. Extraia o pacote na raiz do repositório.
2. Confirme que `.agents` ficou diretamente na raiz.
3. Reabra o workspace no Antigravity.
4. Pergunte: `Quais Skills estão disponíveis?`
5. Digite `/` para conferir os workflows.
6. Comece com `/planejar-modulo autenticacao-permissoes`.

## Fluxo

```text
/planejar-modulo <modulo>
→ revisar docs/modules/<modulo>-spec.md
→ responder "Aprovado"
→ /desenvolver-modulo <modulo>
→ /validar-modulo <modulo>
→ /preparar-pr
```

## Ordem sugerida

1. autenticação e permissões;
2. pacientes;
3. agenda;
4. sessões e prontuários;
5. financeiro;
6. landing page;
7. testes integrados;
8. segurança;
9. documentação e Docker.

Use uma branch ou Worktree diferente por módulo.
