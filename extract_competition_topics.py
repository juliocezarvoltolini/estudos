#!/usr/bin/env python3
"""
Extração e Geração de Guia de Estudo a partir de Editais de Concurso
=====================================================================
Fluxo completo em 10 etapas:
  1  Verificar dependências
  2  Carregar editais
  3  Identificar cargos de TI
  4  Extrair seções da matéria-alvo
  5  Mapear cargos × matéria × nível
  6  Extrair texto completo das seções por cargo
  7  Consolidar índice unificado (via LLM)
  8  Identificar dependências entre tópicos (via LLM)
  9  Gerar prompt de estudo (via LLM)
 10  Validar cobertura dos cargos
"""

import json
import re
import sys
import textwrap
from pathlib import Path

import fitz  # PyMuPDF

# ── Configuração ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent

EDITAIS: dict[str, Path] = {
    "TCU": BASE_DIR / "editais" / "Ed_1_TCU_25_AUFC_Abertura.pdf",
    "TCE-RN": BASE_DIR / "editais" / "Ed1TCERN25abertura.pdf",
    "TRF1": (
        BASE_DIR
        / "editais"
        / "EDITAL Nº 1, de 12 de junho de 2024 - EDITAL Nº 1, de 12 de junho de 2024 - DOU - Imprensa Nacional (1).PDF"
    ),
}

AREA_PROFISSIONAL: list[str] = [
    "tecnologia da informação",
    "analista de sistemas",
    "desenvolvimento",
    "infraestrutura",
    "ti ",
]

MATERIA = "direito administrativo"

OUTPUT_DIR = BASE_DIR / "output"

# ── Utilitários ───────────────────────────────────────────────────────────────


def sep(title: str = "", width: int = 70) -> None:
    if title:
        print(f"\n{'='*width}")
        print(f"  {title}")
        print(f"{'='*width}")
    else:
        print(f"\n{'-'*width}")


def save_text(filename: str, content: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"  → salvo em {path}")
    return path


# ── Etapa 1 — Verificar dependências ─────────────────────────────────────────


def etapa1_verificar_dependencias() -> None:
    sep("ETAPA 1 — Verificar dependências")
    print(f"  PyMuPDF {fitz.__version__} disponível")
    try:
        import anthropic  # noqa: F401

        print(f"  anthropic {anthropic.__version__} disponível")
    except ImportError:
        print("  AVISO: anthropic não instalado — etapas 7-9 desabilitadas")


# ── Etapa 2 — Carregar editais ────────────────────────────────────────────────


def etapa2_carregar_editais() -> dict[str, int]:
    sep("ETAPA 2 — Carregar editais")
    paginas: dict[str, int] = {}
    for nome, caminho in EDITAIS.items():
        if not caminho.exists():
            print(f"  AVISO: {nome} — arquivo não encontrado: {caminho}")
            continue
        doc = fitz.open(str(caminho))
        n = doc.page_count
        doc.close()
        paginas[nome] = n
        print(f"  {nome}: {n} páginas  ({caminho.name})")
    return paginas


# ── Etapa 3 — Identificar cargos relacionados à área profissional ─────────────


def etapa3_identificar_cargos() -> dict[str, list[tuple[int, str]]]:
    sep("ETAPA 3 — Identificar cargos de TI")
    resultados: dict[str, list[tuple[int, str]]] = {}

    for nome, caminho in EDITAIS.items():
        if not caminho.exists():
            continue
        doc = fitz.open(str(caminho))
        hits: list[tuple[int, str]] = []
        for i, page in enumerate(doc):
            if i >= 60:  # limitar busca às primeiras 60 páginas
                break
            text = page.get_text()
            if any(k in text.lower() for k in AREA_PROFISSIONAL):
                trecho = text[:1500].strip()
                hits.append((i + 1, trecho))
        doc.close()
        resultados[nome] = hits
        print(f"\n  {nome} — {len(hits)} página(s) com menção à área de TI")
        for pagina, trecho in hits[:3]:  # mostrar até 3
            print(f"    Página {pagina}:")
            for linha in trecho.splitlines()[:8]:
                print(f"      {linha}")
            print("      ...")

    return resultados


