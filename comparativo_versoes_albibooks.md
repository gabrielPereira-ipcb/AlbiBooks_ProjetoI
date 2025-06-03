# Análise Comparativa das Versões do Projeto AlbiBooks

## Introdução

Este documento descreve comparativamente as diferenças entre a Fase I do projeto AlbiBooks (protótipo inicial `AlbiBooks.ipynb`) e a Fase II, a versão final mais robusta e avançada (representada pelos ficheiros `Copy_of_GeminiFlash2p5V6Stable.ipynb` e `Copy_of_GrokTryIndexacao.ipynb`). O objetivo é detalhar a evolução do sistema de chatbot para bibliotecas, focando nos aspetos técnicos e nas decisões de desenvolvimento.

## 1. Arquitetura do Sistema

### 1.1. Arquitetura da Fase I (`AlbiBooks.ipynb`)
A arquitetura inicial do projeto AlbiBooks, implementada no notebook `AlbiBooks.ipynb`, configurava-se como um sistema monolítico de Retrieval Augmented Generation (RAG). A orquestração da pipeline era maioritariamente gerida pela biblioteca **Langchain**. O fluxo de dados iniciava-se com o carregamento de um subconjunto (500 registos) do dataset público `Eitanli/goodreads` através da biblioteca `datasets` da Hugging Face. As descrições textuais dos livros, campo `Description`, eram o foco principal para a extração de informação.

O processamento destes textos era realizado pelo `RecursiveCharacterTextSplitter` da Langchain, que segmentava as descrições em chunks de 512 tokens com uma sobreposição de 50 tokens, visando manter a continuidade semântica entre segmentos. Para a representação vetorial destes chunks, utilizava-se a classe `HuggingFaceEmbeddings` da Langchain, que encapsulava o modelo de embedding `thenlper/gte-small` da Hugging Face. Este modelo era configurado para normalizar os embeddings resultantes (`normalize_embeddings=True`) e suportava processamento em GPU, caso disponível.

Os embeddings gerados eram então indexados localmente utilizando uma implementação FAISS (Facebook AI Similarity Search) disponibilizada como um wrapper pela Langchain (`langchain.vectorstores.FAISS`). Este índice vetorial permitia a busca eficiente de chunks relevantes baseada na similaridade de cosseno (`DistanceStrategy.COSINE`).

A componente de geração de linguagem natural (LLM) era implementada através da biblioteca `transformers` da Hugging Face. Esta permitia o carregamento de diversos modelos de linguagem open-source, como "HuggingFaceH4/zephyr-7b-beta", "meta-llama/Llama-2-13b-chat-hf" e "distilgpt2". Para otimizar o uso de recursos computacionais, especialmente memória, os modelos eram carregados com quantização em 4-bits. Esta técnica era ativada através da configuração `BitsAndBytesConfig` da biblioteca `transformers`, especificando `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`, `bnb_4bit_use_double_quant=True`, e `bnb_4bit_compute_dtype=torch.bfloat16`.

O fluxo RAG completo consistia em:
1.  Receção de uma pergunta do utilizador (programaticamente, via célula de código).
2.  Geração do embedding da pergunta utilizando o mesmo modelo `thenlper/gte-small`.
3.  Busca de similaridade no índice FAISS para recuperar os `k` chunks de texto mais relevantes.
4.  Construção de um prompt formatado, que combinava o contexto dos documentos recuperados (conteúdo dos chunks) com a pergunta original.
5.  Submissão deste prompt ao LLM selecionado (e.g., Zephyr 7B quantizado) para gerar a resposta.
A interação com o sistema era exclusivamente programática dentro do Jupyter Notebook, sem interface gráfica. Todo o processo, desde a indexação (que era refeita a cada execução completa do notebook, a menos que explicitamente evitada) até à conversação, ocorria no mesmo ambiente de execução.

### 1.2. Arquitetura da Fase II (`Copy_of_GeminiFlash2p5V6Stable.ipynb` e `Copy_of_GrokTryIndexacao.ipynb`)
A Fase II do projeto AlbiBooks reconfigurou a arquitetura para um modelo mais modular e robusto, separando explicitamente o processo de indexação da componente conversacional e adotando modelos de IA acedidos por API.

**Componente de Indexação (`Copy_of_GrokTryIndexacao.ipynb`):**
Este notebook é dedicado exclusivamente à criação e persistência dos artefactos de indexação.
1.  **Carregamento de Dados:** Os dados são lidos de um ficheiro JSON local, `biblioteca_dados_combinado.json`, contendo mais de 18.000 registos de livros específicos do catálogo de uma biblioteca.
2.  **Formatação de Texto para Embedding:** Para cada livro, a função `format_book_text` cria uma cadeia de texto consolidada, agregando múltiplos campos de metadados: `title`, `authors`, `coauthor` (se presente), `language_code`, `country`, `itype` (tipo de item), `subjects_normalized_short_display` (assuntos), `shelvingloc` (localização física) e `call_no` (cota). Esta abordagem visa criar uma representação semântica mais rica e holística do livro.
3.  **Geração de Embeddings (API Mistral):** Os embeddings para estes textos formatados são gerados utilizando o modelo `mistral-embed` através da API da Mistral AI. As chamadas à API são feitas para o endpoint `https://api.mistral.ai/v1/embeddings`, enviando o texto num payload JSON (`{"model": "mistral-embed", "input": [text_content]}`). O código implementa gestão de _rate limiting_ e _exponential backoff_ para lidar com possíveis sobrecargas ou limites da API. A dimensão dos embeddings é de 1024.
4.  **Construção e Persistência do Índice:**
    *   Os embeddings gerados são agregados num array NumPy e guardados como `book_embeddings.npy`.
    *   Os metadados correspondentes a cada livro (incluindo o texto original formatado) são guardados numa lista de dicionários, que é depois serializada usando `pickle` para o ficheiro `book_metadata.pkl`.
    *   Um índice FAISS do tipo `IndexFlatL2` (que utiliza distância Euclidiana L2 para similaridade) é construído sobre os embeddings e persistido como `book_index.faiss`.
    *   Estes três ficheiros (`.npy`, `.pkl`, `.faiss`) são guardados no Google Drive do utilizador, garantindo a sua persistência entre sessões e facilitando o seu carregamento pelo componente conversacional.

**Componente Conversacional (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):**
Este notebook constitui o chatbot interativo.
1.  **Carregamento do Índice:** No início, o sistema carrega os artefactos de indexação (`book_embeddings.npy`, `book_metadata.pkl`, `book_index.faiss`) a partir do Google Drive.
2.  **Fluxo de Recuperação e Geração:**
    *   **Embedding da Pergunta (API Mistral):** Perante uma pergunta do utilizador (submetida via interface Gradio ou consola), o sistema gera primeiro o embedding da pergunta utilizando a mesma API `mistral-embed` e o mesmo endpoint que na fase de indexação.
    *   **Busca FAISS:** O embedding da pergunta é usado para consultar o índice FAISS local (`index.search()`), recuperando os `TOP_K` (configurável, e.g., 5) livros mais relevantes com base na distância L2.
    *   **Formatação do Contexto:** Os metadados dos livros recuperados são extraídos do ficheiro `book_metadata.pkl`. A função `format_context` constrói então uma descrição textual estruturada e detalhada para cada livro, que servirá de contexto para o LLM.
    *   **Geração da Resposta (API Gemini):** Este contexto, juntamente com a pergunta original e o histórico de conversação (se existente), é utilizado para construir um prompt. Este prompt é submetido ao modelo `gemini-1.5-flash-latest` (anteriormente `gemini-2.5-flash-preview-05-20`) da Google através da sua API (`genai.GenerativeModel(model_name)`). A interação com a API Gemini inclui mecanismos de _retry_ e _timeout_ para aumentar a robustez.
3.  **Interface com o Utilizador:** A interação é facilitada por uma interface gráfica desenvolvida com a biblioteca Gradio (`gr.ChatInterface`), que permite um diálogo mais natural e a recolha de feedback.

### 1.3. Principais Mudanças Estruturais e Componentes Novos
A evolução da Fase I para a Fase II reflete uma maturação significativa da arquitetura, com implicações práticas relevantes:
*   **Separação da Indexação:** A criação de um processo de indexação offline e independente do chatbot (`Copy_of_GrokTryIndexacao.ipynb`) é uma das mudanças mais impactantes.
    *   **Implicações:** Melhora a modularidade, permitindo que a indexação (que pode ser demorada e consumir muitos recursos, especialmente com mais de 18.000 documentos) seja executada separadamente, sem afetar o tempo de arranque ou a performance do chatbot. Facilita a manutenção, pois cada componente pode ser atualizado independentemente. Permite que os artefactos de indexação (embeddings, índice FAISS) sejam versionados e reutilizados, e potencialmente partilhados por múltiplas instâncias do chatbot ou outras aplicações.
