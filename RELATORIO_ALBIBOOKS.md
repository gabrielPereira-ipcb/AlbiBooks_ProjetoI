**Relatório Comparativo da Evolução do Projeto AlbiBooks**

**1. Introdução**

O projeto AlbiBooks visa desenvolver um assistente conversacional inteligente (chatbot) para auxiliar os utilizadores de uma biblioteca, fornecendo informações sobre o acervo bibliográfico e respondendo a questões relacionadas. Este relatório tem como objetivo descrever a evolução do projeto desde a sua fase de prototipagem inicial, materializada no notebook `AlbiBooks.ipynb`, até à sua versão final mais robusta e otimizada, apresentada em `GeminiFlashLiteV6UStable.ipynb`. A transição entre estas duas fases reflete um processo iterativo de desenvolvimento, incorporando aprendizagens da pesquisa e prototipagem realizadas, nomeadamente no âmbito de um Projeto I anterior, que explorou as bases da tecnologia de Retrieval Augmented Generation (RAG).

**2. Metodologia do Protótipo (`AlbiBooks.ipynb`)**

O protótipo inicial (`AlbiBooks.ipynb`) focou-se em estabelecer a viabilidade de um sistema RAG para responder a perguntas sobre livros. As principais bibliotecas utilizadas incluíram `transformers` para o acesso a modelos de linguagem, `langchain` como framework para a construção da aplicação RAG, `faiss-cpu` para a criação de índices vetoriais e `datasets` para o manuseamento de dados.

O fluxo de processamento de dados iniciava-se com o carregamento do dataset "Eitanli/goodreads". Para efeitos de prototipagem, apenas uma subseção de 500 linhas era selecionada. A partir destas, as descrições dos livros eram extraídas e convertidas em objetos `LangchainDocument`, aos quais se associavam metadados como autor, título e género. Estes documentos eram subsequentemente divididos em chunks menores utilizando `RecursiveCharacterTextSplitter`, com um tamanho de chunk de 512 caracteres e um overlap de 50.

A estratégia de RAG consistia na geração de embeddings para estes chunks utilizando o modelo `"thenlper/gte-small"` (via `HuggingFaceEmbeddings`). Um índice vetorial FAISS era então construído em tempo real (`FAISS.from_documents`) a partir destes embeddings. Para a fase de geração de respostas, foram testados diversos Modelos de Linguagem de Grande Escala (LLMs) open-source, como `"HuggingFaceH4/zephyr-7b-beta"`, `"meta-llama/Llama-2-13b-chat-hf"` e `"distilgpt2"`, carregados e executados localmente (com recurso a quantização em 4 bits para mitigar limitações de hardware). O prompt enviado a estes LLMs era estruturado para incluir o contexto recuperado do índice FAISS e a pergunta do utilizador.

A avaliação do desempenho era realizada através de uma função `measure_execution`, que registava o tempo de execução e o uso de memória. Os testes funcionais eram conduzidos com um conjunto predefinido de perguntas armazenadas num ficheiro `questions.json`, e as respostas, juntamente com as métricas de desempenho, eram guardadas em `answers.json`.

**3. Metodologia da Versão Final (`GeminiFlashLiteV6UStable.ipynb`)**

A versão final do AlbiBooks (`GeminiFlashLiteV6UStable.ipynb`) representa uma evolução significativa, incorporando otimizações e recorrendo a tecnologias de API para componentes chave. Para a geração de respostas, o sistema utiliza a API Google Gemini, especificamente o modelo `gemini-2.0-flash-lite`. A geração de embeddings para as perguntas dos utilizadores (queries) é delegada à API da Mistral AI, através do modelo `mistral-embed`.

O fluxo de processamento de dados foi revisto para maior eficiência. Em vez de processar dados em tempo real, a versão final carrega embeddings de livros, os seus metadados e um índice FAISS pré-processados a partir de um diretório específico (`EMBEDDINGS_DIR`). Esta abordagem sugere que uma etapa de processamento offline mais exaustiva foi realizada, resultando numa base de conhecimento mais completa e num arranque do sistema consideravelmente mais rápido. A função `initialize_retriever` é responsável por carregar estes recursos.

