# main.py
# Estrazione del contenuto principale (testo) da pagine HTML.
# Usa la libreria python BeautifulSoup per rimuovere elementi non utili come menu, pubblicità, script, ecc.
# Viene usato insieme a un crawler su HTML già scaricati (funziona meglio con pagine statiche).

from bs4 import BeautifulSoup

def extract_main_text(html):
    """
    Funzione per estrarre il testo principale da una pagina HTML, rimuovendo elementi non informativi.

    Parametri:
    - html (str): contenuto HTML della pagina.

    Ritorna:
    - str: testo pulito.
    """
    if not html:
        return "" # Restituisce una stringa vuota
    
    page = BeautifulSoup(html, 'html.parser')

    # Con 'decompose', rimuove:
    # script, style: codice invisibile
    # nav, footer, header, aside: menù, intestazione, pubblicità, ecc.
    for tag in page(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()


    # Cerca il contenuto principale, <main>
    possible_main = page.find('main')
    
    if possible_main:
        text = possible_main.get_text()
        # Se trova <main>, prende solo quel testo.
    else:
        text = page.get_text()
        # Se non lo trova, prende tutto il testo della pagina.


    # Pulisce gli spazi in più
    text = ' '.join(text.split())
    return text # Restituzione del testo pulito


# Esempio per testare il file
# python main.py pagina.html
if __name__ == "__main__":
    import sys

    file_name = sys.argv[1]

    with open(file_name, "r", encoding="utf-8") as f:
        html = f.read()

    # Usa la funzione per estrarre il testo pulito dall'HTML
    clean_text = extract_main_text(html)

    # Stampa il testo estratto
    print(clean_text)