import os
import requests
from bs4 import BeautifulSoup

DEFAULT_URL = ""
HOME_PATH_DOWNLOAD = ""


def telecharger_liens(url):
    """
    Télécharge tous les fichiers liés à partir des balises <a href=...> d'une page web.

    Args:
      url: L'URL de la page web à analyser.

    Returns:
      Une liste des URLs qui n'ont pas pu être téléchargées.
    """

    try:
        response = requests.get(url)
        response.raise_for_status()  # Lève une exception si le statut de la réponse n'est pas OK
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'accès à l'URL {url}: {e}")
        return [url]

    soup = BeautifulSoup(response.content, "html.parser")
    liens = [a["href"] for a in soup.find_all("a", href=True)]

    urls_echec = []
    for lien in liens:
        try:
            # Télécharger le fichier
            path_download = (
                HOME_PATH_DOWNLOAD if HOME_PATH_DOWNLOAD else "~/Downloads"
            )
            nom_fichier = os.path.join(path_download, os.path.basename(lien))
            with requests.get(lien, stream=True) as r:
                r.raise_for_status()
                with open(nom_fichier, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Téléchargement réussi: {lien}")

        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du téléchargement de {lien}: {e}")
            urls_echec.append(lien)

    return urls_echec


if __name__ == "__main__":
    if DEFAULT_URL:
        url_a_analyser = DEFAULT_URL
    else:
        url_a_analyser = input("Entrez l'URL de la page web: ")
    urls_echec = telecharger_liens(url_a_analyser)

    if urls_echec:
        print("\nListe des URLs non téléchargées:")
        for url in urls_echec:
            print(url)
    else:
        print("\nTous les téléchargements ont réussi!")
