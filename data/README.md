# Dados locais — emtu-go

Este diretório contém dados que mudam raramente mas precisam de atualização periódica.
Eles não pertencem ao código porque têm ciclo de vida próprio — mudam por decisão
externa (reajuste tarifário, criação de nova linha) e não por mudança na lógica do sistema.

O Go lê esses arquivos JSON na inicialização. O Python os gera via scraping.
As duas linguagens nunca se comunicam diretamente — o JSON é o contrato entre elas.

---

## linhas.json

Mapeamento de todas as linhas disponíveis. Gerado pelo script
`scripts/atualizar_linhas.py`. Veja `docs/linhas-json.md` para entender
em detalhes como esse arquivo é formado e o que pode quebrar.

**Quando atualizar:**

| Evento | Cadência |
|---|---|
| Reajuste de tarifas | Anualmente, em geral janeiro |
| Nova linha criada ou desativada | Sem cadência fixa — monitorar |
| Atualização preventiva | Mensal |

**Como atualizar manualmente:**

```bash
cd scripts
python3 atualizar_linhas.py
git diff ../data/linhas.json
# Revisar o diff antes de commitar
git add ../data/linhas.json
git commit -m "data: atualiza mapeamento de linhas - $(date +%Y-%m)"
```

**O que verificar no diff:**
- Linhas novas adicionadas — confirmar se é linha real ou erro de parsing
- Linhas removidas — confirmar se foi desativada ou se o HTML mudou
- Tarifas alteradas — comparar com comunicado oficial da EMTU

---

## Por que não buscar em tempo real?

O endpoint `loadLines.php` retorna HTML, não JSON. Parsear HTML a cada requisição
seria lento e frágil. O mapeamento de linhas muda em escala de meses, não de segundos.
Gerar o JSON uma vez e cachear localmente é a decisão certa para esse tipo de dado.

---

## Agendamento futuro

Quando o projeto tiver um servidor, o script pode ser agendado via `cron` — o
agendador de tarefas do Linux. Exemplo para rodar todo dia 1 de cada mês às 9h:

```
0 9 1 * * cd /caminho/emtu-go && python3 scripts/atualizar_linhas.py
```

Por enquanto, a atualização é manual seguindo os passos acima.
