# Installation
# pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

from collections import defaultdict
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import sys
import json

SERVICE_ACCOUNT_FILE = "./credentials.json"
DATA_JSON_OUTPUT = "./data.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
FORCE_ENABLE_SHARE = False

# Remplacez par le chemin vers votre fichier de clés de compte de service
FOLDER_ID = ""

if not os.path.isfile(SERVICE_ACCOUNT_FILE):
    print(f"Error, missing file '{SERVICE_ACCOUNT_FILE}'")
    sys.exit(1)

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("drive", "v3", credentials=creds)


def list_files_and_share(folder_id):
    """Liste les fichiers d'un dossier Google Drive et les partage publiquement.

    Args:
      folder_id: L'ID du dossier Google Drive.

    Returns:
      Une liste de tuples (nom du fichier, URL).
    """

    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents",
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )
    # Or all folder from this user
    # results = (
    #     service.files()
    #     .list(
    #         q="mimeType='application/vnd.google-apps.folder'",
    #         fields="nextPageToken, files(id, name)",
    #     )
    #     .execute()
    # )
    repertoires = results.get("files", [])

    if not repertoires:
        print("Aucun répertoire trouvé.")
        return []

    lst_empty_courses = []
    lst_courses_one_note = []
    lst_courses_small_note = []
    dct_courses_info = defaultdict(dict)
    files_with_urls = []
    for item in repertoires:
        rep_name = item["name"]
        id_repertoire = item["id"]
        if not rep_name[:3].isdigit():
            print(f"Répertoire ignoré: {rep_name}, ID: {id_repertoire}")
            continue
        print(f"Répertoire trouvé: {rep_name}, ID: {id_repertoire}")

        results = (
            service.files()
            .list(
                q=f"'{id_repertoire}' in parents",
                fields="nextPageToken, files(id, name)",
            )
            .execute()
        )
        fichiers = results.get("files", [])
        dct_course_info = {"note": "", "courses": {}}
        if len(fichiers) == 0:
            lst_empty_courses.append(rep_name)
            fichiers = []
        elif len(fichiers) == 1 and fichiers[0]["name"] == "note":
            lst_courses_one_note.append(rep_name)
            # request = service.files().export_media(fileId=fichiers[0]['id'], mimeType='text/plain')
            # contenu_fichier = request.execute().decode('utf-8')
            # print(contenu_fichier.strip())
            fichiers = []
        else:
            dct_courses_info[rep_name] = dct_course_info
        for fichier in fichiers:
            id_fichier = fichier.get("id")
            name_fichier = fichier.get("name")
            if name_fichier == "note":
                request = service.files().export_media(
                    fileId=id_fichier, mimeType="text/plain"
                )
                contenu_fichier = request.execute().decode("utf-8")
                if len(contenu_fichier) < 50:
                    lst_courses_small_note.append(rep_name)
                else:
                    dct_course_info["note"] = contenu_fichier
            # Définir les autorisations de partage public
            if FORCE_ENABLE_SHARE:
                public_permission = {"type": "anyone", "role": "reader"}
                service.permissions().create(
                    fileId=id_fichier, body=public_permission
                ).execute()

            # Obtenir l'URL publique du fichier
            file_link = (
                service.files()
                .get(fileId=id_fichier, fields="webViewLink")
                .execute()
            )
            link = file_link["webViewLink"]
            files_with_urls.append(link)
            dct_course_info.get("courses")[name_fichier] = link

    # lst_courses_one_note
    # dct_courses_info
    with open(DATA_JSON_OUTPUT, "w") as f:
        json.dump(dct_courses_info, f)
    return files_with_urls


if __name__ == "__main__":
    # Remplacez par l'ID du dossier Google Drive que vous souhaitez parcourir
    files_with_urls = list_files_and_share(FOLDER_ID)
    for name, url in files_with_urls:
        print(f"{name}: {url}")
