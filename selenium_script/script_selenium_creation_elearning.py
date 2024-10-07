from lib2to3.pgen2 import driver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def wait_and_sleep(seconds=2):
    time.sleep(seconds)

def select_database(driver, db_name):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "o_database_list"))
        )
        wait_and_sleep()
        
        db_elements = driver.find_elements(By.CLASS_NAME, "list-group-item")
        
        for element in db_elements:
            if db_name in element.text:
                element.click()
                wait_and_sleep()
                print(f"Base de données '{db_name}' sélectionnée")
                return True
        
        print(f"Base de données '{db_name}' non trouvée")
        return False
    except Exception as e:
        print(f"Erreur lors de la sélection de la base de données : {str(e)}")
        return False

def login(driver, username, password):
    try:
        wait_and_sleep(5)  # Attendre un peu plus longtemps pour le chargement de la page
        
        # Trouver et remplir le champ username
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login"))
        )
        username_field.clear()
        username_field.send_keys(username)
        wait_and_sleep()
        
        # Trouver et remplir le champ password
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_field.clear()
        password_field.send_keys(password)
        wait_and_sleep()
        
        # Trouver et cliquer sur le bouton de connexion
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        wait_and_sleep(5)  # Attendre le chargement après la connexion
        
        print("Tentative de connexion effectuée")
        return True
    except Exception as e:
        print(f"Erreur lors de la connexion : {str(e)}")
        return False

def check_login_success(driver):
    try:
        # Vérifier si nous sommes sur la page de discussion
        WebDriverWait(driver, 10).until(
            EC.title_contains("Odoo - Discussion")
        )
        print("Connexion confirmée, sur la page de discussion")
        return True
    except Exception as e:
        print(f"Erreur lors de la vérification de la connexion : {str(e)}")
        return False

# def navigate_to_elearning(driver):
#     try:
#         # Attendre que le menu hamburger soit chargé
#         hamburger_menu = WebDriverWait(driver, 20).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, ".o_navbar_apps_menu .dropdown-toggle"))
#         )
#         print("Menu hamburger trouvé")

#         # Cliquer sur le menu hamburger
#         hamburger_menu.click()
#         print("Menu hamburger cliqué")

#         # Attendre que le menu déroulant s'ouvre
#         WebDriverWait(driver, 10).until(
#             EC.visibility_of_element_located((By.CSS_SELECTOR, ".o-dropdown--menu"))
#         )
#         print("Menu déroulant ouvert")

#         # Trouver et cliquer sur l'option eLearning
#         elearning_option = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'website_slides.website_slides_menu_root')]"))
#         )
#         driver.execute_script("arguments[0].click();", elearning_option)
#         print("Option eLearning cliquée")

#         # Attendre que la page eLearning se charge
#         WebDriverWait(driver, 20).until(
#             EC.url_contains("website_slides")
#         )
#         print("Page eLearning chargée")

#         # Vérifier si nous sommes sur la bonne page
#         if "website_slides" not in driver.current_url:
#             print("Redirection inattendue. Tentative de navigation manuelle vers eLearning.")
#             driver.get("http://localhost:8069/web#menu_id=299&action=469")  # Ajustez cette URL si nécessaire
#             WebDriverWait(driver, 20).until(
#                 EC.url_contains("website_slides")
#             )

#         # Imprimer l'URL et le titre actuels pour le débogage
#         print(f"URL actuelle après navigation : {driver.current_url}")
#         print(f"Titre de la page actuelle : {driver.title}")

#     except Exception as e:
#         print(f"Erreur lors de la navigation vers eLearning : {str(e)}")
#         print(f"URL actuelle : {driver.current_url}")
#         print(f"Titre de la page actuelle : {driver.title}")
    