*   **Novos Modelos de IA (Baseados em API):** Transição completa de modelos de embedding e LLM locais/open-source para serviços de API (`mistral-embed` para embeddings e `gemini-1.5-flash-latest` para geração de respostas).
    *   **Implicações:** Acesso a modelos potencialmente mais poderosos e atualizados sem a necessidade de gerir hardware ou software complexo localmente. Reduz a carga computacional no ambiente de execução do chatbot. Introduz dependências de rede e custos associados ao uso das APIs, mitigados por mecanismos de robustez (retry, backoff).
*   **Abandono do Langchain:** A pipeline RAG é implementada diretamente em Python.
    *   **Implicações:** Oferece maior controlo granular sobre cada etapa do processo RAG, desde a formatação dos dados para embedding até à construção do prompt para o LLM. Pode simplificar a integração com APIs específicas que podem não ter wrappers Langchain otimizados ou que requerem configurações particulares. Aumenta a transparência do fluxo de dados, o que pode ser benéfico para depuração e otimizações. No entanto, exige a implementação manual de lógicas que o Langchain abstrai.
*   **Interface Gráfica com Gradio:** Introdução de uma UI interativa (`gr.ChatInterface`).
    *   **Implicações:** Melhora drasticamente a experiência do utilizador final e a facilidade de teste e demonstração do sistema. Permite interações mais naturais e a recolha de feedback qualitativo (e.g., _flagging_ de respostas).
*   **Gestão de Histórico de Conversação:** Implementação de um sistema para manter o contexto ao longo de múltiplas trocas na conversação.
    *   **Implicações:** Permite conversas mais coerentes e contextuais, onde o chatbot pode responder a perguntas de seguimento e referenciar informações de turnos anteriores, tornando a interação mais natural.
*   **Persistência do Índice no Google Drive:** O índice FAISS, embeddings NumPy e metadados Pickle são guardados e carregados do Google Drive.
    *   **Implicações:** Garante a persistência dos dados de indexação entre sessões de execução dos notebooks Colab, evitando a necessidade de re-indexar a cada vez. Facilita o fluxo de trabalho entre os dois notebooks (indexação e conversação).
*   **Fonte de Dados Específica:** Mudança de um dataset genérico do Goodreads para um ficheiro JSON representativo do catálogo da biblioteca.
    *   **Implicações:** Aumenta substancialmente a relevância e utilidade do chatbot para o seu propósito específico de assistente de biblioteca.
*   **Mecanismos de Robustez para APIs:** Implementação de lógicas de _retry_, _backoff_ e _timeout_.
    *   **Implicações:** Aumenta a fiabilidade do sistema ao lidar com a natureza potencialmente instável de serviços de rede externos, melhorando a resiliência a falhas temporárias ou limites de taxa das APIs.

## 2. Estratégias de Recuperação de Informação e Embeddings

A capacidade de um sistema RAG em fornecer respostas relevantes depende criticamente da qualidade dos seus embeddings e da eficácia da sua estratégia de recuperação. Entre a Fase I e a Fase II do projeto AlbiBooks, ocorreram alterações significativas nestes dois domínios, refletindo uma maturação na abordagem à representação e recuperação de conhecimento.

### 2.1. Modelos de Embedding

*   **Fase I (`AlbiBooks.ipynb`):** O sistema utilizava a biblioteca `HuggingFaceEmbeddings` da Langchain para gerar representações vetoriais a partir de modelos da Hugging Face. O modelo de embedding especificado era o `thenlper/gte-small`. Este é um modelo de transformador projetado para ser eficiente ("small") e de propósito geral ("general text embedder" - gte), produzindo embeddings com uma **dimensão de 384**. A configuração incluía a normalização explícita dos embeddings (`normalize_embeddings: True`). Esta normalização é crucial quando se utiliza a similaridade de cosseno, pois garante que a métrica se concentra apenas na orientação dos vetores, desconsiderando as suas magnitudes. O processamento podia ser realizado em GPU, se disponível.

*   **Fase II (`Copy_of_GeminiFlash2p5V6Stable.ipynb` e `Copy_of_GrokTryIndexacao.ipynb`):** Optou-se por uma mudança para o modelo `mistral-embed`, acedido através da API da Mistral AI. Este modelo produz embeddings com uma **dimensão de 1024**, significativamente maior que o `gte-small`, sugerindo uma capacidade potencialmente superior para capturar nuances semânticas mais complexas. A utilização de um modelo via API implica que a infraestrutura e a manutenção do modelo de embedding são geridas pelo fornecedor (Mistral AI), garantindo acesso a arquiteturas possivelmente mais avançadas e atualizadas sem a sobrecarga de gestão local. Contudo, introduz a necessidade de gerir chamadas de rede, incluindo latência, limites de taxa (endereçados com _retry_ e _backoff_) e custos associados. No código da Fase II, a normalização dos embeddings não é explicitamente controlada no cliente; assume-se que a API da Mistral pode ou não devolver vetores normalizados. Se os vetores não forem normalizados e se utilizar `IndexFlatL2` no FAISS (que calcula a distância Euclidiana), a ordenação dos resultados pode diferir daquela obtida com a similaridade de cosseno, pois a magnitude dos vetores influenciará a distância.

A transição para `mistral-embed` e a sua maior dimensão vetorial indicam uma procura por uma representação semântica mais rica, o que pode ser particularmente benéfico para os metadados mais estruturados e variados dos livros na Fase II. A questão da normalização torna-se importante: se os embeddings da Mistral não forem normalizados e se desejar uma métrica pura de orientação (como o cosseno), seria necessário normalizar os vetores antes da indexação ou no momento da busca, ou utilizar um índice FAISS que incorpore a similaridade de cosseno (e.g., `IndexFlatIP` após normalização).

### 2.2. Estratégias de Recuperação de Informação

Ambas as fases utilizam o FAISS para a criação e consulta de índices vetoriais, mas a unidade de informação indexada e a métrica de similaridade subjacente diferem substancialmente.

*   **Fase I:** Os documentos de origem (descrições de livros do dataset Goodreads) eram processados pelo `RecursiveCharacterTextSplitter` da Langchain. Este componente foi configurado com uma `chunk_size` de 512 tokens e uma `chunk_overlap` de 50 tokens, utilizando separadores comuns em Markdown (e.g., `\n\n`, `\n`, ` `) para tentar preservar a estrutura do texto original ao dividir as descrições em segmentos menores. Um embedding era gerado para cada um destes chunks. O índice FAISS era então construído sobre estes embeddings de chunks, utilizando a `DistanceStrategy.COSINE` para calcular a similaridade. A recuperação consistia em encontrar os chunks individuais cujas descrições fossem semanticamente mais próximas da pergunta do utilizador.

*   **Fase II:** A abordagem à unidade de informação mudou radicalmente, abandonando o _chunking_ de descrições. Em vez disso, cada livro do catálogo (`biblioteca_dados_combinado.json`) é representado por um único embedding. Este embedding é gerado a partir de um texto consolidado, criado pela função `format_book_text`, que agrega múltiplos campos de metadados do livro: título, autor(es), idioma, país, tipo de item, assuntos, localização e cota. O índice FAISS utilizado é o `IndexFlatL2`, que armazena os vetores completos e, durante a busca, calcula a distância Euclidiana (L2) para encontrar os livros mais próximos do embedding da pergunta. A pontuação de relevância (`relevance_score`) é então calculada como `1.0 / (1.0 + dist)`, onde `dist` é a distância L2. Esta transformação visa criar uma medida de "proximidade" que diminui à medida que a distância L2 aumenta.
    *   **Vantagens de embedar metadados consolidados:** Pode capturar uma representação mais holística do livro, permitindo buscas baseadas numa combinação de atributos e não apenas na descrição. Potencialmente mais eficaz para perguntas que visam múltiplos aspetos (e.g., "livros de ficção científica em inglês na prateleira X").
    *   **Desvantagens:** Se um campo específico for muito longo ou ruidoso, pode dominar o embedding. A ausência de _chunking_ pode ser problemática se alguns campos de metadados forem extremamente extensos e excederem o limite de tokens do modelo de embedding, embora para os metadados típicos de um catálogo de biblioteca, isso seja menos provável do que para descrições narrativas longas.

A mudança para embeddings de livros completos e a utilização da distância L2 (com a subsequente transformação em `relevance_score`) representam uma tentativa de alinhar a recuperação com a natureza multifacetada dos dados bibliográficos.

### 2.3. Seleção e Apresentação de Documentos ao LLM

A forma como os documentos recuperados são processados e formatados como contexto para o modelo de linguagem é crucial para a qualidade da resposta final.

*   **Fase I:** Após a recuperação dos chunks mais relevantes pelo FAISS, o contexto para o LLM era construído através da simples concatenação do campo `page_content` (o texto original do chunk) de cada um dos `num_docs_final` (configurável, e.g., 3-5) chunks recuperados. Esta abordagem, embora direta, fornecia ao LLM um bloco de texto relativamente não estruturado, composto por fragmentos de descrições.

