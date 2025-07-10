import requests
from bs4 import BeautifulSoup
import json
import time
import random

BASE_URL = "https://catalogo.ipcb.pt/cgi-bin/koha/opac-detail.pl?biblionumber={}"
ID_MIN = 40
ID_MAX = 71292 + 40  # 71332
SAMPLE_SIZE = 2000
OUTPUT_FILE = "biblioteca_dados_amostra.json"
ERROR_PAGE_TEXT = "Erro 404"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9",
    "Referer": "https://catalogo.ipcb.pt/"
}

session = requests.Session()
session.headers.update(HEADERS)

def scrape_book_details(book_id):
    # Função de scraping existente - sem alterações
    url = BASE_URL.format(book_id)
    print(f"Acessando {url}...")  
    try:
        response = session.get(url, timeout=10)

        if response.status_code != 200 or ERROR_PAGE_TEXT in response.text:
            print(f"Livro ID {book_id} não encontrado ou erro 404.")
            return None 
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Título
        titulo = soup.find("h1").get_text(strip=True) if soup.find("h1") else None

        # Autor - método alternativo 
        autor = None
        autor_labels = soup.find_all("span", class_="label")
        for label in autor_labels:
            if "Autor" in label.get_text():
                parent = label.parent
                autor_link = parent.find("a")
                if autor_link:
                    autor = autor_link.get_text(strip=True)
                break
        
        # Co-autor - método alternativo
        co_autor = None
        for label in autor_labels:
            if "Co-autor" in label.get_text():
                parent = label.parent
                co_autor_link = parent.find("a")
                if co_autor_link:
                    co_autor = co_autor_link.get_text(strip=True)
                break
        
        # Idioma - método alternativo
        idioma = None
        for label in autor_labels:
            if "Idioma" in label.get_text():
                parent = label.parent
                idioma_span = parent.find_all("span")
                if len(idioma_span) > 1:
                    idioma = idioma_span[1].get_text(strip=True)
                break
        
        # País - método alternativo
        pais = None
        for label in autor_labels:
            if "País" in label.get_text():
                parent = label.parent
                pais_span = parent.find_all("span")
                if len(pais_span) > 1:
                    pais = pais_span[1].get_text(strip=True)
                break
        
        # Nome comum - pode conter múltiplos valores
        nome_comum = []
        for label in autor_labels:
            if "Nome comum" in label.get_text():
                parent = label.parent
                links = parent.find_all("a")
                for link in links:
                    nome_comum.append(link.get_text(strip=True))
                break
        
        # Dados adicionais (Tabela)
        itype = None
        shelvingloc = None
        call_no = None
        
        tabela = soup.find("tr", typeof="Offer")
        if tabela:
            itype_cell = tabela.find("td", class_="itype")
            if itype_cell:
                itype = itype_cell.get_text(strip=True)
            
            shelving_span = tabela.find("span", class_="shelvingloc")
            if shelving_span:
                shelvingloc = shelving_span.get_text(strip=True)
            
            call_no_cell = tabela.find("td", class_="call_no")
            if call_no_cell:
                call_no = call_no_cell.get_text(strip=True)
        
        return {
            "id": book_id,
            "titulo": titulo,
            "autor": autor,
            "co-autor": co_autor,
            "idioma": idioma,
            "pais": pais,
            "nome_comum": nome_comum,
            "itype": itype,
            "shelvingloc": shelvingloc,
            "call_no": call_no
        }
    except requests.exceptions.Timeout:
        print(f"Tempo limite excedido ao acessar ID {book_id}. Pulando...")
        return None
    except Exception as e:
        print(f"Erro inesperado ao acessar ID {book_id}: {e}")
        return None

def main():
    # Gerar lista de IDs aleatórios sem repetição
    print(f"Gerando {SAMPLE_SIZE} IDs aleatórios entre {ID_MIN} e {ID_MAX}...")
    random_ids = random.sample(range(ID_MIN, ID_MAX + 1), SAMPLE_SIZE)
    
    books_data = []
    successful_scrapes = 0
    total_attempts = 0
    
    # Arquivo para salvar progresso
    progress_file = OUTPUT_FILE.replace('.json', '_progress.json')
    
    try:
        # Tentar carregar progresso anterior, se existir
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                books_data = json.load(f)
                # Excluir IDs já raspados da lista
                scraped_ids = {book['id'] for book in books_data}
                random_ids = [id for id in random_ids if id not in scraped_ids]
                print(f"Carregado progresso anterior: {len(books_data)} livros já raspados.")
        except (FileNotFoundError, json.JSONDecodeError):
            print("Nenhum progresso anterior encontrado. Iniciando do zero.")
        
        # Iniciar contagem
        successful_scrapes = len(books_data)
        
        for book_id in random_ids:
            total_attempts += 1
            print(f"[{successful_scrapes}/{SAMPLE_SIZE}] Tentativa {total_attempts}: Scraping livro ID: {book_id}")
            
            book_data = scrape_book_details(book_id)
            
            if book_data and book_data["titulo"]:  # Verifica se obteve pelo menos o título
                books_data.append(book_data)
                successful_scrapes += 1
                
                # Salvar progresso a cada 10 livros
                if successful_scrapes % 10 == 0:
                    with open(progress_file, 'w', encoding='utf-8') as f:
                        json.dump(books_data, f, ensure_ascii=False, indent=4)
                    print(f"Progresso salvo: {successful_scrapes}/{SAMPLE_SIZE} livros")
                
                if successful_scrapes >= SAMPLE_SIZE:
                    break
            
            # Tempo de espera aleatório entre requisições
            wait_time = random.uniform(3, 7)
            print(f"Aguardando {wait_time:.1f} segundos...")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário. Salvando dados coletados até agora...")
    
    finally:
        # Salvar resultados finais
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(books_data, f, ensure_ascii=False, indent=4)
        
        print(f"\nScraping concluído. {successful_scrapes} livros salvos em {OUTPUT_FILE}")
        print(f"Total de tentativas: {total_attempts}")

if __name__ == "__main__":
    main()