#     # Capture d'écran pour le débogage
#     driver.save_screenshot("navigation_elearning.png")
def navigate_to_elearning(driver):
    try:
        # Cliquer sur le menu hamburger
        hamburger_menu = WebDriverWait(driver, 20).until(
           EC.element_to_be_clickable((By.CSS_SELECTOR, ".o_navbar_apps_menu .dropdown-toggle"))
        )
        driver.execute_script("arguments[0].click();", hamburger_menu)
        print("Menu hamburger cliqué")

        # Attendre que le menu déroulant s'ouvre
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".o-dropdown--menu"))
        )
        print("Menu déroulant ouvert")

        # Vérifier si l'option eLearning est présente
        elearning_options = driver.find_elements(By.XPATH, "//a[contains(@class, 'dropdown-item') and contains(text(), 'eLearning')]")
        
        if elearning_options:
            elearning_option = elearning_options[0]
            driver.execute_script("arguments[0].click();", elearning_option)
            print("Option eLearning cliquée")
        else:
            print("Option eLearning non trouvée dans le menu. Tentative de navigation directe.")
            # Essayez de naviguer directement vers l'URL eLearning
            driver.get("http://localhost:8069/web#menu_id=299&action=469")  # Ajustez cette URL si nécessaire
        
        # Attendre que la page eLearning se charge
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "o_content"))
        )
        print("Page eLearning chargée")

        # Vérifier si nous sommes sur la bonne page
        if "website_slides" in driver.current_url or "elearning" in driver.current_url.lower():
            print("Navigation vers eLearning réussie")
        else:
            print("La navigation vers eLearning a échoué. Vérifiez manuellement l'URL correcte.")

        print(f"URL actuelle après navigation : {driver.current_url}")
        print(f"Titre de la page actuelle : {driver.title}")

    except Exception as e:
        print(f"Erreur lors de la navigation vers eLearning : {str(e)}")
        print(f"URL actuelle : {driver.current_url}")
        print(f"Titre de la page actuelle : {driver.title}")
    
    driver.save_screenshot("navigation_elearning.png")


def create_elearning_course(driver):
    try:
        # Cliquer sur le bouton "Créer"
        create_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'o_list_button_add') or contains(@class, 'o-kanban-button-new')]"))
        )
        create_button.click()
        print("Cliqué sur le bouton Créer")

        # Attendre que le formulaire de création se charge
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "o_form_view"))
        )
        print("Formulaire de création chargé")

        # Remplir le formulaire du cours
        course_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        course_name.send_keys("Cours de test Selenium")
        print("Nom du cours saisi")

        description = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "description"))
        )
        description.send_keys("Ce cours a été créé automatiquement par un script Selenium.")
        print("Description du cours saisie")

        # Sauvegarder le cours
        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'o_form_button_save')]"))
        )
        save_button.click()
        print("Cours sauvegardé")

        # Attendre la confirmation de sauvegarde
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "o_form_saved"))
        )
        print("Cours eLearning créé avec succès")

    except Exception as e:
        print(f"Erreur lors de la création du cours eLearning : {str(e)}")
        print(f"URL actuelle : {driver.current_url}")
        print(f"Titre de la page : {driver.title}")

def main():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get("http://localhost:8069")
        wait_and_sleep()
        print(f"URL actuelle : {driver.current_url}")
        print(f"Titre de la page : {driver.title}")
        
        # Sélection de la base de données
        try:
            select_db = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "list-group-item"))
            )
            select_db.click()
            wait_and_sleep()
            print("Base de données 'nutrition_libre' sélectionnée")
        except Exception as e:
            print(f"Erreur lors de la sélection de la base de données : {str(e)}")
        
        # Tentative de connexion
        if login(driver, "admin", "admin"):
            if check_login_success(driver):
                print("Connecté avec succès")
                # Ici, vous pouvez ajouter le code pour naviguer vers eLearning et créer un cours
                navigate_to_elearning(driver)
                create_elearning_course(driver)
            else:
                print("La connexion semble avoir échoué ou la page attendue n'a pas été chargée")
        else:
            print("Échec de la connexion")
        
    except Exception as e:
        print(f"Une erreur générale s'est produite : {str(e)}")
    finally:
        wait_and_sleep()
        print(f"URL finale : {driver.current_url}")
        print(f"Titre final de la page : {driver.title}")
        driver.quit()

if __name__ == "__main__":
    main()