*   **Fase II:** O processo é mais elaborado. Após a busca no FAISS com `index.search(query_embedding, top_k)`, que retorna os índices e distâncias dos `top_k` livros mais próximos, o sistema utiliza esses índices para extrair os metadados completos de cada livro a partir da lista `book_metadata` (carregada do ficheiro `.pkl`). A função `format_context` é então responsável por construir uma descrição textual estruturada e detalhada para cada um destes `top_k` livros. Esta formatação explícita campos como título, autor, idioma, localização, cota, assuntos, etc., de forma clara e organizada.
    *   **Impacto no LLM:** A apresentação de um contexto estruturado e rico em metadados na Fase II é significativamente mais informativa para o LLM do que a simples concatenação de chunks da Fase I. O LLM recebe informação organizada, facilitando a extração de detalhes específicos (como a cota ou localização, que eram o objetivo primário) e a síntese de respostas mais precisas e detalhadas.
    *   **Quantidade de Contexto:** Enquanto `num_docs_final` na Fase I controlava o número de chunks, `top_k` na Fase II controla o número de livros completos cujos metadados são formatados para o contexto. Dada a maior densidade informacional dos metadados consolidados por livro em comparação com chunks de descrição, a qualidade do contexto por unidade (livro vs. chunk) é superior na Fase II, mesmo que o número de unidades seja semelhante.

Esta evolução na construção do contexto visa fornecer ao LLM informação mais direcionada e diretamente utilizável, alinhada com as tarefas de um assistente de biblioteca, como fornecer a localização e cota de um livro.

## 3. Melhorias no Desempenho

A avaliação do desempenho de um sistema conversacional abrange diversas dimensões, incluindo tempo de resposta, gestão de tokens e a qualidade percebida das respostas. A transição da Fase I para a Fase II visou melhorias em todas estas frentes.

### 3.1. Tempo de Resposta

*   **Fase I (`AlbiBooks.ipynb`):** O tempo de resposta era influenciado por múltiplos fatores locais. O decorador `@measure_execution` registava tempos totais para a pipeline RAG (função `answer_with_rag`) entre 15 a 93 segundos. Os principais componentes deste tempo eram:
    1.  **Carregamento do Modelo de Embedding:** Se não pré-carregado, o modelo `thenlper/gte-small` necessitava de ser carregado para a memória.
    2.  **Inferência do Embedding da Pergunta:** Geração do vetor da pergunta pelo modelo local.
    3.  **Busca FAISS:** Consulta ao índice FAISS local, geralmente rápida para o volume de dados (500 chunks).
    4.  **Inferência do LLM Local:** Este era o principal gargalo. Modelos como "HuggingFaceH4/zephyr-7b-beta", mesmo quantizados, são computacionalmente intensivos, e a sua execução em CPU ou GPU limitada resultava em latências elevadas.
    A criação inicial do índice FAISS (processamento e embedding dos 500 documentos) também representava um custo de tempo significativo no arranque do notebook, embora não diretamente no tempo de resposta por pergunta subsequente, assumindo que o índice já estava construído.

*   **Fase II (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):** Os tempos de resposta, medidos pela mesma função `answer_question` e observados na interface Gradio, situaram-se entre 2.25 a 10.37 segundos. Os componentes do tempo de resposta são:
    1.  **Chamada à API Mistral (Embedding da Pergunta):** Inclui a latência de rede para enviar a pergunta e receber o seu embedding. A eficiência da API Mistral é crucial aqui.
    2.  **Busca FAISS Local:** Consulta ao índice FAISS carregado localmente (`book_index.faiss`), que é muito rápida para os cerca de 18.000 vetores.
    3.  **Chamada à API Gemini (Geração da Resposta):** Inclui a latência de rede para enviar o prompt (pergunta + contexto + histórico) e receber a resposta gerada. A performance da API Gemini é determinante.
    A **separação da indexação** para um processo offline na Fase II significa que o "arranque a frio" do chatbot é muito mais rápido, pois apenas carrega os artefactos pré-computados (índice FAISS, embeddings, metadados), eliminando o tempo de processamento inicial dos documentos. A variabilidade da latência de rede é um novo fator, mas a descarga do processamento intensivo (embeddings e LLM) para APIs otimizadas parece compensar, resultando em tempos de resposta geralmente inferiores e mais consistentes. A implementação de um **`timeout` de 30 segundos para a API Gemini** (com 3 tentativas) na função `get_gemini_response` assegura que o sistema não fica indefinidamente à espera, melhorando a experiência do utilizador perante problemas de rede ou sobrecarga da API.

### 3.2. Número de Tokens

A gestão eficiente do número de tokens é vital, tanto pelos custos associados às APIs como pelos limites de contexto dos LLMs.

*   **Fase I:**
    *   **Contexto para o LLM:** Determinado pelo `chunk_size` (512 tokens) e `num_docs_final` (e.g., 3-5 chunks), levando a um contexto de entrada para o LLM na ordem de 1500-2500 tokens, mais a pergunta.
    *   **Limites dos LLMs Locais:** Modelos como Zephyr 7B têm limites de contexto típicos (e.g., 4k ou 8k tokens). Embora o contexto enviado estivesse dentro destes limites, a capacidade de LLMs mais pequenos de utilizar eficazmente contextos longos pode ser limitada.
    *   **Resposta do LLM:** Limitada a `max_new_tokens=500`, controlando o tamanho da saída.
    *   **Densidade Informacional:** Chunks de descrição podem ter densidade informacional variável.

*   **Fase II:**
    *   **Contexto para o LLM (Gemini):** O modelo `gemini-1.5-flash-latest` suporta um contexto consideravelmente maior (até 1M de tokens na sua versão completa, embora o limite efetivo via API possa ser diferente e configurável). O prompt enviado ao Gemini é construído a partir de:
        *   Metadados detalhados e formatados dos `top_k` livros recuperados (função `format_context`).
        *   Histórico da conversa (até `MAX_HISTORY_LENGTH=10` trocas, formatado por `format_history`).
        *   A pergunta atual do utilizador.
        Esta abordagem pode resultar num número de tokens de entrada potencialmente elevado, especialmente com um histórico de conversa longo e `top_k` elevado.
    *   **Densidade Informacional:** A formatação explícita de metadados (título, autor, cota, localização) visa uma alta densidade de informação relevante por token.
    *   **Trade-off Contexto vs. Qualidade:** Um contexto mais rico (mais metadados, histórico mais longo) fornece mais informação ao LLM, potencialmente melhorando a qualidade e a contextualização da resposta. No entanto, aumenta o número de tokens, o que pode impactar a latência da API e os custos.
    *   **Resposta do LLM (Gemini):** Não há uma limitação explícita de `max_new_tokens` na chamada à API Gemini no código fornecido. Isto significa que a API utilizará o seu limite padrão ou um limite configurado na plataforma Google AI Studio, o que pode permitir respostas mais longas e detalhadas, se necessário, mas também requer monitorização para evitar verbosidade excessiva ou custos inesperados.

### 3.3. Precisão das Respostas

A precisão das respostas é avaliada qualitativamente, considerando a relevância, correção e utilidade da informação fornecida.

*   **Fase I:**
    *   A precisão dependia da qualidade dos embeddings do `thenlper/gte-small` para recuperar chunks relevantes e da capacidade do LLM local (e.g., Zephyr 7B) de sintetizar uma resposta a partir desses fragmentos de texto. LLMs mais pequenos podem ter dificuldade em raciocinar sobre contextos longos compostos por múltiplos chunks desconexos ou em extrair informações muito específicas se estas não estiverem proeminentes.
    *   A utilização de dados genéricos do Goodreads limitava a relevância das respostas para um contexto bibliotecário específico (e.g., não havia informação de cota ou localização física).

*   **Fase II:** Espera-se uma melhoria substancial na precisão devido a múltiplos fatores:
    *   **Embeddings de Maior Qualidade:** O `mistral-embed` (dimensão 1024) é um modelo mais recente e com maior capacidade, o que deve levar a uma recuperação de documentos (livros) mais relevante e precisa do índice FAISS.
    *   **Contexto Mais Rico e Estruturado:** Fornecer ao Gemini metadados detalhados e bem formatados (incluindo título, autor, idioma, cota, localização, assuntos) permite ao LLM aceder diretamente à informação necessária para responder a perguntas típicas de biblioteca. Isto é superior a fornecer apenas excertos de descrições.
    *   **LLM Mais Avançado (Gemini):** O `gemini-1.5-flash-latest` possui capacidades de compreensão, raciocínio e seguimento de instruções significativamente superiores aos modelos open-source mais pequenos usados na Fase I. Consegue lidar melhor com contextos mais longos e informação estruturada.
    *   **Gestão de Histórico:** A inclusão do histórico da conversa permite respostas contextualmente mais adequadas e a resolução de ambiguidades, melhorando a percepção de precisão e inteligência do sistema.
    *   **Prompt Engineering Específico:** As instruções no prompt do Gemini ("Você é um assistente de biblioteca amigável.", "Se não houver informação suficiente, seja honesto...", "Sempre refira a localização do livro...") guiam o LLM a fornecer respostas mais úteis, alinhadas com as expectativas de um assistente de biblioteca, e a admitir limitações, o que também é uma forma de precisão (evitar alucinações).
    *   **Dados Específicos da Biblioteca:** A mudança para o `biblioteca_dados_combinado.json` garante que as respostas se baseiam no acervo real da biblioteca, tornando-as factualmente relevantes para o utilizador final. A capacidade de fornecer cotas e localizações exatas é um ganho de precisão fundamental.