# ── Etapa 4 — Extrair seções da matéria-alvo ─────────────────────────────────


def etapa4_extrair_materia() -> dict[str, list[tuple[int, str]]]:
    sep(f"ETAPA 4 — Páginas com '{MATERIA}'")
    secoes: dict[str, list[tuple[int, str]]] = {}

    for nome, caminho in EDITAIS.items():
        if not caminho.exists():
            continue
        doc = fitz.open(str(caminho))
        hits: list[tuple[int, str]] = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if MATERIA in text.lower():
                hits.append((i + 1, text[:4000]))
        doc.close()
        secoes[nome] = hits
        paginas_str = ", ".join(str(p) for p, _ in hits)
        print(f"  {nome}: páginas [{paginas_str}]")

    return secoes


# ── Etapa 5 — Mapeamento manual de cargos × matéria ──────────────────────────
# Ajuste as páginas conforme a leitura prévia dos editais.


def etapa5_mapear_cargos(secoes: dict[str, list[tuple[int, str]]]) -> dict[str, dict]:
    sep("ETAPA 5 — Mapear cargos de TI × matéria")

    # Inferir páginas automaticamente a partir do mapeamento da Etapa 4
    def paginas_de(edital: str) -> list[int]:
        return [p for p, _ in secoes.get(edital, [])]

    CARGOS_TI: dict[str, dict] = {
        "TCU": {
            "cargo": "AUFC — Auditoria de TI",
            "nivel": "Completo",
            "edital": "TCU",
            "paginas": paginas_de("TCU"),
        },
        "TCE-RN_C4": {
            "cargo": "Analista Administrativo — TI Desenvolvimento",
            "nivel": "Noções",
            "edital": "TCE-RN",
            "paginas": paginas_de("TCE-RN"),
        },
        "TCE-RN_C5": {
            "cargo": "Analista Administrativo — TI Infraestrutura",
            "nivel": "Noções",
            "edital": "TCE-RN",
            "paginas": paginas_de("TCE-RN"),
        },
        "TCE-RN_C12": {
            "cargo": "Auditor de Controle Externo — TI",
            "nivel": "Noções",
            "edital": "TCE-RN",
            "paginas": paginas_de("TCE-RN"),
        },
        "TRF1_TI": {
            "cargo": "Analista Judiciário — Análise de Sistemas",
            "nivel": "Noções",
            "edital": "TRF1",
            "paginas": paginas_de("TRF1"),
        },
    }

    for cid, info in CARGOS_TI.items():
        print(
            f"  {cid}: {info['cargo']} | {info['nivel']} | "
            f"páginas {info['paginas']}"
        )

    return CARGOS_TI


# ── Etapa 6 — Extrair texto das seções por cargo ─────────────────────────────


def extrair_paginas(caminho: Path, paginas: list[int]) -> str:
    if not caminho.exists() or not paginas:
        return ""
    doc = fitz.open(str(caminho))
    texto = ""
    for p in paginas:
        if 1 <= p <= doc.page_count:
            texto += f"\n--- Página {p} ---\n"
            texto += doc[p - 1].get_text()
    doc.close()
    return texto


def etapa6_extrair_secoes(cargos_ti: dict[str, dict]) -> dict[str, str]:
    sep("ETAPA 6 — Extrair texto por cargo")
    textos: dict[str, str] = {}
    blocos_para_arquivo: list[str] = []

    for cid, info in cargos_ti.items():
        caminho = EDITAIS.get(info["edital"])
        if caminho is None or not caminho.exists():
            print(f"  {cid}: edital '{info['edital']}' não encontrado — pulando")
            continue
        texto = extrair_paginas(caminho, info["paginas"])
        textos[cid] = texto
        bloco = (
            f"\n{'='*60}\n"
            f"CARGO: {info['cargo']}  |  NÍVEL: {info['nivel']}\n"
            f"EDITAL: {info['edital']}  |  PÁGINAS: {info['paginas']}\n"
            f"{'='*60}\n"
            f"{texto[:3000]}"
        )
        print(bloco[:600] + "\n  ...")
        blocos_para_arquivo.append(bloco)

    conteudo = "\n".join(blocos_para_arquivo)
    save_text("etapa6_secoes_por_cargo.txt", conteudo)
    return textos


