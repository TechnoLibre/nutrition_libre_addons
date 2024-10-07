import asyncio
import aiohttp
import os
import requests
from bs4 import BeautifulSoup

DEFAULT_URL = ""
HOME_PATH_DOWNLOAD = ""


async def telecharger_fichier(session, url, nom_fichier, url_missing):
    """Télécharge un fichier à partir d'une URL."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            with open(nom_fichier, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)
        print(f"Téléchargement réussi: {url}")
    except aiohttp.ClientError as e:
        url_missing.append(url)
        print(f"Erreur lors de l'accès à l'URL {url}: {e}")


async def telecharger_liens(url):
    """
    Télécharge tous les fichiers liés à partir des balises <a href=...> d'une page web
    en utilisant asyncio.

    Args:
      url: L'URL de la page web à analyser.

    Returns:
      Une liste des URLs qui n'ont pas pu être téléchargées.
    """
    urls_echec = []
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            response.raise_for_status()

            # Essayer de détecter l'encodage automatiquement
            encodage = (
                response.charset or "UTF-16LE"
            )  # Utiliser latin-1 comme solution de repli

            try:
                soup = BeautifulSoup(
                    await response.text(encoding=encodage), "html.parser"
                )
            except UnicodeDecodeError:
                print(
                    f"Erreur de décodage pour {url}. Essayer avec 'latin-1' ou 'utf-8'"
                )
                try:
                    soup = BeautifulSoup(
                        await response.text(encoding="latin-1"), "html.parser"
                    )
                    # soup = BeautifulSoup(await response.text(encoding="utf-8"), "html.parser")
                except UnicodeDecodeError as e:
                    print(f"Erreur de décodage pour {url}: {e}")
                    urls_echec.append(url)
                    return urls_echec
            liens = [a["href"] for a in soup.find_all("a", href=True)]

            tasks = []
            for lien in liens:
                try:
                    path_download = (
                        HOME_PATH_DOWNLOAD
                        if HOME_PATH_DOWNLOAD
                        else "~/Downloads"
                    )
                    nom_fichier = os.path.join(
                        path_download, os.path.basename(lien)
                    )
                    tasks.append(
                        telecharger_fichier(
                            session, lien, nom_fichier, urls_echec
                        )
                    )
                except Exception as e:
                    print(
                        f"Erreur lors de la création de la tâche pour {lien}: {e}"
                    )
                    urls_echec.append(lien)

            await asyncio.gather(*tasks)

    except aiohttp.ClientError as e:
        print(f"Erreur d'execution: {e}")

    return urls_echec


if __name__ == "__main__":
    if DEFAULT_URL:
        url_a_analyser = DEFAULT_URL
    else:
        url_a_analyser = input("Entrez l'URL de la page web: ")
    urls_echec = asyncio.run(telecharger_liens(url_a_analyser))

    if urls_echec:
        print("\nListe des URLs non téléchargées:")
        for url in urls_echec:
            print(url)
    else:
        print("\nTous les téléchargements ont réussi!")