As métricas de desempenho (tempo e memória) são consistentemente recolhidas em ambas as fases utilizando o decorador `@measure_execution`. A Fase II demonstra uma otimização significativa no uso de memória para a função principal de resposta (e.g., 0.06-0.09 MB na Fase II vs. 0.11-0.42 MB na Fase I), principalmente devido à descarga da computação do LLM e dos embeddings para APIs externas, restando localmente apenas a gestão do fluxo, a busca FAISS e a interação com as APIs.

## 4. Alterações nos Dados

A natureza e o tratamento dos dados subjacentes a um sistema RAG são determinantes para a sua eficácia. O projeto AlbiBooks evoluiu significativamente neste aspeto entre as suas duas fases, desde a fonte e volume até à estratégia de preparação para a geração de embeddings.

### 4.1. Fonte, Volume e Qualidade dos Dados

*   **Fase I (`AlbiBooks.ipynb`):**
    *   **Fonte:** Utilizava o dataset `Eitanli/goodreads`, carregado da plataforma Hugging Face Datasets. Este dataset é público e genérico, contendo informações sobre uma vasta gama de livros. Inclui campos como `Book_ID`, `Title`, `Author`, `Avg_Rating` (avaliação média), `Num_Ratings` (número de avaliações), `Description` e `URL` (para a página do livro no Goodreads). Embora rico em alguns aspetos (como avaliações e popularidade), o campo `Description` era o principal foco para a geração de embeddings. Outros campos como `Avg_Rating` ou `Num_Ratings` poderiam teoricamente ter sido usados para filtrar ou enriquecer os dados, mas a implementação focou-se no conteúdo textual da descrição.
    *   **Volume:** Para fins de demonstração, o volume de dados foi limitado a 500 registos. Este volume reduzido, embora facilitasse a prototipagem rápida, oferecia uma cobertura muito limitada para um sistema de perguntas e respostas generalista.
    *   **Qualidade:** A qualidade era a do dataset original. As descrições podiam variar grandemente em extensão, detalhe e estilo. A generalidade dos dados e a ausência de informações específicas de um catálogo bibliotecário (como cota ou localização física) limitavam a aplicabilidade do chatbot a um contexto de biblioteca real.

*   **Fase II (`Copy_of_GrokTryIndexacao.ipynb`):**
    *   **Fonte:** Os dados passaram a ser carregados de um ficheiro JSON local, `biblioteca_dados_combinado.json`. Este ficheiro parece ser uma exportação ou _scraping_ do catálogo de uma biblioteca específica, contendo campos cruciais para um assistente de biblioteca, tais como: `id` (identificador único), `title`, `authors`, `co-author`, `language_code`, `country` (país de publicação), `itype` (tipo de item, e.g., "Livro", "Periódico"), `subjects_normalized_short_display` (lista de assuntos), `shelvingloc` (localização física na biblioteca) e `call_no` (cota do livro).
    *   **Volume:** O volume aumentou drasticamente para 18.266 livros. Este aumento é fundamental, pois expande significativamente a cobertura do catálogo da biblioteca, aumentando a probabilidade de o sistema encontrar informação relevante para as consultas dos utilizadores.
    *   **Qualidade:** A "qualidade dos dados" no contexto de metadados de uma biblioteca refere-se à sua **completude** (todos os campos relevantes estão preenchidos?), **precisão** (a informação está correta, e.g., a cota corresponde ao livro?) e **consistência** (o mesmo tipo de informação é representado da mesma forma em todos os registos?). A mudança para `biblioteca_dados_combinado.json` representa um aumento na relevância e especificidade dos dados. A qualidade intrínseca destes dados (precisão, completude) depende do processo de curadoria original da biblioteca e da forma como foram extraídos para o JSON. No entanto, a presença de campos como `shelvingloc` e `call_no` é, por si só, um enorme salto qualitativo para o propósito do chatbot.

A transição para dados específicos da biblioteca e o aumento do volume são passos cruciais na criação de um chatbot verdadeiramente útil, capaz de responder a perguntas sobre o acervo específico de uma instituição.

### 4.2. Estratégia de Chunking e Formatação para Embedding

*   **Fase I:** Adotou uma estratégia de _chunking_ explícita das descrições dos livros.
    *   O `RecursiveCharacterTextSplitter` da Langchain foi utilizado com `chunk_size=512` tokens e `chunk_overlap=50` tokens. Este _splitter_ tenta dividir o texto recursivamente usando uma lista predefinida de separadores (`MARKDOWN_SEPARATORS = ["\n\n", "\n", " ", ""]`), começando pelos que indicam maiores quebras estruturais (parágrafos) e progredindo para separadores mais finos. O objetivo é manter, tanto quanto possível, sentenças e parágrafos coesos dentro de cada chunk.
    *   **Desvantagens do Chunking:** Apesar da tentativa de preservar a semântica, o chunking pode levar à perda do contexto global do documento original, pois cada chunk é embedado isoladamente. Informações que se complementam através de diferentes secções da descrição podem ser separadas, e a relevância de um chunk individual pode ser difícil de avaliar sem o seu contexto mais amplo.

*   **Fase II:** A abordagem mudou radicalmente, abandonando o chunking em favor da criação de um **documento único e consolidado por livro** para embedding.
    *   A função `format_book_text` é responsável por esta consolidação. Por exemplo, um livro poderia ser formatado como:
        ```
        Título: O Nome do Vento
        Autor(es): Patrick Rothfuss
        Idioma: por
        País: USA
        Tipo de Item: Livro
        Assuntos: Fantasia, Aventura
        Localização: Piso 2, Secção B
        Cota: LIT RO P NOME
        ```
        Esta cadeia de texto formatada é então usada para gerar um único embedding para o livro.
    *   **Trade-offs:**
        *   **Vantagens:** Captura uma semântica mais global do item, integrando todos os seus metadados relevantes numa única representação vetorial. Pode ser mais eficaz para consultas que combinam múltiplos atributos.
        *   **Desvantagens:** Se alguns campos forem excessivamente longos ou contiverem informação "ruidosa" (pouco relevante ou mal formatada), podem influenciar desproporcionalmente o embedding. No entanto, para metadados de biblioteca, que tendem a ser relativamente concisos e estruturados, este risco é menor do que com descrições narrativas longas.
    Esta estratégia contrasta fortemente com a da Fase I, pois foca-se na representação holística do item bibliográfico em vez de fragmentos da sua descrição.

### 4.3. Normalização de Dados

A normalização de dados, tanto textuais como vetoriais, pode influenciar a performance de sistemas de recuperação.

*   **Normalização Textual:**
    *   Em ambas as fases, não foram aplicados passos explícitos de normalização textual robusta, como conversão para minúsculas, remoção sistemática de pontuação, _stemming_ (redução de palavras ao seu radical) ou _lematização_ (redução à forma canónica). A função `format_book_text` da Fase II concatena os valores dos campos como estão.
    *   **Justificativa Potencial:** Modelos de embedding modernos, especialmente os baseados em transformadores, são frequentemente treinados em grandes volumes de texto não normalizado e podem ser capazes de lidar com variações de capitalização e formas flexionadas. A normalização agressiva poderia, em alguns casos, remover nuances importantes. No entanto, a ausência de normalização pode levar a que termos idênticos com capitalização diferente (e.g., "Lisboa" vs "lisboa") sejam tratados de forma distinta, embora a magnitude deste efeito varie com o modelo.

*   **Normalização Vetorial:**
    *   **Fase I:** A configuração `HuggingFaceEmbeddings(normalize_embeddings=True)` garantia que os vetores de embedding do `thenlper/gte-small` eram normalizados para terem comprimento unitário (L2-norm igual a 1). Isto é essencial quando se utiliza a **similaridade de cosseno** (`DistanceStrategy.COSINE` no FAISS), pois esta métrica mede o cosseno do ângulo entre dois vetores, e é mais significativa quando os vetores estão na superfície de uma hiperesfera unitária.
    *   **Fase II:** A normalização dos embeddings gerados pela API `mistral-embed` não é explicitamente controlada no código cliente. Se a API não devolver vetores normalizados, o uso de `IndexFlatL2` no FAISS (que calcula a distância Euclidiana) significa que tanto a orientação como a magnitude dos vetores influenciam a busca. Vetores com menor magnitude intrínseca podem parecer artificialmente "mais próximos" de outros vetores, mesmo que a sua orientação semântica não seja a ideal. A função `relevance_score = 1.0 / (1.0 + dist)` tenta converter a distância L2 numa pontuação de similaridade, mas não substitui a normalização vetorial se a intenção for medir a pura similaridade de orientação. Idealmente, para usar L2 como substituto da similaridade de cosseno, os vetores deveriam ser normalizados antes da indexação.

