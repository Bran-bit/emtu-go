# emtu-go

Package Go para acesso a dados de transporte público da EMTU na Baixada Santista.

Todos os dados vêm do site `m.piracicabana.com.br`, que é a fonte oficial do aplicativo
de ônibus em operação na região.

> **Status: em desenvolvimento.** O package ainda não tem nenhum código Go funcional.
> A documentação e a estrutura de dados estão definidas — a implementação começa agora.

---

## Roadmap

- [x] Investigar fontes de dados disponíveis
- [x] Descobrir e documentar endpoints da Piracicabana
- [x] Gerar mapeamento de linhas (`data/linhas.json`) via script Python
- [x] Documentar estrutura, origem dos dados e cadência de atualização
- [ ] `domain/linha.go` — structs: `Linha`, `Parada`, `Veiculo`, `Horario`
- [ ] `client/piracicabana.go` — `BuscarVeiculos(numero string)`
- [ ] `client/piracicabana.go` — `BuscarParadas(numero string)`
- [ ] `client/piracicabana.go` — `BuscarHorarios(numero string, tipoDia TipoDia)`
- [ ] `linhas.go` — `ListarLinhas()` lendo de `data/linhas.json`
- [ ] Testes para cada função
- [ ] Exemplo de uso em `example/main.go`

---

## O que este package oferecerá

```go
// Posição atual dos veículos de uma linha
veiculos, err := emtu.BuscarVeiculos("918")
// → []Veiculo{Prefixo, Lat, Lng, Sentido, Horario}

// Paradas de uma linha em sequência
paradas, err := emtu.BuscarParadas("918")
// → []Parada{ID, Endereco, Lat, Lng, Sequencia}

// Horários programados de uma linha por tipo de dia
horarios, err := emtu.BuscarHorarios("918", emtu.DiasUteis)
// → []string{"04:40", "05:05", "05:35", ...}

// Lista todas as linhas disponíveis com tarifa
linhas, err := emtu.ListarLinhas()
// → []Linha{Numero, Nome, Tarifa, VarLinha}
```

---

## Como os dados são obtidos

O site da Piracicabana não tem API pública documentada. Os endpoints foram descobertos
por engenharia reversa — interceptando as requisições do site com ferramentas de
debug de rede.

### Posição em tempo real

```
POST m.piracicabana.com.br/_versoes/3/backend/updateBus.php
User-Agent: Mozilla/5.0 ... Chrome
Body: v_company=115&v_linha={var_linha}&v_showpass=0&v_tryshowpass=0&v_myuser=11
```

O servidor bloqueia requisições sem User-Agent de browser — proteção anti-bot básica.
Não há autenticação, cookie ou sessão necessários.

O número público da linha (ex: 918) é mapeado para o ID interno (451) via
`data/linhas.json`. Esse arquivo é gerado pelo script `scripts/atualizar_linhas.py`
e precisa ser atualizado periodicamente — veja `data/README.md`.

### Paradas e horários

```
POST m.piracicabana.com.br/_versoes/3/backend/loadTrace.php
Body: v_sentido={sentido}&v_linha={var_linha}&v_empresa=115
```

Retorna o trajeto completo com coordenadas de cada parada em sequência.
Chamar com `v_sentido=1` retorna a ida, `v_sentido=2` retorna a volta.

### Lista de linhas

```
POST m.piracicabana.com.br/_versoes/3/parts/loadLines.php
Body: var_company=0&var_pesq=
```

Retorna HTML com todas as linhas, seus IDs internos e tarifas. O script
`scripts/atualizar_linhas.py` parseia esse HTML e gera o `data/linhas.json`.
Veja `docs/linhas-json.md` para entender esse processo em detalhe.

---

## Estrutura do repositório

```
emtu-go/
├── data/
│   ├── linhas.json          # mapeamento número → var_linha + tarifa
│   └── README.md            # origem dos dados e cadência de atualização
├── docs/
│   └── linhas-json.md       # como o linhas.json é formado e o que pode quebrar
└── scripts/
    └── atualizar_linhas.py  # gera data/linhas.json via scraping
```

---

## Dados locais

Veja `data/README.md` para entender quando e como atualizar `data/linhas.json`.

---

## Limitações

- Todos os endpoints são não oficiais — podem mudar sem aviso
- Se o site da Piracicabana mudar sua estrutura, os clientes precisam ser atualizados
- Cobertura limitada às linhas operadas pela Piracicabana na Baixada Santista

---

## Usado por

- `transit-finder` — cálculo de rotas de ônibus
