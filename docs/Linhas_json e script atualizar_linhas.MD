# Como o linhas.json é formado

Este documento explica a origem do arquivo `data/linhas.json`, como o script
que o gera funciona, o que pode quebrar e como detectar problemas.

---

## O problema

O site da Piracicabana não oferece uma API JSON para listar as linhas disponíveis.
O endpoint `loadLines.php` retorna HTML — a mesma página que o usuário vê no browser,
com os botões de cada linha renderizados como elementos HTML.

No momento, esta página foi a única fonte encontrada para obter o número das linhas de ônibus,
vide que o código usado para cada uma é diferente do número das linhas (Ex: a linha `918` no sistema corresponde a `451`, como exposto a seguir).

---

## O que o HTML contém

Cada linha aparece no HTML como um bloco com esta estrutura:

```html
<a href="busca-linha.php?lid=4a356c6c6643592f4974733d&cid=767059736e47653873384d3d&tpid=..."
   class="link-line">
    <div class="btn-inner-lines bg-light-btn-stops" id="451">
        <div class="text-lines">
            <b><span class="line-id bg-br">918</span>918 </b>
            <p>Casqueiro / Ilha Caraguatá / Centro de Santos / Ferry Boat</p>
            <p>R$ 6,00</p>
        </div>
    </div>
</a>
```

Desse bloco extraímos:

| Campo | Onde fica no HTML | Exemplo |
|---|---|---|
| `numero` | Texto do `<span class="line-id">` | `918` |
| `var_linha` | Atributo `id` do div interno | `451` |
| `lid` | Parâmetro `lid` do href | `4a356c6c6643592f4974733d` |
| `cid` | Parâmetro `cid` do href | `767059736e47653873384d3d` |
| `nome` | Texto do `<b>` sem o span | `918` ou `CIRCULAR 004` |
| `tarifa` | Texto do `<p>` que contém `R$` | `R$ 6,00` |

**O campo mais importante é `var_linha`** — é o ID interno que o sistema usa para
consultar posição em tempo real (`updateBus.php`) e trajeto (`loadTrace.php`).
O número público `918` é só o nome que o usuário vê.

---

## O script

**Arquivo:** `scripts/atualizar_linhas.py`
**Linguagem:** Python 3
**Dependências:** `requests`, `beautifulsoup4` (ambos instaláveis via `pip`)

O script faz uma requisição POST para `loadLines.php`, recebe o HTML, usa o
BeautifulSoup para navegar na estrutura HTML como se fosse um documento, extrai
os campos de cada linha e salva o resultado em `data/linhas.json`.

BeautifulSoup é uma biblioteca Python que transforma HTML em uma estrutura
navegável — equivalente a percorrer uma árvore de elementos. O script procura
todos os elementos com `class="link-line"` e extrai os dados de cada um.

---

## O que pode quebrar

O script depende da estrutura HTML do site da Piracicabana. Se eles mudarem
o HTML, o script pode quebrar de duas formas:

**Quebra ruidosa** — o script lança um erro e para. Fácil de detectar.
Acontece se o endpoint `loadLines.php` ficar fora do ar ou retornar erro HTTP.

**Quebra silenciosa** — o script roda sem erro mas extrai dados errados ou
incompletos. Mais perigoso. Acontece se:
- A classe CSS `link-line` for renomeada → script retorna lista vazia
- O atributo `id` do div for removido → `var_linha` fica vazio em todas as linhas
- O `<span class="line-id">` for reestruturado → `numero` fica errado

**Como detectar quebra silenciosa:**
Sempre rodar `git diff data/linhas.json` após o script e verificar:
- O número total de linhas não deve cair drasticamente (hoje são 124)
- A linha 918 deve ter `var_linha: "451"` — se mudou, algo está errado
- Nenhum campo deve aparecer vazio em massa

---

## Formato do linhas.json

```json
[
  {
    "numero": "918",
    "nome": "918918",
    "tarifa": "R$ 6,00",
    "var_linha": "451",
    "lid": "4a356c6c6643592f4974733d",
    "cid": "767059736e47653873384d3d"
  }
]
```

O campo `nome` às vezes aparece duplicado (`918918`) porque o HTML tem o número
dentro do span e repetido no texto do `<b>`. Isso é um artefato do HTML — o
campo relevante para uso é `numero`.

---

## Como o Go usa esse arquivo

O package `emtu-go` lê `data/linhas.json` uma vez na inicialização e mantém
o mapeamento em memória:

```go
// Internamente, algo assim:
mapa["918"] = Linha{VarLinha: "451", Tarifa: "R$ 6,00", ...}
```

Quando alguém chama `emtu.BuscarVeiculos("918")`, o código:
1. Lê `mapa["918"]` para obter `var_linha = "451"`
2. Faz o POST para `updateBus.php` com `v_linha=451`
3. Retorna os veículos encontrados

Se `linhas.json` estiver desatualizado, o Go vai tentar usar um `var_linha`
antigo — que pode não existir mais ou apontar para a linha errada. Por isso
a atualização periódica é importante.

---

## Alternativas consideradas e descartadas

**Noxxonsat:** API terceirizada que serviu dados da EMTU em projetos anteriores.
Certificado SSL expirado, campo de veículos sempre vazio, e menos atual que
o site da Piracicabana. Descartada em favor da fonte primária.

**API oficial da EMTU:** portal `api.emtu.sp.gov.br` com documentação de
API REST. Encontrei informações sobre esse site em um outro repositório, mas está fora do ar (01/03/2026).
Também há informações sobre "EMTU Dados Abertos", mas nenhum dos links disponibilizados funcionam.