A escolha de normalizar (ou não) os dados textuais e os vetores de embedding tem implicações diretas na forma como a similaridade é calculada e, consequentemente, na qualidade dos resultados da recuperação.

## 5. Implementação de Métricas e Testes

A avaliação contínua e a monitorização do desempenho são aspetos cruciais no desenvolvimento de sistemas de IA. O projeto AlbiBooks incorporou diferentes abordagens para métricas e testes ao longo da sua evolução, focando-se no desempenho técnico e na qualidade funcional.

### 5.1. Recolha de Métricas de Desempenho

Ambas as fases do projeto demonstraram uma preocupação com o desempenho técnico, implementando mecanismos para medir o tempo de execução e o consumo de memória das operações críticas.

*   O decorador Python `@measure_execution` foi consistentemente utilizado. Este decorador utiliza:
    *   `time.time()` para registar o tempo de início e fim da execução da função decorada, calculando a diferença para obter o `execution_time` em segundos.
    *   A biblioteca `tracemalloc` para monitorizar a alocação de memória. `tracemalloc.start()` é chamado antes da execução da função, e `tracemalloc.get_traced_memory()` é usado para obter o uso de memória atual (`memory_used`) e o pico de uso (`memory_peak`) durante a execução da função. `tracemalloc.stop()` é chamado no final. As unidades são convertidas para megabytes (MB).
    A importância destas métricas reside na capacidade de identificar gargalos de desempenho (quer em componentes locais como a inferência de LLMs na Fase I, quer em chamadas a APIs externas na Fase II) e otimizar o consumo de recursos, o que é vital tanto para a eficiência do sistema como para a gestão de custos em ambientes de produção.

*   **Fase I (`AlbiBooks.ipynb`):** O decorador `@measure_execution` envolvia a função principal de resposta com RAG (`answer_with_rag`). As métricas de tempo e memória eram impressas na consola após cada chamada. Crucialmente, ao utilizar a função `questions_from_file` para o benchmarking de LLMs, estas métricas eram também **guardadas num ficheiro `answers.json`**, juntamente com a pergunta, a resposta gerada e o contexto recuperado. Isto permitia uma análise comparativa e agregada do desempenho de diferentes modelos de LLM sob as mesmas condições de teste, facilitando uma avaliação mais objetiva das suas características de performance.

*   **Fase II (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):** A mesma abordagem com o decorador `@measure_execution` foi mantida, aplicando-se à função `answer_question` (que lida com a lógica RAG, incluindo chamadas às APIs Mistral e Gemini). As métricas (`execution_time`, `memory_used`, `memory_peak`) são recolhidas e impressas na consola do servidor a cada interação na interface Gradio. Isto fornece feedback em tempo real sobre o custo computacional de cada resposta. Contudo, ao contrário da Fase I, **não há uma persistência automática destas métricas num ficheiro estruturado** quando se utiliza a interface Gradio. Esta ausência pode dificultar análises de desempenho longitudinais ou comparativas mais sistemáticas, a menos que os dados da consola sejam registados manualmente ou através de ferramentas de logging adicionais.

Esta recolha consistente de métricas de desempenho técnico, embora com diferentes níveis de persistência, permite aferir o impacto das alterações arquiteturais e otimizar os recursos computacionais.

### 5.2. Testes e Avaliação da Qualidade

As estratégias para testar a funcionalidade e avaliar a qualidade das respostas evoluíram do foco em benchmarking de modelos para uma abordagem mais interativa e qualitativa.

*   **Fase I (`AlbiBooks.ipynb`):**
    *   **Benchmarking de LLMs:** O notebook implementava um sistema de benchmarking para comparar diferentes LLMs open-source. Um conjunto de perguntas predefinidas era lido de um ficheiro `questions.json`.
    *   **Reprodutibilidade e Comparabilidade:** A utilização de um conjunto fixo de perguntas (`questions.json`) é valiosa pois garante a **reprodutibilidade** dos testes e a **comparabilidade** direta das respostas e do desempenho (métricas do `@measure_execution`) entre diferentes modelos ou configurações.
    *   **Análise Manual de Saídas:** As respostas geradas, o contexto e as métricas eram guardados em `answers.json`. A avaliação da qualidade das respostas era, no entanto, um processo **manual e subjetivo**, dependendo da inspeção humana deste ficheiro. Esta abordagem, embora informativa, é morosa e pode variar entre avaliadores. Não foram implementadas métricas automáticas de avaliação da qualidade textual (e.g., ROUGE, BLEU, METEOR).

*   **Fase II (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):**
    *   **Testes Interativos via Gradio:** A introdução da interface Gradio alterou a dinâmica de teste para uma abordagem mais **interativa e exploratória**. Isto permite aos programadores e testadores dialogar com o chatbot em tempo real, descobrindo casos de falha não antecipados e avaliando a usabilidade e naturalidade da conversa de forma mais holística.
    *   **Feedback Manual (_Flagging_):** A interface Gradio foi configurada com `flagging_mode="manual"`, permitindo aos utilizadores marcar respostas com categorias como "Like", "Spam", "Inappropriate", ou "Other". Este mecanismo de feedback humano é extremamente valioso:
        *   Serve para identificar respostas problemáticas ou de baixa qualidade.
        *   Pode constituir um **dataset qualitativo** que, se recolhido e analisado sistematicamente, poderia ser utilizado para futuras iterações de desenvolvimento, como a afinação fina (fine-tuning) do LLM ou o treino de um modelo de recompensa para Reinforcement Learning from Human Feedback (RLHF), embora estas técnicas avançadas não tenham sido implementadas.
    *   **Avaliação do Histórico de Conversa:** A capacidade de manter um histórico de conversação permite testar a coerência, a capacidade de resolução de co-referências e a manutenção do contexto em diálogos multi-turno.
    *   Não se observa um sistema de benchmarking automatizado com um conjunto de perguntas fixas como na Fase I. A ênfase deslocou-se para a avaliação qualitativa e interativa.

É importante notar a **ausência de métricas automáticas de avaliação específicas para RAG** em ambas as fases. Ferramentas e _frameworks_ como RAGAs, TruLens, ou ARES, que avaliam aspetos como a fidelidade da resposta ao contexto, a relevância do contexto recuperado, e a qualidade da resposta gerada, não foram implementadas. A introdução futura de tais métricas poderia fornecer uma avaliação mais objetiva e escalável da qualidade da recuperação de informação e da geração de linguagem, complementando os testes manuais e interativos.

A evolução nas estratégias de teste reflete a passagem de uma fase de exploração de componentes e benchmarking (Fase I) para uma fase de desenvolvimento de um sistema mais orientado ao utilizador e à sua experiência interativa (Fase II).

## 6. Ajustes no Fluxo de Interação com o Utilizador (UX Conversacional)

A experiência do utilizador (UX) numa aplicação conversacional é paramount, influenciando diretamente a sua adoção e eficácia. O projeto AlbiBooks demonstrou uma evolução considerável no design da interação entre a Fase I e a Fase II, transitando de uma abordagem puramente técnica para uma mais centrada no utilizador.

### 6.1. Interface e Modo de Interação

*   **Fase I (`AlbiBooks.ipynb`):**
    *   A interação com o sistema era predominantemente **programática**, confinada ao ambiente de um Jupyter Notebook. As perguntas eram submetidas através da execução de células de código Python, quer chamando diretamente a função `answer_with_rag(question, llm, knowledge_index, num_docs_final)`, quer utilizando a função auxiliar `questions_from_file` que processava um lote de perguntas de um ficheiro JSON.
    *   As respostas e os documentos de suporte eram apresentados como **saída de texto simples na consola** do notebook ou, no caso do processamento em lote, persistidos em ficheiros JSON (`answers.json`) para análise offline.
    *   Este modo de interação, embora eficiente para desenvolvimento e depuração por programadores, é inadequado para um utilizador final não técnico, pois carece de uma interface dedicada e intuitiva.

*   **Fase II (`Copy_of_GeminiFlash2p5V6Stable.ipynb`):**
    *   A alteração mais impactante na UX foi a introdução de uma **interface gráfica de utilizador (GUI) baseada em Gradio**. Especificamente, utilizou-se `gr.ChatInterface`, um componente de alto nível do Gradio que rapidamente cria uma interface de chat. Esta interface apresenta uma **caixa de texto** para o utilizador inserir a sua pergunta e uma **área de exibição do diálogo** que mostra o histórico da conversação (perguntas do utilizador e respostas do chatbot) de forma clara e organizada.
    *   Para melhorar a perceção de interatividade e naturalidade, a resposta do chatbot é apresentada com um **efeito de "escrita" progressiva**. Isto é conseguido no código através de `yield response[:i+1]` dentro de um ciclo, onde cada pequena porção da resposta é enviada para a interface com um pequeno atraso (`time.sleep(0.01)`), simulando que o chatbot está a "digitar" a resposta.
    *   Embora o notebook da Fase II também mantenha uma função `perguntar_ao_assistente` para interação via consola (que, ao contrário da Fase I, já incorpora gestão de histórico), a interface Gradio representa o principal avanço na UX.
    *   O Gradio facilita enormemente a **demonstração do chatbot** a _stakeholders_ e permite **testes iterativos** mais rápidos e eficazes, pois os programadores e testadores podem interagir com o sistema de forma natural, sem necessidade de escrever código para cada pergunta.