# ── Etapa 7 — Consolidar índice unificado via LLM ────────────────────────────


PROMPT_CONSOLIDAR = """
Você é um especialista em concursos públicos brasileiros.

Abaixo estão os textos extraídos das seções de **{materia}** dos editais:

{textos}

**Sua tarefa:**
1. Liste TODOS os tópicos e subtópicos de {materia} mencionados nos textos acima.
2. Para cada tópico, indique em quais editais/cargos ele aparece:
   - TCU (nível Completo)
   - TCE-RN TI (nível Noções)
   - TRF1 TI (nível Noções)
3. Indique qualquer legislação específica mencionada junto ao tópico.
4. Retorne uma tabela Markdown com colunas:
   | Tópico | TCU | TCE-RN (TI) | TRF1 (TI) | Legislação |
   usando ✓ para presença e — para ausência.
5. Após a tabela, liste os tópicos como JSON puro (array de strings) sob a chave "topicos".

Formato de saída esperado:
```markdown
<tabela>
```
```json
{{"topicos": ["Tópico 1", "Tópico 2", ...]}}
```
"""


def _get_anthropic_client():
    """Retorna cliente Anthropic ou None se a chave não estiver configurada."""
    import os

    try:
        import anthropic
    except ImportError:
        return None, "anthropic não instalado"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None, (
            "ANTHROPIC_API_KEY não definida — configure a variável de ambiente "
            "para habilitar as etapas 7-9.\n"
            "  Exemplo: export ANTHROPIC_API_KEY=sk-ant-..."
        )

    return anthropic.Anthropic(api_key=api_key), None


LLM_MODEL = "claude-sonnet-4-6"


def _salvar_prompt_para_uso_manual(filename: str, textos: dict[str, str]) -> None:
    """Salva o prompt completo para uso manual num LLM externo."""
    blocos = [f"### {cid}\n{texto[:6000]}" for cid, texto in textos.items()]
    contexto = "\n\n".join(blocos)
    conteudo = PROMPT_CONSOLIDAR.format(materia=MATERIA.title(), textos=contexto)
    path = save_text(filename, conteudo)
    print(
        f"  Prompt salvo em {path}.\n"
        "  Cole seu conteúdo num LLM (ex: claude.ai) para obter o índice consolidado."
    )


