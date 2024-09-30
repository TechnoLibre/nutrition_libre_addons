from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Initialiser le pilote pour Firefox
try:
    driver_firefox = webdriver.Firefox()
    # Ouvrir une page web (par exemple, Google) avec Firefox
    driver_firefox.get("https://www.google.com")
    
    # Effectuer une recherche (par exemple, "Selenium Python") avec Firefox
    search_box_firefox = driver_firefox.find_element(By.NAME, "q")
    search_box_firefox.send_keys("Selenium Python")
    search_box_firefox.send_keys(Keys.RETURN)
    
    # Attendre et fermer le navigateur Firefox
    time.sleep(5)
    driver_firefox.quit()
except Exception as e:
    print(f"Erreur lors de l'exécution avec Firefox : {e}")

# Initialiser le pilote pour Chrome
try:
    driver_chrome = webdriver.Chrome()
    # Ouvrir une page web (par exemple, Google) avec Chrome
    driver_chrome.get("https://www.google.com")
    
    # Effectuer une recherche (par exemple, "Selenium Python") avec Chrome
    search_box_chrome = driver_chrome.find_element(By.NAME, "q")
    search_box_chrome.send_keys("Selenium Python")
    search_box_chrome.send_keys(Keys.RETURN)
    
    # Attendre et fermer le navigateur Chrome
    time.sleep(5)
    driver_chrome.quit()
except Exception as e:
    print(f"Erreur lors de l'exécution avec Chrome : {e}")
