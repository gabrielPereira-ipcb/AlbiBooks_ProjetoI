## Alterações nos Dados

A evolução do sistema de recomendação de livros evidencia alterações substanciais na forma como os dados são tratados, desde o volume e fonte até as estratégias de processamento para embeddings.

### 1. Volume de Dados

*   **Sistema Original (`AlbiBooks.ipynb`):**
    *   Operava com um volume de dados limitado, processando em tempo de execução as primeiras **500 linhas** do dataset `Eitanli/goodreads`. Estes 500 documentos resultavam em 1.126 chunks após o processo de divisão.
*   **Sistema Final (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):**
    *   Utiliza um conjunto de dados significativamente maior. Carrega um índice FAISS e metadados pré-existentes que correspondem a **18.266 livros indexados**.

A diferença no volume de dados é um dos principais fatores de mudança, com o sistema final tendo acesso a uma base de conhecimento aproximadamente 36 vezes maior, o que potencialmente aumenta a cobertura e a relevância das informações recuperadas.

### 2. Qualidade e Fonte dos Dados

*   **Sistema Original (`AlbiBooks.ipynb`):**
    *   A fonte de dados era o dataset público `Eitanli/goodreads`.
    *   Os metadados utilizados limitavam-se aos campos disponíveis neste dataset, como `Author`, `Book` (título) e `Genres`. O conteúdo principal para embedding era o campo `Description`.
    *   A qualidade dos dados era intrínseca à do dataset `Eitanli/goodreads`.

*   **Sistema Final (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):**
    *   Os metadados são carregados de um arquivo `book_metadata.pkl`, cuja origem (indicada pelo caminho no Google Drive `/projeto II V3/scrapyFiles/`) sugere um processo de coleta de dados customizado (scraping).
    *   A estrutura dos metadados no sistema final é consideravelmente mais rica e específica, incluindo campos como:
        *   `titulo`, `autor`, `co-autor`
        *   `idioma`
        *   `nome_comum` (representando assuntos ou palavras-chave)
        *   `pais`
        *   `analitico` (entradas analíticas, comuns em catálogos de biblioteca para capítulos de livros ou artigos em periódicos)
        *   `itype` (tipo de item, ex: livro, monografia)
        *   `shelvingloc` (localização física na estante)
        *   `call_no` (cota do livro no sistema da biblioteca)
    *   **Inferência:** A presença de campos como `shelvingloc` e `call_no` indica fortemente que os metadados da versão final são provenientes de um sistema de gerenciamento de bibliotecas (ILS - Integrated Library System) ou de um catálogo bibliográfico detalhado, e não apenas de um dataset genérico como o Goodreads. Estes dados são mais estruturados e alinhados com as necessidades de um assistente de biblioteca real, permitindo respostas mais precisas sobre a disponibilidade e localização física dos livros.

### 3. Estratégia de Chunking (Divisão de Texto)

*   **Sistema Original (`AlbiBooks.ipynb`):**
    *   Implementava explicitamente a divisão (chunking) das descrições dos livros utilizando `RecursiveCharacterTextSplitter`.
    *   Os parâmetros definidos eram `chunk_size=512` e `chunk_overlap=50`, com separadores baseados em Markdown.

*   **Sistema Final (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):**
    *   O código para chunking não está presente, pois o sistema carrega embeddings e um índice FAISS já processados.
    *   No entanto, é fundamental reconhecer que uma estratégia de chunking foi aplicada como uma etapa de **pré-processamento offline** para criar os embeddings dos 18.266 documentos. A qualidade e a granularidade desses chunks pré-existentes são cruciais para a eficácia do sistema de recuperação de informação. A escolha adequada do tamanho dos chunks e da sobreposição influencia diretamente a relevância dos contextos fornecidos ao LLM.

### 4. Normalização de Embeddings

*   **Sistema Original (`AlbiBooks.ipynb`):**
    *   Ao configurar o `HuggingFaceEmbeddings` com o modelo `thenlper/gte-small`, a opção `encode_kwargs={"normalize_embeddings": True}` era explicitamente definida. Isso garante que todos os vetores de embedding gerados localmente (para documentos e queries) fossem normalizados (usualmente para comprimento L2 unitário).

*   **Sistema Final (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):**
    *   **Embeddings de Documentos (Pré-calculados):** A normalização não é visível no código de carregamento. Contudo, para garantir consistência e otimizar a busca por similaridade (especialmente com métricas como cosseno ou produto escalar), é altamente provável e uma prática recomendada que os embeddings de documentos armazenados em `book_embeddings.npy` tenham sido normalizados durante o pré-processamento.
    *   **Embeddings de Queries (API Mistral):** A API `mistral-embed` utilizada para gerar os embeddings das queries retorna vetores que já são normalizados para comprimento 1, conforme a documentação da Mistral. A conversão para `.astype('float32')` no código é para compatibilidade com FAISS.

A manutenção da normalização dos embeddings em ambas as pontas (documentos e queries) é essencial para a precisão da busca por similaridade, pois assegura que as comparações de distância (ou similaridade) sejam consistentes e significativas.