def etapa7_consolidar_indice(textos: dict[str, str]) -> tuple[str, list[str]]:
    sep("ETAPA 7 — Consolidar índice unificado (via LLM)")

    client, erro = _get_anthropic_client()
    if client is None:
        print(f"  AVISO: {erro}")
        _salvar_prompt_para_uso_manual("etapa7_prompt_consolidar.txt", textos)
        return "", []

    # Montar contexto com amostras de cada cargo (limite de tokens)
    blocos: list[str] = []
    for cid, texto in textos.items():
        blocos.append(f"### {cid}\n{texto[:6000]}")
    contexto = "\n\n".join(blocos)

    prompt = PROMPT_CONSOLIDAR.format(materia=MATERIA.title(), textos=contexto)

    print("  Chamando Claude para consolidar índice...")
    resposta = client.messages.create(
        model=LLM_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    conteudo = resposta.content[0].text
    save_text("etapa7_indice_unificado.md", conteudo)
    print(conteudo[:1000] + "\n  ...")

    # Extrair lista JSON de tópicos
    topicos: list[str] = []
    match = re.search(r'```json\s*(\{.*?\})\s*```', conteudo, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            topicos = data.get("topicos", [])
        except json.JSONDecodeError:
            pass

    if not topicos:
        # fallback: extrair linhas da tabela
        for linha in conteudo.splitlines():
            linha = linha.strip()
            if linha.startswith("|") and "✓" in linha:
                partes = [c.strip() for c in linha.split("|")]
                if len(partes) > 1:
                    topicos.append(partes[1])

    print(f"\n  {len(topicos)} tópico(s) extraído(s)")
    return conteudo, topicos


# ── Etapa 8 — Identificar dependências entre tópicos ─────────────────────────


PROMPT_DEPENDENCIAS = """
Você é um especialista em Direito Administrativo e concursos públicos.

Lista de tópicos de **{materia}** a sequenciar:

{topicos_numerados}

**Sua tarefa:**
Para cada tópico acima, identifique suas dependências e classifique em níveis:

- **Nível 1 (Fundamentos):** sem dependências — base conceitual
- **Nível 2 (Estrutura):** depende do Nível 1
- **Nível 3 (Instrumentos):** depende dos Níveis 1 e 2
- **Nível 4 (Controles):** depende dos Níveis 1, 2 e 3
- **Nível 5 (Procedimentos e Contratos):** depende de todos os anteriores

Dentro de cada nível, ordene por frequência de cobrança em provas CEBRASPE/FGV.

Retorne:
1. Uma seção Markdown descrevendo cada nível com os tópicos ordenados.
2. Um bloco JSON com a estrutura:
```json
{{
  "niveis": {{
    "1": ["tópico A", "tópico B"],
    "2": ["tópico C"],
    ...
  }}
}}
```
"""


def etapa8_identificar_dependencias(topicos: list[str]) -> tuple[str, dict]:
    sep("ETAPA 8 — Identificar dependências entre tópicos (via LLM)")

    if not topicos:
        print("  Nenhum tópico disponível — etapa ignorada")
        return "", {}

    client, erro = _get_anthropic_client()
    if client is None:
        print(f"  AVISO: {erro}")
        topicos_numerados = "\n".join(f"{i+1}. {t}" for i, t in enumerate(topicos))
        prompt_txt = PROMPT_DEPENDENCIAS.format(
            materia=MATERIA.title(), topicos_numerados=topicos_numerados
        )
        save_text("etapa8_prompt_dependencias.txt", prompt_txt)
        return "", {}

    topicos_numerados = "\n".join(f"{i+1}. {t}" for i, t in enumerate(topicos))
    prompt = PROMPT_DEPENDENCIAS.format(
        materia=MATERIA.title(),
        topicos_numerados=topicos_numerados,
    )

    print("  Chamando Claude para mapear dependências...")
    resposta = client.messages.create(
        model=LLM_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    conteudo = resposta.content[0].text
    save_text("etapa8_dependencias.md", conteudo)
    print(conteudo[:800] + "\n  ...")

    niveis: dict = {}
    match = re.search(r'```json\s*(\{.*?\})\s*```', conteudo, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            niveis = data.get("niveis", {})
        except json.JSONDecodeError:
            pass

    return conteudo, niveis


# ── Etapa 9 — Gerar prompt de estudo ─────────────────────────────────────────


PROMPT_ESTUDO_TEMPLATE = """
Você é um professor especialista em concursos públicos, referência nas bancas
CEBRASPE e FGV, e agora irá criar um roteiro de ensino completo de
**{materia}** para candidatos que concorrem a cargos de Tecnologia da
Informação nos seguintes concursos:

- **TCU 2025** — AUFC Auditoria de TI (nível Completo)
- **TCE-RN 2025** — Analista Administrativo TI e Auditor de Controle Externo TI (nível Noções)
- **TRF1 2024** — Analista Judiciário — Análise de Sistemas (nível Noções)

---

## Sequência de estudo

{sequencia_niveis}

---

## Instrução de ensino

Para **cada tópico**, na ordem indicada acima, siga rigorosamente a estrutura:

1. **Conceito direto** — definição objetiva, sem rodeios
2. **Elementos e características** — enumere os atributos essenciais
3. **Distinções com institutos similares** — compare e contraste
4. **Fundamentação legal** — cite lei, decreto ou súmula aplicável
5. **Caso prático resolvido** — situação hipotética com resolução passo a passo
6. **Pegadinhas e pontos de atenção** — erros frequentes dos candidatos

Ao final de cada tópico, indique quais editais o cobram:
  `[TCU]` `[TCE-RN]` `[TRF1]`

---

## Questões de fixação

Ao final de **cada nível** (grupo de tópicos), gere:

- **5 questões CEBRASPE** (Certo/Errado) cobrindo os tópicos do nível,
  incluindo gabarito comentado.
- **3 questões FGV** (múltipla escolha, 5 alternativas) com gabarito comentado.

---

## Observações finais

- Sinalize tópicos cobrados de forma **conceitual** vs. **aplicação em casos práticos**.
- Para tópicos de nível "Noções", priorize conceitos gerais e exemplos simples.
- Para tópicos de nível "Completo" (TCU), aprofunde doutrina e jurisprudência.
"""


def etapa9_gerar_prompt_estudo(niveis: dict, textos_brutos: dict[str, str] | None = None) -> str:
    sep("ETAPA 9 — Gerar prompt de estudo")

    nomes_nivel = {
        "1": "Fundamentos",
        "2": "Estrutura",
        "3": "Instrumentos",
        "4": "Controles",
        "5": "Procedimentos e Contratos",
    }

    if niveis:
        linhas: list[str] = []
        for nivel_num in sorted(niveis.keys(), key=lambda x: int(x)):
            topicos_nivel = niveis[nivel_num]
            nome = nomes_nivel.get(str(nivel_num), f"Nível {nivel_num}")
            linhas.append(f"### Nível {nivel_num} — {nome}")
            for t in topicos_nivel:
                linhas.append(f"- {t}")
            linhas.append("")
        sequencia = "\n".join(linhas)

    elif textos_brutos:
        # Fallback: gerar sequência sugerida a partir dos tópicos encontrados nos textos
        sequencia = _sequencia_fallback(textos_brutos)
    else:
        sequencia = (
            "_Sequência não gerada automaticamente — "
            "defina ANTHROPIC_API_KEY e reexecute para ativar as etapas 7-9._"
        )

    prompt_final = PROMPT_ESTUDO_TEMPLATE.format(
        materia=MATERIA.title(),
        sequencia_niveis=sequencia,
    )

    path = save_text("etapa9_prompt_de_estudo.md", prompt_final)
    print(f"\n  Prompt de estudo gerado com {len(prompt_final)} caracteres → {path}")
    print(textwrap.indent(prompt_final[:500], "  ") + "\n  ...")
    return prompt_final


def _sequencia_fallback(textos: dict[str, str]) -> str:
    """
    Extrai tópicos de Direito Administrativo dos textos brutos e organiza em
    uma sequência sugerida de 5 níveis sem necessitar de LLM.
    """
    # Ordem clássica de DA para concursos — serve de âncora para os tópicos encontrados
    ORDEM_SUGERIDA: list[tuple[str, list[str]]] = [
        (
            "Fundamentos",
            [
                "princíp",
                "conceito",
                "regime jurídico",
                "fontes",
                "administração pública",
                "organização",
            ],
        ),
        (
            "Estrutura",
            [
                "órgão",
                "entidade",
                "agência",
                "autarquia",
                "fundação",
                "empresa pública",
                "sociedade de economia",
                "descentralização",
                "desconcentração",
                "poder de polícia",
            ],
        ),
        (
            "Instrumentos",
            [
                "ato administrativo",
                "atributo",
                "classificação",
                "invalidação",
                "convalidação",
                "extinção",
                "discricionário",
                "vinculado",
            ],
        ),
        (
            "Controles",
            [
                "controle",
                "legalidade",
                "responsabilidade",
                "improbidade",
                "prescrição",
                "recurso",
                "revisão",
            ],
        ),
        (
            "Procedimentos e Contratos",
            [
                "licitação",
                "contrato",
                "processo administrativo",
                "serviço público",
                "concessão",
                "permissão",
                "bens públicos",
                "desapropriação",
                "tombamento",
                "servidão",
            ],
        ),
    ]

    # Coletar linhas de conteúdo programático de todos os textos
    linhas_da: list[str] = []
    for texto in textos.values():
        for linha in texto.splitlines():
            l = linha.strip()
            if len(l) > 10 and any(
                k in l.lower()
                for k in [
                    "princíp",
                    "ato admin",
                    "licitação",
                    "contrato",
                    "processo admin",
                    "poder de polícia",
                    "responsab",
                    "improbidade",
                    "controle",
                    "serviço público",
                    "bens públicos",
                    "agente",
                    "desapropriação",
                    "órgão",
                    "entidade",
                    "autarquia",
                    "concessão",
                ]
            ):
                linhas_da.append(l)

    # Deduplica preservando ordem
    vistas: set[str] = set()
    linhas_unicas: list[str] = []
    for l in linhas_da:
        chave = l[:60].lower()
        if chave not in vistas:
            vistas.add(chave)
            linhas_unicas.append(l)

    # Distribuir pelos níveis
    saida: list[str] = []
    for num, (nome_nivel, palavras) in enumerate(ORDEM_SUGERIDA, start=1):
        itens = [l for l in linhas_unicas if any(p in l.lower() for p in palavras)]
        if itens:
            saida.append(f"### Nível {num} — {nome_nivel} _(sequência sugerida)_")
            for item in itens[:15]:  # máximo 15 por nível
                saida.append(f"- {item}")
            saida.append("")

    if not saida:
        return "_Nenhum tópico de DA identificado automaticamente nos textos._"

    saida.append(
        "> **Nota:** Esta sequência foi gerada automaticamente a partir dos textos "
        "dos editais. Para uma sequência com dependências precisas, configure "
        "`ANTHROPIC_API_KEY` e reexecute o script."
    )
    return "\n".join(saida)


# ── Etapa 10 — Validar cobertura ─────────────────────────────────────────────


def etapa10_validar_cobertura(cargos_ti: dict[str, dict], textos: dict[str, str]) -> None:
    sep("ETAPA 10 — Validar cobertura dos cargos")
    ok = True
    for cid, info in cargos_ti.items():
        texto = textos.get(cid, "")
        if not texto.strip():
            print(f"  ATENÇÃO: cargo '{cid}' ({info['cargo']}) sem texto extraído.")
            ok = False
        elif len(texto.strip()) < 200:
            print(
                f"  ATENÇÃO: cargo '{cid}' tem texto muito curto "
                f"({len(texto.strip())} chars) — verifique as páginas."
            )
            ok = False
        else:
            print(f"  OK: {cid} — {len(texto.strip())} chars extraídos")
    if ok:
        print("\n  Todos os cargos possuem conteúdo extraído.")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    print("\n" + "=" * 70)
    print("  EXTRAÇÃO E GERAÇÃO DE GUIA DE ESTUDO — EDITAIS DE CONCURSO")
    print("=" * 70)

    etapa1_verificar_dependencias()
    etapa2_carregar_editais()
    etapa3_identificar_cargos()
    secoes = etapa4_extrair_materia()
    cargos_ti = etapa5_mapear_cargos(secoes)
    textos = etapa6_extrair_secoes(cargos_ti)

    # Etapas que dependem de LLM (requerem ANTHROPIC_API_KEY)
    _, topicos = etapa7_consolidar_indice(textos)
    _, niveis = etapa8_identificar_dependencias(topicos)
    etapa9_gerar_prompt_estudo(niveis, textos_brutos=textos)

    etapa10_validar_cobertura(cargos_ti, textos)

    sep("CONCLUÍDO")
    print(f"  Arquivos gerados em: {OUTPUT_DIR}/")
    for arq in sorted(OUTPUT_DIR.glob("*.md")) if OUTPUT_DIR.exists() else []:
        print(f"    {arq.name}")
    for arq in sorted(OUTPUT_DIR.glob("*.txt")) if OUTPUT_DIR.exists() else []:
        print(f"    {arq.name}")


if __name__ == "__main__":
    main()
