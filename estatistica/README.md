# 📊 Módulo 1 — Fundamentos Matemáticos e Estatísticos

> **Concurso-alvo:** TRF1 — Analista Judiciário — Ciência de Dados e IA
> **Pré-requisito:** Nenhum. Este é o módulo inicial.
> **É pré-requisito para:** Todos os demais módulos

---

## 📚 Tópicos deste módulo

| Arquivo | Tópico | Peso em concurso |
|---------|--------|-----------------|
| [`1.1-estatistica-descritiva.md`](./1.1-estatistica-descritiva.md) | Estatística Descritiva | ⭐⭐⭐⭐ |
| [`1.2-probabilidade-distribuicoes.md`](./1.2-probabilidade-distribuicoes.md) | Probabilidade e Distribuições | ⭐⭐⭐⭐⭐ |
| [`1.3-inferencia-estatistica.md`](./1.3-inferencia-estatistica.md) | Inferência Estatística | ⭐⭐⭐⭐⭐ |
| [`1.4-regressao-linear.md`](./1.4-regressao-linear.md) | Análise de Regressão Linear | ⭐⭐⭐ |
| [`1.5-tecnicas-de-amostragem.md`](./1.5-tecnicas-de-amostragem.md) | Técnicas de Amostragem | ⭐⭐⭐⭐ |

---

## 🗺️ Mapa de dependências

```
[1.1 Estatística Descritiva]
         ↓
[1.2 Probabilidade e Distribuições]
         ↓
[1.3 Inferência Estatística]
         ↓
[1.4 Regressão Linear]
         ↓
[1.5 Técnicas de Amostragem]
         ↓
    [Módulo 2 ➡]
```

---

## 🏆 Os 20 pontos mais cobrados do Módulo 1

### Estatística Descritiva (1.1)
1. Na presença de outliers → use **mediana** (não a média)
2. Assimetria positiva: **Média > Mediana > Moda**
3. Assimetria negativa: **Média < Mediana < Moda**
4. Distribuição simétrica: **Média = Mediana = Moda**
5. Outlier pelo IQR: fora de [Q1 − 1,5×IQR ; Q3 + 1,5×IQR]

### Probabilidade (1.2)
6. P(A|B) = P(A∩B) / P(B) — probabilidade condicional
7. Eventos independentes: P(A∩B) = P(A) × P(B)
8. Teorema de Bayes: P(A|B) = [P(B|A) × P(A)] / P(B)
9. Regra **68-95-99,7** da distribuição normal (μ ± 1σ, 2σ, 3σ)
10. TCL: médias amostrais → normal para n ≥ 30, **independente** da distribuição original

### Inferência Estatística (1.3)
11. IC de 95%: se repetirmos, 95% dos IC conterão o parâmetro (não é probabilidade do parâmetro!)
12. Maior confiança = IC mais **largo**; maior n = IC mais **estreito**
13. p-valor < α → **rejeitar H₀**
14. Erro Tipo I = **Falso Positivo** (α) | Erro Tipo II = **Falso Negativo** (β)
15. **Correlação ≠ Causalidade** ← questão clássica!

### Regressão Linear (1.4)
16. β₁ = variação em Y para +1 unidade em X (mantendo demais constantes)
17. MQO minimiza a **soma dos quadrados** dos resíduos
18. R² ajustado (não R² simples) para comparar modelos com diferentes números de variáveis
19. Suposições LINE: **L**inearidade, **I**ndependência, **N**ormalidade, **E**rros homocedásticos
20. Multicolinearidade: VIF > 10 = problema severo

### Técnicas de Amostragem (1.5)
21. Estratificada: grupos **homogêneos** internamente; **todos** os estratos amostrados
22. Conglomerados: grupos **heterogêneos** internamente; apenas **alguns** grupos amostrados
23. Sistemática: k = N/n; risco de **periodicidade**
24. Apenas amostragem **probabilística** permite inferência estatística válida

---

## 💡 Abordagem de estudo recomendada

1. **Leia** o arquivo do tópico do início ao fim
2. **Resolva** os exemplos com papel e caneta
3. **Revise** a seção "O que mais cai em concurso"
4. **Resolva questões** de concursos anteriores sobre o tópico
5. **Avance** para o próximo tópico

---

*Atualizado em: 2026-02-17*
