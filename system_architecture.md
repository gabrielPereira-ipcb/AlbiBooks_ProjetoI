## Arquitetura do Sistema

Esta seção detalha a arquitetura do sistema de recomendação de livros, comparando a versão original (`AlbiBooks.ipynb`) com a versão final (`Copy_of_GeminiFlash2p5V6Stable.ipynb`).

### Arquitetura do Sistema Original (`AlbiBooks.ipynb`)

O sistema original foi construído como um pipeline de Geração Aumentada por Recuperação (RAG) com os seguintes componentes principais:

1.  **Carregamento e Pré-processamento de Dados:**
    *   Utilizava a biblioteca `datasets` para carregar o conjunto de dados "Eitanli/goodreads".
    *   Uma subamostra de 500 livros era selecionada para processamento.
    *   As descrições dos livros eram extraídas para formar a base de conhecimento.

2.  **Processamento de Texto e Base de Conhecimento:**
    *   As descrições textuais eram convertidas em objetos `LangchainDocument`.
    *   A biblioteca `langchain.text_splitter.RecursiveCharacterTextSplitter` era empregada para dividir os documentos longos em pedaços menores (chunks), otimizando a recuperação.

3.  **Geração de Embeddings e Banco Vetorial:**
    *   Utilizava `HuggingFaceEmbeddings` com o modelo "thenlper/gte-small" para gerar embeddings vetoriais para cada chunk de texto.
    *   Um índice vetorial era criado usando `FAISS` (da biblioteca `langchain.vectorstores`), configurado com a estratégia de distância por cosseno para realizar buscas por similaridade.

4.  **Modelo de Linguagem (LLM) e Geração de Respostas:**
    *   Uma função (`load_llm_with_prompt`) era responsável por carregar diferentes LLMs open-source (ex: "HuggingFaceH4/zephyr-7b-beta", "meta-llama/Llama-2-13b-chat-hf", "distilgpt2") a partir da biblioteca `transformers`.
    *   Os modelos eram carregados com quantização de 4 bits (`BitsAndBytesConfig`) para otimizar o uso de memória.
    *   A geração de respostas seguia um fluxo RAG:
        1.  A pergunta do usuário era usada para buscar documentos relevantes no índice FAISS.
        2.  Os chunks de texto recuperados formavam o contexto.
        3.  O LLM gerava uma resposta com base nesse contexto e na pergunta original, utilizando um template de prompt formatado manualmente.

5.  **Benchmarking:**
    *   Um decorador (`measure_execution`) media o tempo de execução e o uso de memória das funções principais.
    *   Era possível ler perguntas de um arquivo JSON, processá-las através do pipeline RAG e salvar as respostas junto com as métricas de desempenho.

**Fluxo de Dados (Original):**
Dataset Goodreads -> Pré-processamento (descrições) -> Divisão em Chunks -> Geração de Embeddings (HuggingFace local) -> Criação de Índice FAISS -> Pergunta do Usuário -> Busca por Similaridade no FAISS -> Construção de Contexto -> Geração de Resposta pelo LLM Local Quantizado.

### Arquitetura do Sistema Final (`Copy_of_GeminiFlash2p5V6Stable.ipynb`)

O sistema final evoluiu significativamente, introduzindo o uso de APIs para embeddings e geração de linguagem, além de uma interface de usuário mais interativa.

1.  **Inicialização do Recuperador (Retriever):**
    *   **Mudança Estrutural:** Em vez de gerar embeddings e o índice FAISS em tempo de execução, o sistema final carrega estes componentes de arquivos pré-computados:
        *   Embeddings de documentos: `book_embeddings.npy`
        *   Metadados dos livros: `book_metadata.pkl`
        *   Índice FAISS: `book_index.faiss`
    *   Esta abordagem acelera a inicialização e reduz a carga computacional no início.

2.  **Geração de Embeddings para Consultas:**
    *   **Novo Componente:** Utiliza a API da Mistral (modelo "mistral-embed") para gerar embeddings dinamicamente para as perguntas (queries) dos usuários.
    *   Inclui lógica de retry para lidar com possíveis falhas ou limites de taxa da API.

3.  **Busca por Similaridade:**
    *   A função `search` utiliza o embedding da query (gerado pela Mistral API) para buscar no índice FAISS pré-carregado.

