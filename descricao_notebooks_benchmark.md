```markdown
## Descrição do Notebook `AlbiBooks_FaseII_Benchmark.ipynb`

### Objetivo
Este notebook é projetado para realizar um benchmark automatizado do sistema AlbiBooks Fase II, que utiliza a API Mistral para embeddings e a API Gemini para geração de respostas. O objetivo é processar um conjunto predefinido de perguntas, recolher respostas, documentos recuperados, contexto enviado ao LLM, e métricas de desempenho (tempo de execução e uso de memória) para cada pergunta.

### Pré-requisitos
1.  **Ficheiros de Índice:** Os artefactos de indexação gerados pelo `Copy_of_GrokTryIndexacao.ipynb` (ou similar) devem estar presentes no diretório especificado pela variável `EMBEDDINGS_DIR`. Estes incluem:
    *   `book_embeddings.npy`
    *   `book_metadata.pkl`
    *   `book_index.faiss`
2.  **Ficheiro de Perguntas:** Um ficheiro JSON (por defeito, `benchmark_universitario_perguntas.json`) contendo a lista de perguntas para o benchmark. Cada pergunta deve ter um "id" e um campo "pergunta".
3.  **API Keys:** As chaves API para Mistral AI e Google AI Studio (Gemini) devem estar configuradas como segredos no ambiente Google Colab (`MISTRAL_KEY` e `GOOGLE_API_KEY`).
4.  **Bibliotecas Python:** Todas as bibliotecas listadas na primeira célula de código devem estar instaladas.

### Funcionalidades Principais
- **Modo de Simulação:**
    - Uma flag `MODO_SIMULACAO` (booleana) permite executar o notebook sem fazer chamadas reais às APIs. Quando `True`, utiliza dados "dummy" para embeddings, busca, contexto e respostas. Isto é útil para testar o fluxo do notebook rapidamente.
    - `NUM_PERGUNTAS_SIMULACAO` limita o número de perguntas processadas em modo de simulação.
    - **IMPORTANTE:** Para uma execução real do benchmark, `MODO_SIMULACAO` deve ser definida como `False`.
- **Carregamento de Perguntas:** Lê as perguntas do ficheiro JSON especificado.
- **Processamento RAG por Pergunta:** Para cada pergunta:
    - Inicializa um histórico de conversa vazio (para independência dos testes).
    - Chama a função `answer_question` que:
        - Gera embedding da pergunta (Mistral API, ou simulado).
        - Realiza busca no índice FAISS (ou simulado).
        - Formata o contexto com os documentos recuperados.
        - Gera uma resposta usando Gemini API (ou simulado).
        - Mede o tempo de execução e o uso de memória.
- **Recolha de Resultados Detalhados:** Para cada pergunta, armazena:
    - ID da pergunta.
    - Texto da pergunta.
    - Resposta gerada.
    - Documentos recuperados (com detalhes como título, autor, score de relevância).
    - Contexto exato enviado ao Gemini.
    - Métricas de desempenho (tempo, memória).
- **Armazenamento dos Resultados:** Guarda todos os resultados num ficheiro JSON Lines (e.g., `benchmark_fase_ii_resultados.jsonl`), onde cada linha é um objeto JSON representando os resultados de uma pergunta.

### Como Utilizar
1.  Assegure-se de que todos os pré-requisitos estão cumpridos (ficheiros de índice, ficheiro de perguntas, API keys).
2.  Configure a flag `MODO_SIMULACAO`:
    - `True` para testes rápidos de fluxo.
    - `False` para a execução real do benchmark com chamadas às APIs.
3.  Defina os caminhos para o `perguntas_file` e `resultados_file` na última célula.
4.  Execute todas as células do notebook.
5.  Os resultados serão guardados no `resultados_file` especificado.
```

## Descrição do Notebook `AlbiBooks_Analise_Benchmark.ipynb`

### Objetivo
Este notebook é destinado a carregar, processar e analisar os resultados gerados pelo notebook de benchmarking `AlbiBooks_FaseII_Benchmark.ipynb`. Ele fornece ferramentas para calcular métricas de desempenho quantitativas, preparar os dados para avaliação qualitativa e visualizar os resultados.

### Pré-requisitos
1.  **Ficheiro de Resultados do Benchmark:** Um ficheiro JSON Lines (e.g., `benchmark_fase_ii_resultados.jsonl` ou `simulated_benchmark_fase_ii_resultados.jsonl`) gerado pelo `AlbiBooks_FaseII_Benchmark.ipynb`.
2.  **Bibliotecas Python:** Todas as bibliotecas listadas na primeira célula de código devem estar instaladas (pandas, matplotlib, seaborn, numpy, json).

### Funcionalidades Principais
- **Carregamento de Dados:**
    - A função `carregar_resultados(filepath)` lê o ficheiro JSON Lines e converte-o num DataFrame Pandas.
- **Análise de Métricas de Desempenho Quantitativas:**
    - Extrai as métricas de tempo de execução, memória usada e pico de memória da coluna `metricas_desempenho`.
    - Calcula estatísticas descritivas (média, mediana, min, max, desvio padrão) para estas métricas.
    - Gera visualizações como histogramas e boxplots para ilustrar a distribuição do tempo de resposta e, opcionalmente, do uso de memória.
- **Preparação para Análise Qualitativa:**
    - Adiciona colunas vazias (ou com valores padrão) ao DataFrame para que o utilizador possa posteriormente anotar manualmente a qualidade das respostas. As colunas sugeridas incluem:
        - `avaliacao_relevancia_resposta`
        - `avaliacao_precisao_resposta`
        - `avaliacao_completude_resposta`
        - `avaliacao_relevancia_docs_recuperados`
        - `observacoes_qualitativas`
    - O utilizador pode exportar este DataFrame para CSV/Excel, preencher estas colunas, e depois reimportá-lo para análises qualitativas mais profundas.
- **Análise de Documentos Recuperados:**
    - Calcula o número médio de documentos recuperados por pergunta.
    - Permite a análise dos `relevance_score` dos documentos recuperados (se disponíveis e relevantes para a métrica de distância usada).
- **Inspeção Detalhada de Casos Específicos:**
    - A função `mostrar_detalhes_pergunta(df, id_pergunta_ou_indice)` permite visualizar de forma formatada todos os dados recolhidos para uma pergunta específica (texto da pergunta, resposta, contexto enviado ao LLM, documentos recuperados, métricas), facilitando a análise aprofundada de casos de interesse.

### Como Utilizar
1.  Certifique-se de que o ficheiro de resultados do benchmark (e.g., `benchmark_fase_ii_resultados.jsonl`) está no caminho correto, conforme especificado na variável `resultados_benchmark_filepath`.
2.  Execute as células do notebook sequencialmente.
3.  Analise as estatísticas e gráficos gerados para as métricas de desempenho.
4.  Para a análise qualitativa:
    *   Pode exportar o DataFrame (após a célula "Preparação para Análise Qualitativa") para um formato como CSV.
    *   Preencha as colunas de avaliação manualmente nesse ficheiro.
    *   Reimporte o ficheiro CSV para o notebook para realizar análises sobre as avaliações (e.g., calcular médias de scores qualitativos, gerar gráficos de distribuição das avaliações).
5.  Utilize a função `mostrar_detalhes_pergunta` para investigar respostas ou comportamentos específicos.

Este notebook serve como um ponto de partida para a análise e pode ser expandido com visualizações e análises mais complexas conforme necessário.
```