O sistema de RAG foi aprimorado com funcionalidades para aumentar a robustez e a qualidade da interação. Foi implementada a gestão do histórico de conversas (limitado por `MAX_HISTORY_LENGTH`), permitindo que o chatbot mantenha o contexto ao longo de múltiplas interações. Adicionalmente, foram introduzidos mecanismos de retry com backoff exponencial e timeouts para as chamadas às APIs externas (Mistral e Gemini), conferindo maior resiliência ao sistema perante falhas transientes ou lentidão das APIs. A estrutura do prompt enviado ao modelo Gemini foi enriquecida, incorporando não só o contexto recuperado e a pergunta, mas também uma persona para o chatbot ("assistente de biblioteca amigável") e o histórico da conversa formatado.

Para a interação com o utilizador, foi desenvolvida uma interface gráfica utilizando a biblioteca `gradio`, através da função `chatbot_interface`. A medição de performance com a função `measure_execution` foi mantida, e as métricas são agora apresentadas diretamente na interface Gradio, oferecendo feedback imediato sobre a eficiência de cada consulta.

**4. Análise Comparativa e Evolução do Projeto**

A transição do protótipo `AlbiBooks.ipynb` para a versão `GeminiFlashLiteV6UStable.ipynb` reflete uma maturação significativa do projeto AlbiBooks. Esta evolução é marcada por otimizações em performance, robustez, qualidade da interação e pela adoção de serviços especializados de Modelos de Linguagem (LLMs) e embeddings através de APIs.

**4.1. Bibliotecas e Modelos:**

*   **Comparação:**
    *   **Protótipo (`AlbiBooks.ipynb`):** Utilizava predominantemente bibliotecas open-source do ecossistema Hugging Face. Para embeddings, recorria a `HuggingFaceEmbeddings` com o modelo `"thenlper/gte-small"`. Para a geração de respostas (LLM), testou diversos modelos carregados localmente (ou via Hugging Face Hub), como `"HuggingFaceH4/zephyr-7b-beta"`, `"meta-llama/Llama-2-13b-chat-hf"` e `"distilgpt2"`. A gestão destes modelos implicava o download e, potencialmente, a configuração de `BitsAndBytesConfig` para quantização em 4 bits, visando a execução em hardware com recursos limitados (GPU Colab).
    *   **Versão Final (`GeminiFlashLiteV6UStable.ipynb`):** Migrou para a utilização de APIs comerciais. Para embeddings, adotou a API da Mistral com o modelo `"mistral-embed"`. Para a geração de respostas, utiliza a API Google Gemini com o modelo `"gemini-2.0-flash-lite"`. As bibliotecas `transformers` e `torch` ainda são relevantes, mas o foco desloca-se da gestão local de modelos para a interação com estas APIs (`google-generativeai` para Gemini, `requests` para Mistral).

*   **Justificativa das Mudanças:**
    *   **Performance e Qualidade da Resposta:** APIs como Gemini e Mistral oferecem acesso a modelos de ponta, frequentemente mais poderosos e com melhor qualidade de resposta do que modelos open-source que podem ser executados localmente com recursos restritos. O modelo Gemini Flash Lite, por exemplo, é otimizado para respostas rápidas.
    *   **Custo e Complexidade de Gestão:** Embora as APIs tenham custos associados por utilização, eliminam a complexidade de descarregar, configurar, otimizar (quantização) e servir modelos localmente. Isto simplifica a arquitetura, reduz o tempo de setup e os requisitos de hardware para inferência.
    *   **Escalabilidade:** As APIs são geridas pelos fornecedores (Google, Mistral) e oferecem maior escalabilidade inerente comparativamente à gestão manual de modelos em infraestrutura própria ou limitada como a do Colab.
    *   **Manutenção:** A utilização de APIs transfere a responsabilidade da manutenção e atualização dos modelos para os fornecedores, garantindo acesso a melhorias contínuas sem intervenção direta.

**4.2. Gestão de Dados:**

*   **Contraste:**
    *   **Protótipo:** Realizava o processamento de dados de forma síncrona e parcial. Carregava as primeiras 500 linhas do dataset "Eitanli/goodreads", extraía as descrições, convertia-as para `LangchainDocument`, dividia-as em chunks com `RecursiveCharacterTextSplitter`, e construía o índice vetorial FAISS (`FAISS.from_documents`) em tempo real a cada execução do notebook.
    *   **Versão Final:** Adota uma abordagem de pré-processamento. A função `initialize_retriever` carrega diretamente um array NumPy de embeddings (`book_embeddings.npy`), uma lista de metadados (`book_metadata.pkl`) e um índice FAISS pré-construído (`book_index.faiss`) a partir de um diretório específico (`EMBEDDINGS_DIR`). Isto implica que o dataset completo (ou uma porção significativamente maior) foi processado, embedado e indexado numa fase anterior, externa ao fluxo principal do notebook de inferência.

