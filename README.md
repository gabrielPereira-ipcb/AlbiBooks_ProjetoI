# AlbiBooks

## Description
**AlbiBooks** is an AI-based chatbot designed to interact with library databases. The main goal is to democratize access to library services, enabling book searches and recommendations in a practical and intuitive way. The project utilizes **Retrieval-Augmented Generation (RAG)** techniques to enhance response accuracy and relevance.

## Technologies Used
- **Python 3.11.11**
- **Google Colab** (development environment)
- **LangChain** (framework for LLM-based applications)
- **Hugging Face Transformers** (pre-trained models for NLP)
- **FAISS** (Facebook AI Similarity Search for vector-based retrieval)
- **PyTorch** (machine learning framework)
- **Goodreads Books Dataset (Kaggle)**

## Models Used
Three different Large Language Models (LLMs) were tested to evaluate the effectiveness of the approach:
- **DistilGPT2** – A compact and efficient text generation model.
- **Llama-2-13b-chat-hf** – A robust model for text understanding and generation.
- **Zephyr-7b-beta** – Specialized in interactive dialogues.

## Project Structure
```
AlbiBooks/
│── data/                  # Database used (Goodreads Books)
│── notebooks/             # Google Colab notebooks for implementation
│── models/                # Pre-trained models used
│── utils/                 # Helper functions for data loading and processing
│── README.md              # Project documentation
```

## How to Run
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/albibooks.git
   cd albibooks
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Open the notebook in Google Colab**:
   - Open the `.ipynb` file and execute the cells as described.
4. **Interact with the chatbot**:
   - Use the implemented functions in the notebook to test interactions with the model.

## Features
- Library catalog search.
- Personalized book recommendations.
- Optimized responses using RAG.
- Comparison of different AI models for performance evaluation.

## Results and Discussion
The tests indicate that the **RAG** implementation significantly improves response accuracy, reducing hallucinations and providing more relevant information. The **Llama-2-13b-chat-hf** model delivered the best overall performance, while **DistilGPT2** was the most efficient in terms of computational resources.

## Authors
- **Gabriel de Santana Pereira**
- **Ana Margarida Pereira Duarte**

This project was developed as part of the Bachelor's degree in Computer Science and Multimedia at the School of Technology of the Polytechnic Institute of Castelo Branco.

## References
- Base tutorial: [Advanced RAG on Hugging Face](https://huggingface.co/docs)
- Dataset: [Goodreads Books (Kaggle)](https://www.kaggle.com/datasets)

## License
This project is distributed under the MIT license.