### 6.2. Gestão do Histórico de Conversação

A capacidade de manter o contexto ao longo de um diálogo é fundamental para a coerência e naturalidade de um chatbot.

*   **Fase I:** A função `answer_with_rag` processava cada pergunta de forma isolada, **sem qualquer mecanismo explícito de gestão de histórico** dentro da própria função. Se fosse necessário considerar o contexto de interações anteriores (e.g., para resolver pronomes ou responder a perguntas de seguimento), essa lógica teria de ser implementada manualmente pelo programador no código que orquestrasse as chamadas sucessivas à função `answer_with_rag`.

*   **Fase II:** Foi implementada uma **gestão explícita do histórico de conversação** dentro do fluxo principal do chatbot.
    *   Uma lista Python, designada `history` no código da função `answer_question` (que é chamada pela interface Gradio), armazena as trocas de perguntas e respostas da sessão de chat atual. Cada elemento da lista é tipicamente uma tupla `(pergunta_utilizador, resposta_chatbot)`.
    *   Quando uma nova interação ocorre, é acrescentada à lista `history`. Se o comprimento da lista exceder `MAX_HISTORY_LENGTH` (definido como 10 trocas), a interação mais antiga é removida, implementando uma janela deslizante de histórico.
    *   A função `format_history` transforma esta lista numa representação textual linear (e.g., "Utilizador: Pergunta1\nAssistente: Resposta1\nUtilizador: Pergunta2...") que é pré-anexada ao prompt enviado ao modelo Gemini.
    *   **Exemplo de utilidade:** Se o utilizador pergunta "Quais são os livros de Saramago na biblioteca?" e o chatbot lista três livros, uma pergunta de seguimento como "E sobre o segundo que mencionaste, está disponível?" pode ser corretamente interpretada pelo Gemini, pois o histórico fornece o contexto de qual foi o "segundo livro mencionado".
    *   O `MAX_HISTORY_LENGTH` representa um trade-off: um histórico mais longo permite manter o contexto por mais tempo, mas aumenta o número de tokens enviados à API (potenciando custos e latência) e pode tornar o prompt demasiado complexo para o LLM processar eficazmente.

### 6.3. Orientação do Comportamento do Chatbot

Controlar ou guiar o comportamento do LLM é crucial para alinhar as suas respostas com o propósito da aplicação e as expectativas do utilizador.

*   **Fase I:** O comportamento do LLM era primariamente determinado pelas suas características de treino prévio e pelo conteúdo factual dos chunks de texto recuperados. **Não havia instruções explícitas no prompt** para guiar o tom, estilo ou persona da resposta.

*   **Fase II:** O prompt enviado ao Gemini é cuidadosamente construído para incluir **instruções específicas (prompt engineering)** que moldam o comportamento do chatbot:
    *   `"Você é um assistente de biblioteca amigável."`: Esta instrução visa estabelecer um **tom cordial e prestável** na interação, melhorando a perceção da UX.
    *   `"Se não houver informação suficiente, seja honesto e sugira algo útil."`: Promove a **transparência e a honestidade intelectual** do chatbot. Em vez de inventar informação (alucinar) quando não encontra dados relevantes, é instruído a admitir a limitação e, idealmente, a oferecer alternativas ou sugestões construtivas.
    *   `"Sempre refira a localização do livro (a biblioteca onde se encontra)."`: Esta é uma instrução de domínio específico, crucial para um assistente de biblioteca. Garante que o chatbot tenta fornecer **informação prática e acionável** (localização física e cota) que é frequentemente o objetivo principal do utilizador.
    *   Estas instruções, combinadas com as capacidades superiores de compreensão e seguimento de instruções do Gemini, contribuem para criar uma **persona de chatbot mais definida, útil e alinhada** com o seu papel. O chatbot não é apenas um recuperador de factos, mas um assistente com diretrizes de comportamento.
    *   A funcionalidade de _flagging_ do Gradio, embora não diretamente ligada ao prompt, permite que os utilizadores forneçam feedback que pode ser usado indiretamente para avaliar se o chatbot está a aderir a estas diretrizes de comportamento (e.g., se foi amigável, se forneceu a localização).

Esta orientação explícita é um passo importante para aumentar a fiabilidade, utilidade e qualidade geral da experiência conversacional na Fase II.

## 7. Ferramentas e Bibliotecas Utilizadas

A escolha de ferramentas e bibliotecas é fundamental na definição da arquitetura e das capacidades de um projeto de software. A evolução do AlbiBooks da Fase I para a Fase II foi acompanhada por uma reavaliação e alteração significativa do stack tecnológico, refletindo a maturação dos objetivos e da abordagem técnica.

### 7.1. Principais Ferramentas e Bibliotecas da Fase I (`AlbiBooks.ipynb`)

A Fase I do projeto recorreu a um conjunto de ferramentas predominantemente associadas ao ecossistema open-source da Hugging Face e à biblioteca Langchain, visando uma rápida prototipagem da pipeline RAG:

*   **`langchain`**: Serviu como o _framework_ central de orquestração. Providenciou abstrações para a divisão de texto (`RecursiveCharacterTextSplitter`), para a interface com modelos de embedding (`HuggingFaceEmbeddings`), e para a envolvência do motor de busca vetorial FAISS (`langchain.vectorstores.FAISS`), simplificando a montagem da pipeline RAG e a experimentação com diferentes componentes.
*   **`transformers`**: Biblioteca nuclear da Hugging Face, utilizada para carregar e executar modelos de linguagem (LLMs) como o "HuggingFaceH4/zephyr-7b-beta" e o modelo de embedding `thenlper/gte-small` de forma local. Componentes como `AutoTokenizer` e `AutoModelForCausalLM` foram essenciais para esta tarefa.
*   **`torch`**: Principal biblioteca de _deep learning_ (PyTorch) que serve de infraestrutura base para a `transformers`, realizando os cálculos tensoriais e operações de rede neural.
*   **`accelerate`**: Biblioteca da Hugging Face que simplifica a execução de código PyTorch em diversas configurações de hardware (CPU, GPU, multi-GPU), otimizando o desempenho sem grandes alterações no código.
*   **`bitsandbytes`**: Utilizada para carregar modelos de linguagem de grande dimensão com menor consumo de memória através de técnicas de quantização em 4-bits (`BitsAndBytesConfig`), tornando viável a execução de LLMs como o Zephyr 7B em ambientes com recursos limitados.
*   **`sentence-transformers`**: Embora a interação direta fosse frequentemente abstraída pelo Langchain, esta biblioteca é fundamental para muitos dos modelos de embedding da Hugging Face, incluindo o `thenlper/gte-small`, fornecendo a arquitetura e os pesos pré-treinados.
*   **`faiss-cpu`**: Implementação CPU da biblioteca FAISS (Facebook AI Similarity Search), utilizada para criar e gerir o índice de vetores de embeddings para uma busca de similaridade eficiente, mesmo com um número considerável de vetores.
*   **`datasets`**: Biblioteca da Hugging Face para carregar e manipular datasets de forma padronizada, utilizada aqui para aceder ao dataset `Eitanli/goodreads`.
*   **Utilitários Python:** Incluíam `json` (para manipulação de ficheiros JSON como `questions.json` e `answers.json`), `time` e `tracemalloc` (para medição de desempenho via decorador `@measure_execution`), e `tqdm` (para barras de progresso visuais durante operações longas).
*   Outras importações como `pacmap` (para redução de dimensionalidade e visualização de embeddings) e `openpyxl` (para interagir com ficheiros Excel) sugerem atividades exploratórias e de análise de dados que, embora não centrais à pipeline RAG principal, faziam parte do ambiente de desenvolvimento.

### 7.2. Principais Ferramentas e Bibliotecas da Fase II (`Copy_of_GeminiFlash2p5V6Stable.ipynb` e `Copy_of_GrokTryIndexacao.ipynb`)

A Fase II transitou para uma arquitetura que depende mais de APIs externas e ferramentas específicas para a interface, gestão de dados e robustez:

*   **`google-generativeai`**: O SDK oficial da Google foi introduzido para facilitar a comunicação com a API do modelo Gemini (e.g., `gemini-1.5-flash-latest`), permitindo a geração de respostas contextuais com base nos dados recuperados e no histórico da conversa.
*   **`requests`**: A biblioteca HTTP padrão em Python tornou-se essencial para interagir diretamente com a API REST da Mistral AI (endpoint `https://api.mistral.ai/v1/embeddings`), enviando os textos dos livros para obter os seus respetivos embeddings `mistral-embed`.
*   **`faiss-cpu`**: Manteve-se como a biblioteca de eleição para a criação (no notebook de indexação), persistência (como `book_index.faiss`) e carregamento/consulta (no notebook do chatbot) do índice vetorial FAISS.
*   **`gradio`**: Biblioteca utilizada para construir rapidamente interfaces de utilizador interativas para modelos de machine learning. Foi empregue para criar a `gr.ChatInterface`, melhorando significativamente a usabilidade e a capacidade de demonstração do AlbiBooks.
*   **`numpy`**: Fundamental para a manipulação eficiente de arrays numéricos, especialmente para armazenar os vetores de embeddings (como `book_embeddings.npy`) e para operações com o FAISS.
*   **`pickle`**: Utilizado para serializar e deserializar objetos Python, especificamente para guardar (`book_metadata.pkl`) e carregar a lista de metadados dos livros, que é associada aos embeddings.
*   **Utilitários Python:** `json` (para carregar os dados dos livros de `biblioteca_dados_combinado.json`), `os` (para interações com o sistema de ficheiros, e.g., verificar existência de ficheiros de índice), `time` (usado em `measure_execution` e para simular o efeito de "escrita" no Gradio), `tracemalloc` (para `measure_execution`), e `threading`.
*   **`threading`**: Especificamente utilizado na função `get_gemini_response_with_timeout` para implementar um mecanismo de _timeout_ para as chamadas à API Gemini, evitando que o sistema bloqueie indefinidamente em caso de problemas de rede ou da API.
*   **`google.colab.userdata`**: Utilidade específica do ambiente Google Colab, para aceder de forma segura a API keys (como `GEMINI_API_KEY` e `MISTRAL_API_KEY`) armazenadas como segredos do utilizador.

### 7.3. Justificativa para Mudanças de Ferramentas

As alterações no conjunto de ferramentas refletem as mudanças arquiteturais e a evolução dos requisitos do projeto, visando maior robustez, desempenho e qualidade:

*   **Abandono do `langchain`**: Embora o Langchain facilite a prototipagem rápida, a sua remoção na Fase II permitiu um **controlo mais granular e flexibilidade** sobre cada componente da pipeline RAG. Isto é particularmente vantajoso ao interagir diretamente com APIs específicas (Mistral, Gemini) que podem ter nuances não totalmente cobertas pelas abstrações do Langchain, ou ao implementar lógicas customizadas de formatação de prompt, gestão de histórico e tratamento de erros. O trade-off é a perda da conveniência de abstrações prontas a usar, exigindo mais código explícito.
*   **Substituição de `transformers` locais por SDKs de API**: A decisão de usar APIs para embeddings (Mistral) e geração de LLM (Gemini) foi estratégica.
    *   **Benefícios:** Acesso a modelos _state-of-the-art_ (SOTA) potencialmente mais poderosos e com melhor desempenho do que os que poderiam ser executados localmente com recursos limitados. Redução significativa da carga computacional local (CPU/GPU e memória). Manutenção e atualização dos modelos geridas pelos fornecedores das APIs.
    *   **Desvantagens:** Introdução de dependência de rede e potenciais latências. Custos associados ao uso das APIs. Menor controlo sobre a arquitetura e o funcionamento interno dos modelos.
*   **Introdução do `gradio`**: A necessidade de uma interface de utilizador mais rica, interativa e acessível para demonstração, teste e potencial utilização final levou à adoção do Gradio. Esta ferramenta simplifica drasticamente a criação de UIs para aplicações de IA.
*   **Uso de `numpy` e `pickle` para persistência**: Com a separação da fase de indexação (que se tornou um processo offline), tornou-se imperativo persistir os artefactos de indexação. `numpy` é ideal para armazenar eficientemente os arrays de embeddings (`.npy`), e `pickle` é uma forma conveniente de serializar a lista de metadados dos livros (`.pkl`) para carregamento rápido pelo chatbot.

A manutenção do **`faiss-cpu`** em ambas as fases atesta a sua contínua adequação, robustez e eficiência para tarefas de busca por similaridade em vetores de média a grande escala, mesmo em ambiente de CPU.

## 8. Justificações Técnicas para as Principais Decisões

A transição da Fase I para a Fase II do projeto AlbiBooks foi marcada por um conjunto de decisões arquiteturais e tecnológicas significativas. Cada decisão visou endereçar limitações identificadas na fase anterior e alinhar o sistema de forma mais eficaz com os objetivos de robustez, relevância, desempenho e experiência de utilização.

1.  **Mudança de Modelos de Embedding (Hugging Face local `thenlper/gte-small` para API Mistral `mistral-embed`)**
    *   **Contexto da Decisão:** A Fase I utilizava o `thenlper/gte-small` (dimensão 384), um modelo de embedding local eficiente para propósitos gerais. Contudo, para um domínio especializado como um catálogo de biblioteca e com um volume de dados crescente, a sua capacidade de discriminação semântica e a qualidade dos embeddings poderiam constituir um fator limitante. Além disso, a geração de embeddings para um grande volume de dados localmente é computacionalmente intensiva.
    *   **Benefícios Esperados e Alcançados:** A adoção do `mistral-embed` (dimensão 1024) via API procurou beneficiar de uma arquitetura de embedding potencialmente mais avançada e com maior capacidade de representação semântica, otimizada pela Mistral AI. Esperava-se que isto resultasse numa melhor qualidade de recuperação de informação, especialmente para as nuances do vocabulário específico dos metadados dos livros. A mudança também desonerou significativamente os recursos computacionais locais, particularmente no processo de indexação dos mais de 18.000 livros da Fase II. O acesso via API simplifica a manutenção, pois o modelo é gerido e atualizado pelo fornecedor.
    *   **Trade-offs Considerados:** A principal desvantagem é a introdução de uma dependência de um serviço externo e da rede. Isto implica gerir latências de comunicação, possíveis custos associados ao uso da API (volume de chamadas) e a necessidade de gerir chaves de API de forma segura. Há também um menor controlo sobre o modelo de embedding em si (e.g., arquitetura exata, dados de treino).
    *   **Impacto Global no Projeto:** Esta mudança contribuiu para a melhoria da qualidade da recuperação de informação, um pilar fundamental do sistema RAG. Ao descarregar a tarefa de embedding, permitiu focar recursos no desenvolvimento de outros aspetos do sistema e viabilizou a indexação de um volume de dados muito maior, aumentando a relevância geral do AlbiBooks.

2.  **Mudança de Modelos de Geração de Linguagem (LLMs locais para API Gemini `gemini-1.5-flash-latest`)**
    *   **Contexto da Decisão:** A Fase I utilizava LLMs open-source locais (e.g., Zephyr 7B, Llama 2 13B) quantizados. Embora permitissem total controlo e ausência de custos de API, estes modelos, mesmo as versões mais pequenas, exigiam recursos computacionais consideráveis (VRAM, CPU) e apresentavam latências de inferência elevadas. As suas capacidades de compreensão de contextos longos, raciocínio complexo e seguimento de instruções detalhadas no prompt também poderiam ser inferiores às de modelos de fronteira proprietários.
    *   **Benefícios Esperados e Alcançados:** A transição para o `gemini-1.5-flash-latest` via API da Google visou alavancar um modelo de linguagem de grande escala com capacidades superiores de compreensão, geração de texto mais fluente e coerente, melhor raciocínio e um seguimento mais fiável de instruções complexas (essencial para o _prompt engineering_ da Fase II). Isto traduziu-se em respostas potencialmente mais precisas, contextualmente relevantes e estilisticamente alinhadas com a persona definida para o chatbot. Eliminou-se a complexidade da gestão de infraestrutura local para LLMs e a necessidade de otimizações como a quantização.
    *   **Trade-offs Considerados:** Semelhante à mudança nos embeddings, esta decisão introduziu dependência da API da Google, potenciais custos por volume de tokens processados e a variabilidade da latência de rede. Perde-se o controlo direto sobre a arquitetura do modelo, o seu ciclo de atualizações e a total privacidade dos dados enviados (embora os fornecedores de API geralmente garantam a confidencialidade).
    *   **Impacto Global no Projeto:** Melhorou significativamente a qualidade e a sofisticação das respostas geradas, contribuindo para uma experiência conversacional mais natural e útil. Permitiu a implementação eficaz de um _prompt engineering_ mais detalhado, crucial para o comportamento desejado do assistente de biblioteca.

3.  **Separação do Processo de Indexação**
    *   **Contexto da Decisão:** Na Fase I, a indexação (se não persistida manualmente fora do fluxo do notebook) era tipicamente executada como parte do mesmo fluxo de trabalho da conversação, o que era moroso e ineficiente, especialmente com o aumento do volume de dados.
    *   **Benefícios Esperados e Alcançados:** A criação de um notebook dedicado (`Copy_of_GrokTryIndexacao.ipynb`) para a indexação tornou este um processo offline e independente. Isto melhorou drasticamente a modularidade: o chatbot (`Copy_of_GeminiFlash2p5V6Stable.ipynb`) inicia muito mais rapidamente, pois apenas carrega os artefactos pré-computados (índice FAISS, embeddings NumPy, metadados Pickle). A manutenção é facilitada, permitindo atualizações ou reindexação do catálogo sem interromper o chatbot. Os artefactos de indexação podem ser versionados e geridos de forma independente.
    *   **Trade-offs Considerados:** Introduz a necessidade de gerir o fluxo de dados entre dois processos/notebooks, incluindo o armazenamento e o acesso aos artefactos de indexação (resolvido com o Google Drive). Qualquer atualização no catálogo de livros exige a re-execução do notebook de indexação.
    *   **Impacto Global no Projeto:** Aumentou a eficiência operacional, a escalabilidade do processo de indexação e a rapidez de arranque do chatbot, contribuindo para a robustez e manutenibilidade do sistema.