*   **Implicações:**
    *   **Eficiência e Tempo de Arranque:** A versão final é drasticamente mais eficiente no arranque. O tempo necessário para carregar ficheiros pré-processados é significativamente menor do que processar textos, gerar embeddings e construir um índice FAISS do zero a cada vez. Isto torna o sistema muito mais ágil para utilização imediata.
    *   **Reutilização:** Os artefactos pré-processados (embeddings, metadados, índice) são altamente reutilizáveis, não apenas por este notebook, mas potencialmente por outras aplicações ou serviços que necessitem de aceder à mesma base de conhecimento.
    *   **Consistência:** Utilizar dados pré-processados garante consistência na base de conhecimento utilizada para as buscas, eliminando variações que poderiam surgir de diferentes execuções do processamento de dados no protótipo.

**4.3. Robustez e Escalabilidade:**

*   **Funcionalidades na Versão Final:**
    *   **Gestão de Histórico de Conversas:** A introdução de `MAX_HISTORY_LENGTH` e a lógica para adicionar e truncar o histórico na função `answer_question` permitem que o chatbot mantenha um contexto ao longo de múltiplas interações, levando a respostas mais coerentes e relevantes em diálogos mais longos.
    *   **Mecanismos de Retry e Timeout:** As funções `get_embedding` (para a API Mistral) e `generate_gemini_response` (para a API Gemini) implementam estratégias de retry com backoff exponencial (`BASE_WAIT_TIME * (2 ** attempt)`) e timeouts específicos (`GEMINI_TIMEOUT`). Isto aumenta a robustez do sistema ao lidar com falhas transitórias de rede, sobrecarga das APIs ou respostas lentas, tornando o sistema mais resiliente a problemas comuns em sistemas distribuídos.

*   **Comparação com o Protótipo:**
    *   O protótipo não possuía gestão explícita de histórico de conversas; cada pergunta era tratada de forma isolada.
    *   Não havia mecanismos de retry ou timeout para o carregamento dos modelos de embedding ou LLM do Hugging Face, nem para a sua inferência, tornando-o mais suscetível a falhas sem recuperação automática. A robustez dependia inteiramente da estabilidade da ligação ao Hub e da disponibilidade dos recursos do Colab.

**4.4. Estratégias de RAG (Retrieval Augmented Generation):**

*   **Recuperação:**
    *   **Protótipo:** Criava um índice FAISS em memória (`FAISS.from_documents`) usando `HuggingFaceEmbeddings` (com `"thenlper/gte-small"`) a partir dos chunks de texto gerados das 500 descrições de livros. A busca era feita neste índice e os embeddings da query eram gerados pelo mesmo modelo.
    *   **Versão Final:** Carrega um índice FAISS pré-construído, sugerindo uma base de conhecimento mais extensa e estável. Para a busca, utiliza a API da Mistral (`mistral-embed`) para gerar o embedding da query do utilizador em tempo real. Este embedding é então usado para pesquisar no índice FAISS carregado. A mudança para `mistral-embed` pode oferecer embeddings de melhor qualidade ou mais alinhados com o tipo de dados e tarefas.

*   **Geração e Prompting:**
    *   **Protótipo:** O prompt enviado aos LLMs (Zephyr, Llama 2, DistilGPT2) era relativamente simples, contendo apenas o contexto extraído dos documentos recuperados e a pergunta do utilizador.
    *   **Versão Final:** Utiliza o modelo `gemini-2.0-flash-lite` através da sua API. O prompt é consideravelmente mais elaborado, incluindo uma persona ("assistente de biblioteca amigável"), o histórico da conversa formatado e o contexto recuperado. Esta abordagem mais sofisticada de engenharia de prompts visa melhorar a relevância e a qualidade das respostas. A função `format_context` na versão final também extrai um conjunto mais rico de metadados dos livros, fornecendo ao LLM informações mais completas.

