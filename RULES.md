# Regras Estritas de Produção e Versionamento

Estas regras são **obrigatórias** para qualquer desenvolvedor ou assistente de Inteligência Artificial trabalhando neste repositório.

## 1. Regras de Branching e Merging
- **NUNCA** faça commits diretos na branch `main`.
- **NUNCA** faça merge para a branch `main` sem que o usuário (Cleilton) solicite explicitamente e dê a aprovação final.
- O ambiente padrão de trabalho é **SEMPRE** a branch `development`.
- Novas features devem ser feitas em branches derivadas da `development` (ex: `feature/nova-rota`), e após finalizadas, unidas de volta à `development`.

## 2. Aprovação Obrigatória
O deploy automático está configurado na branch `main` no Render.com. Sendo assim, qualquer push ou merge para a `main` impacta imediatamente a produção. Portanto: **Apenas o usuário tem a palavra final para enviar código para a main**.