4.  **Alteração na Fonte e Estrutura dos Dados para Embeddings**
    *   **Contexto da Decisão:** A Fase I utilizava um dataset genérico do Goodreads, focando-se nas descrições textuais dos livros. Esta abordagem limitava severamente a relevância do chatbot para um contexto bibliotecário real, que requer acesso a metadados específicos como cota e localização.
    *   **Benefícios Esperados e Alcançados:** A mudança para o `biblioteca_dados_combinado.json` (catálogo específico da biblioteca) e a estratégia de criar um embedding único por livro, consolidando múltiplos campos de metadados (`title`, `authors`, `language_code`, `subjects_normalized_short_display`, `shelvingloc`, `call_no`, etc.) através da função `format_book_text`, foram cruciais. Isto permitiu que o sistema recuperasse informação diretamente relevante para as necessidades dos utilizadores de uma biblioteca. A representação vetorial tornou-se mais holística, capturando a semântica do livro através de diversos atributos, e não apenas da sua descrição.
    *   **Trade-offs Considerados:** A qualidade do embedding consolidado depende da qualidade e relevância dos campos incluídos. Campos ruidosos ou excessivamente longos poderiam, teoricamente, dominar o embedding. No entanto, para metadados de biblioteca, esta abordagem mostrou-se eficaz.
    *   **Impacto Global no Projeto:** Esta foi uma das alterações mais impactantes para a relevância e utilidade do AlbiBooks. Permitiu que o chatbot respondesse a perguntas práticas e específicas do contexto bibliotecário, tornando-o uma ferramenta potencialmente valiosa.

5.  **Introdução de Interface Gráfica (Gradio) e Gestão de Histórico**
    *   **Contexto da Decisão:** A Fase I carecia de uma interface de utilizador intuitiva (interação puramente programática) e não geria o histórico da conversa, limitando cada interação a um único turno.
    *   **Benefícios Esperados e Alcançados:** A interface Gradio (`gr.ChatInterface`) tornou o sistema acessível a utilizadores não técnicos, facilitando a demonstração, o teste interativo e a recolha de feedback. A gestão explícita do histórico de conversação (armazenando e reenviando as últimas `MAX_HISTORY_LENGTH` trocas) permitiu diálogos mais naturais, coerentes e contextualmente informados, onde o chatbot pode compreender referências a turnos anteriores e responder a perguntas de seguimento.
    *   **Trade-offs Considerados:** A gestão de histórico aumenta o número de tokens enviados ao LLM, o que pode ter implicações de custo e latência. A interface Gradio, embora fácil de implementar, pode ter limitações em termos de personalização avançada da UI em comparação com _frameworks_ web dedicados.
    *   **Impacto Global no Projeto:** Melhorou drasticamente a experiência do utilizador (UX) e a usabilidade do sistema. A gestão de histórico é uma funcionalidade fundamental para qualquer chatbot que aspire a interações minimamente sofisticadas.

6.  **Abandono do Langchain e Implementação Direta da Lógica RAG**
    *   **Contexto da Decisão:** O Langchain foi útil na Fase I para prototipagem rápida. No entanto, à medida que os requisitos se tornaram mais específicos, especialmente em relação à interação com APIs e à personalização do fluxo de dados, a camada de abstração do Langchain podia impor limitações.
    *   **Benefícios Esperados e Alcançados:** A implementação direta da lógica RAG na Fase II proporcionou um controlo mais granular sobre cada etapa: formatação de pedidos para as APIs Mistral e Gemini, tratamento de respostas, construção de prompts, e integração do histórico. Isto facilitou otimizações específicas, a implementação de mecanismos de robustez personalizados e uma maior transparência no fluxo de dados, o que pode ser benéfico para depuração.
    *   **Trade-offs Considerados:** Exigiu a escrita de mais código explícito para funcionalidades que o Langchain abstrai (e.g., algumas formas de encadeamento de chamadas, formatação de prompts). A manutenção deste código customizado recai inteiramente sobre o programador.
    *   **Impacto Global no Projeto:** Permitiu uma integração mais afinada com os serviços de API escolhidos e uma maior flexibilidade na implementação da lógica RAG, contribuindo para a robustez e o desempenho otimizado do sistema da Fase II.

7.  **Implementação de Mecanismos Robustos de Interação com APIs (Retry, Timeout)**
    *   **Contexto da Decisão:** As interações com APIs externas (Mistral, Gemini) são inerentemente suscetíveis a falhas de rede, sobrecarga do servidor da API, ou outros problemas transitórios. A ausência de mecanismos de tratamento destas situações tornaria o sistema pouco fiável.
    *   **Benefícios Esperados e Alcançados:** A introdução explícita de lógicas de _retry_ com _backoff exponencial_ (para a API Mistral, através da função `get_embedding_with_retry`) e _timeouts_ com _retries_ (para a API Gemini, através de `get_gemini_response_with_timeout` usando `threading`) na Fase II aumentou significativamente a fiabilidade e resiliência do sistema. Estes mecanismos permitem que o chatbot lide graciosamente com falhas temporárias, repetindo a chamada à API algumas vezes antes de desistir, o que melhora a experiência do utilizador ao minimizar interrupções.
    *   **Trade-offs Considerados:** A implementação destes mecanismos adiciona alguma complexidade ao código. Definir tempos de _timeout_ e número de _retries_ apropriados requer alguma experimentação para equilibrar a persistência em caso de falha com a capacidade de resposta do sistema.
    *   **Impacto Global no Projeto:** Crucial para a robustez de um sistema que depende de serviços externos. Sem estes mecanismos, a aplicação seria frágil e propensa a falhas frequentes, minando a confiança do utilizador.

Estas decisões, consideradas no seu conjunto, demonstram uma progressão informada e iterativa, onde as aprendizagens da Fase I levaram a escolhas de engenharia na Fase II que resultaram num sistema AlbiBooks significativamente mais capaz, relevante e robusto para o seu propósito como assistente de biblioteca.

## Conclusão

A trajetória do projeto AlbiBooks, desde o protótipo inicial da Fase I até à versão mais elaborada da Fase II, demonstra uma evolução técnica e funcional considerável. A Fase I estabeleceu uma prova de conceito viável, utilizando ferramentas open-source como Langchain e modelos da Hugging Face para implementar um sistema RAG básico. Embora funcional, esta fase caracterizava-se por uma arquitetura monolítica para indexação e conversação, dependência de datasets genéricos e uma interface de utilizador programática.

A Fase II representa um salto qualitativo em direção a um sistema mais robusto, especializado e com foco na experiência do utilizador. As principais transformações incluem:

*   **Adoção de APIs Especializadas:** A transição para a API da Mistral para geração de embeddings e para a API Gemini para a geração de respostas permitiu alavancar modelos de IA de ponta, potencialmente mais poderosos e otimizados, ao mesmo tempo que reduziu a carga computacional local.
*   **Arquitetura Modular:** A separação do processo de indexação da componente conversacional resultou num design mais limpo, eficiente e fácil de manter.
*   **Dados Específicos e Contexto Enriquecido:** A utilização de um catálogo de biblioteca real e a criação de embeddings a partir de metadados consolidados por livro aumentaram significativamente a relevância e a precisão do sistema. A informação fornecida ao LLM tornou-se mais estruturada e detalhada.
*   **Melhoria da Experiência do Utilizador:** A introdução de uma interface gráfica com Gradio e a implementação da gestão do histórico de conversação transformaram a interação com o AlbiBooks, tornando-a mais intuitiva, natural e útil.
*   **Maior Controlo e Robustez:** A implementação direta da pipeline RAG e a incorporação de mecanismos de _retry_ e _timeout_ para as chamadas de API conferiram maior controlo sobre o fluxo de dados e aumentaram a fiabilidade do sistema.

Em suma, o AlbiBooks evoluiu de um protótipo exploratório para uma aplicação mais madura, que reflete uma compreensão mais profunda dos requisitos de um chatbot para bibliotecas. As decisões técnicas tomadas na Fase II, como a escolha de modelos de API, a reestruturação da arquitetura de dados e a priorização da UX, foram fundamentais para alcançar um sistema mais capaz de responder eficazmente às necessidades dos seus utilizadores no contexto específico de uma biblioteca. O projeto demonstra uma clara progressão na aplicação de técnicas de IA generativa e recuperação de informação para resolver um problema do mundo real.