4.  **Formatação de Contexto e Histórico:**
    *   `format_context`: Monta uma string de contexto detalhada a partir dos metadados dos livros recuperados, incluindo informações como co-autor, idioma, assuntos, país, localização e cota.
    *   `format_history`: **Novo Componente.** Formata o histórico da conversa (últimas N interações) para ser incluído no prompt enviado ao LLM, permitindo respostas mais contextuais em diálogos.

5.  **Modelo de Linguagem (LLM) e Geração de Respostas:**
    *   **Novo Componente (API Externa):** Utiliza a API Google Generative AI com o modelo `gemini-2.5-flash-preview-05-20` para a geração de respostas.
    *   A função `generate_gemini_response` inclui lógica robusta de retry e timeout (usando `threading`) para chamadas à API Gemini.
    *   O pipeline RAG (`answer_question`):
        1.  Recebe a pergunta do usuário e o histórico da conversa.
        2.  Gera o embedding da pergunta via Mistral API.
        3.  Busca documentos relevantes no índice FAISS carregado.
        4.  Formata o contexto com os metadados dos livros e o histórico da conversa.
        5.  Constrói um prompt detalhado, instruindo o modelo Gemini a atuar como um assistente de biblioteca amigável, usar o contexto e o histórico, e ser honesto sobre limitações.
        6.  Obtém a resposta da API Gemini.
        7.  Atualiza e gerencia o histórico da conversa (limitado a `MAX_HISTORY_LENGTH` trocas).

6.  **Benchmarking:**
    *   O decorador `measure_execution` é mantido para monitorar o desempenho da função `answer_question`.

7.  **Interface com o Usuário:**
    *   `perguntar_ao_assistente`: Uma interface de console básica para interação direta.
    *   **Novo Componente (Interface Gráfica):** Utiliza a biblioteca `gradio` para criar uma interface de chat web (`chatbot_interface`), tornando a interação com o sistema mais amigável e acessível.

**Fluxo de Dados (Final):**
Carregamento de Embeddings/Metadados/Índice FAISS Pré-calculados -> Pergunta do Usuário (Console/Gradio) + Histórico da Conversa -> Geração de Embedding da Pergunta (Mistral API) -> Busca no Índice FAISS -> Formatação de Contexto (Metadados) e Histórico -> Construção de Prompt Detalhado -> Geração de Resposta (Gemini API) -> Exibição da Resposta e Atualização do Histórico.

### Mudanças Estruturais e Novos Componentes

*   **De Processamento Local para APIs Externas:**
    *   A geração de embeddings para documentos foi movida para um pré-processamento (resultados carregados do disco).
    *   A geração de embeddings para queries passou de um modelo local para a **Mistral API**.
    *   A geração de respostas passou de LLMs locais quantizados para a **Google Gemini API**.
*   **Pré-computação de Recursos:** O carregamento de embeddings e índices pré-construídos (`.npy`, `.pkl`, `.faiss`) em vez da sua criação em tempo real é uma mudança estrutural chave para performance e eficiência na inicialização.
*   **Gerenciamento de Histórico de Conversa:** A introdução do `format_history` e a sua inclusão no prompt do LLM permitem que o sistema mantenha o contexto ao longo de múltiplas interações, resultando em um diálogo mais coerente.
*   **Interface de Usuário Gráfica:** A adição da interface com `gradio` representa uma melhoria significativa na usabilidade em comparação com a interação puramente baseada em código ou console.
*   **Robustez em Chamadas de API:** Implementação de timeouts e lógicas de retry nas chamadas às APIs Mistral e Gemini para maior resiliência.
*   **Detalhes do Contexto:** O contexto fornecido ao LLM agora inclui mais metadados dos livros, potencialmente levando a respostas mais informativas.
*   **Prompt Engineering:** O prompt para o LLM Gemini é mais elaborado, especificando o papel do assistente e como ele deve utilizar as informações fornecidas.

Em resumo, a arquitetura final é mais modular, aproveita serviços de API especializados para embeddings e geração de linguagem, e foca em uma melhor experiência do usuário com histórico de conversa e interface gráfica, além de otimizar a inicialização através do carregamento de recursos pré-processados.