*   **Impacto das Mudanças:**
    *   **Qualidade e Relevância:** A utilização de um modelo de embedding possivelmente superior (Mistral) e um LLM mais avançado (Gemini), juntamente com um prompt mais detalhado e contextual, tem o potencial de melhorar significativamente a relevância, precisão e naturalidade das respostas.
    *   **Conversas Contextuais:** A inclusão explícita do histórico da conversa é uma melhoria crucial para permitir diálogos mais longos e manter o contexto entre turnos, algo que o protótipo não suportava eficazmente.

**4.5. Interação com o Utilizador e Avaliação:**

*   **Contraste na Interação:**
    *   **Protótipo:** A interação era primariamente batch, com perguntas carregadas de um ficheiro `questions.json` e resultados guardados em `answers.json`. A avaliação focava-se em métricas de performance offline.
    *   **Versão Final:** Introduz uma interface gráfica interativa com `gradio` (`chatbot_interface`), permitindo uma utilização dinâmica. A medição de performance (`measure_execution`) é mantida, e as métricas são apresentadas na UI, oferecendo feedback imediato.

*   **Evolução na Experiência do Utilizador e Avaliação:**
    *   **Experiência do Utilizador:** A interface Gradio representa um salto qualitativo, tornando o sistema acessível e utilizável de forma intuitiva.
    *   **Avaliação:** A versão final permite uma avaliação qualitativa e interativa mais direta, complementando as métricas quantitativas. Os utilizadores podem aferir a qualidade das respostas e a fluidez da conversa em tempo real.

**4.6. Aprendizagens e Evolução Geral:**

*   **Principais Aprendizagens:**
    *   A exploração inicial evidenciou as limitações de recursos locais para LLMs de grande escala e a ineficiência do processamento de dados em tempo real para cada sessão.
    *   A importância do pré-processamento de dados e da utilização de APIs especializadas (Mistral, Gemini) emergiu como uma solução para melhorar performance, escalabilidade e reduzir a complexidade de gestão.
    *   A necessidade de funcionalidades como gestão de histórico, mecanismos de retry e engenharia de prompts mais sofisticada tornou-se clara para aumentar a robustez e a qualidade da interação conversacional.

*   **Evolução Geral do Projeto:**
    O projeto AlbiBooks evoluiu de uma prova de conceito focada na viabilidade da tecnologia RAG para um sistema mais maduro e orientado para a aplicação prática. A versão final demonstra um foco na otimização da performance (através de pré-processamento e APIs), na robustez (com retries e timeouts), na qualidade da interação (com prompts avançados e gestão de histórico) e na experiência do utilizador (com a interface Gradio). Esta transição reflete uma progressão natural no ciclo de vida de desenvolvimento de software de IA, onde as aprendizagens da prototipagem informam o design de um sistema mais refinado e eficiente.

**5. Conclusão**

A evolução do projeto AlbiBooks, desde o protótipo `AlbiBooks.ipynb` até à versão final `GeminiFlashLiteV6UStable.ipynb`, demonstra um progresso substancial em direção a um assistente de biblioteca mais funcional, robusto e eficiente. As principais diferenças residem na adoção de APIs especializadas para embeddings (Mistral) e geração de linguagem (Gemini), no pré-processamento da base de conhecimento para otimizar o tempo de arranque e na implementação de funcionalidades avançadas de RAG, como gestão de histórico e prompts mais contextuais.

A arquitetura final apresenta benefícios claros em termos de robustez, com a inclusão de mecanismos de retry e timeout, melhor performance devido ao uso de componentes pré-processados e APIs otimizadas, e uma qualidade de interação superior, possibilitada por LLMs mais avançados e uma engenharia de prompt mais cuidada. A introdução de uma interface Gradio também melhora significativamente a usabilidade e a capacidade de avaliação interativa.

As aprendizagens obtidas ao longo deste processo iterativo sublinham a importância da experimentação e da adaptação na construção de sistemas de IA complexos. A transição de modelos locais para APIs, a otimização do pipeline de dados e o refinamento contínuo da estratégia de RAG são testemunhos da natureza evolutiva do desenvolvimento neste domínio.

Como perspetivas futuras, poder-se-ia explorar a expansão da base de conhecimento, a inclusão de feedback do utilizador em tempo real para aprimoramento contínuo do modelo (fine-tuning ou reinforcement learning from human feedback - RLHF), ou a integração de funcionalidades adicionais, como a capacidade de realizar reservas de livros ou fornecer recomendações personalizadas mais elaboradas.
