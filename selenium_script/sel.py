#!/usr/bin/env python3
import sys
import argparse

from selenium.common import TimeoutException

import web_login
import selenium_lib
import time

from randomwordfr import RandomWordFr

from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains


def run(config, selenium_tool):
    if not config.ore_test:
        return
    # Open new tab test another case
    selenium_tool.open_tab("localhost:8069")
    time.sleep(0.5)

    selenium_tool.start_record()
    if config.scenario == "create_clan":
        scenario_create_clan(config, selenium_tool)
    if config.scenario == "join_new_clan":
        scenario_join_new_clan(config, selenium_tool)


def scenario_join_new_clan(config, selenium_tool):
    # Click to Button label Crée ton clan
    selenium_tool.inject_cursor()
    selenium_tool.click_with_mouse_move(By.CLASS_NAME, "o_footer")
    # Wait new clan is created by notification, need to compare from last clan
    selenium_tool.wait_add_new_element_and_click(
        by=By.CLASS_NAME, value="container_explorer"
    )

    scenario_create_new_account_with_random_user(config, selenium_tool)

    # Join a clan
    selenium_tool.inject_cursor()
    selenium_tool.click_with_mouse_move(by=By.ID, value="btn_ask_join_clan")

    # Wait to be invited, the page will auto-refresh and the button dialog will appear
    selenium_tool.wait_new_element_and_click(
        by=By.ID, value="btn_start_clavardage_from_clan", inject_cursor=True
    )

    # Send a message before receive it
    selenium_tool.inject_cursor()
    new_element_chat = selenium_tool.wait_add_new_element(
        by=By.CLASS_NAME, value="chat_msg"
    )

    rw = RandomWordFr()
    dct_contain = rw.get()
    word_name = dct_contain.get("word")
    word_definition = dct_contain.get("definition").replace("\n", " ")
    msg = (
        f"Je voulais te partager le mot «{word_name}» que j'ai appris"
        f" aujourd'hui. {word_definition}"
    )

    selenium_tool.input_text_with_mouse_move(
        By.ID, "input_text_chat", msg, no_scroll=True
    )
    selenium_tool.click_with_mouse_move(
        By.CLASS_NAME,
        "fa-send",
        timeout=5,
        no_scroll=True,
    )


def scenario_create_clan(config, selenium_tool):
    # Click to Button label Crée ton clan
    selenium_tool.inject_cursor()
    selenium_tool.click_with_mouse_move(
        By.XPATH, "/html/body/div[1]/main/div/section[3]/div/div/div[2]/div/a"
    )

    scenario_create_new_account_with_random_user(config, selenium_tool)

    # Création du clan
    # Préparation des informations
    rw = RandomWordFr()
    dct_contain = rw.get()
    club_name = dct_contain.get("word")
    club_name_description = dct_contain.get("definition")
    dct_contain = rw.get()
    club_city_name = dct_contain.get("word")
    dct_contain = rw.get()
    institution = dct_contain.get("word")

    # Fill clan_name
    no_scroll = True
    # TODO try to use execute_script to fill text
    #  The problem occur when fill text, scroll change
    if not no_scroll:
        selenium_tool.inject_cursor()

    viewport_ele_by = By.CLASS_NAME
    viewport_ele_value = "buttons_form_container"
    selenium_tool.input_text_with_mouse_move(
        By.NAME,
        "clan_name",
        f"Club de {club_name}",
        no_scroll=no_scroll,
        viewport_ele_by=viewport_ele_by,
        viewport_ele_value=viewport_ele_value,
    )

    # Fill clan_description
    selenium_tool.input_text_with_mouse_move(
        By.XPATH,
        "/html/body/div[1]/main/div/div/section/div[2]/div[1]/textarea[1]",
        f"Définition de {club_name} : {club_name_description}",
        no_scroll=no_scroll,
        viewport_ele_by=viewport_ele_by,
        viewport_ele_value=viewport_ele_value,
    )

    # Fill clan_besoin
    selenium_tool.input_text_with_mouse_move(
        By.XPATH,
        "/html/body/div[1]/main/div/div/section/div[2]/div[1]/textarea[2]",
        f"Créer des liens sur un sujet aléatoire.",
        no_scroll=no_scroll,
        viewport_ele_by=viewport_ele_by,
        viewport_ele_value=viewport_ele_value,
    )

    # Fill clan_ville_region
    selenium_tool.input_text_with_mouse_move(
        By.NAME,
        "clan_ville_region",
        f"Ville de {club_city_name}",
        no_scroll=no_scroll,
        viewport_ele_by=viewport_ele_by,
        viewport_ele_value=viewport_ele_value,
    )

    # Fill Nom d'un organisation
    selenium_tool.input_text_with_mouse_move(
        By.NAME,
        "clan_organisation",
        f"{institution}",
        no_scroll=no_scroll,
        viewport_ele_by=viewport_ele_by,
        viewport_ele_value=viewport_ele_value,
    )

    # Fill clan_besoin
    selenium_tool.input_text_with_mouse_move(
        By.XPATH,
        "/html/body/div[1]/main/div/div/section/div[2]/div[1]/textarea[3]",
        f"Autodidacte\nPerformance\nCréation de lien humain",
        no_scroll=no_scroll,
        viewport_ele_by=viewport_ele_by,
        viewport_ele_value=viewport_ele_value,
    )

    # Créer clan
    selenium_tool.click_with_mouse_move(
        By.ID,
        "submitBtn",
        no_scroll=no_scroll,
        viewport_ele_by=viewport_ele_by,
        viewport_ele_value=viewport_ele_value,
    )

    # Force refresh angularjs
    # Move mouse on same button
    # If window didn't open, move mouse to another button
    clan_button_xpath = "/html/body/div[1]/main/div/div/div[2]/div/div/a[1]"
    hoverable = selenium_tool.driver.find_element(By.ID, "submitBtn")
    ActionChains(selenium_tool.driver).move_to_element(hoverable).perform()
    try:
        selenium_tool.get_element(By.XPATH, clan_button_xpath, timeout=5)
    except TimeoutException:
        hoverable = selenium_tool.driver.find_element(By.ID, "prevBtn")
        ActionChains(selenium_tool.driver).move_to_element(hoverable).perform()

    # Configure clan button
    selenium_tool.click_with_mouse_move(
        By.XPATH,
        clan_button_xpath,
        timeout=5,
        no_scroll=True,
    )

    # Wait notification about adhesion clan and accept it
    selenium_tool.inject_cursor()
    selenium_tool.wait_increment_number_text_and_click(
        by=By.ID, value="badge_notification_all_count"
    )
    selenium_tool.click_with_mouse_move(
        By.ID,
        "BtnTabNotifications",
        timeout=5,
        no_scroll=True,
    )
    all_url_link = selenium_tool.get_all_element(
        By.NAME, "url_link_notification", timeout=5
    )

    first_link = all_url_link[0]
    # Extract name
    extract_text_link = first_link.text
    first_char = extract_text_link.find("«")
    second_char = extract_text_link.find("»")
    extract_user_name_link = extract_text_link[first_char + 1 : second_char]

    selenium_tool.click_with_mouse_move(element=first_link)

    selenium_tool.inject_cursor()
    all_button_accept = selenium_tool.get_all_element(
        By.NAME, "btn_accept_membre_demande_adhesion_clan", timeout=5
    )

    for button_ele in all_button_accept:
        selenium_tool.click_with_mouse_move(element=button_ele)

    # Time to chat with it
    selenium_tool.inject_cursor()
    selenium_tool.click_with_mouse_move(
        by=By.ID, value="sub_menu_communaute_clan"
    )

    selenium_tool.inject_cursor()
    selenium_tool.click_with_mouse_move(
        by=By.ID, value="btn_start_clavardage_from_clan"
    )

    selenium_tool.inject_cursor()
    selenium_tool.input_text_with_mouse_move(
        By.ID,
        "input_text_chat",
        "Nous avons notre premier nouveau membre, bienvenue"
        f" {extract_user_name_link}!",
        no_scroll=no_scroll,
    )
    selenium_tool.click_with_mouse_move(
        By.CLASS_NAME,
        "fa-send",
        timeout=5,
        no_scroll=True,
    )

    new_element_chat = selenium_tool.wait_add_new_element(
        by=By.CLASS_NAME, value="chat_msg"
    )

    rw = RandomWordFr()
    dct_contain = rw.get()
    word_name = dct_contain.get("word")
    word_definition = dct_contain.get("definition").replace("\n", " ")
    msg = f"Et moi, le mot «{word_name}» - {word_definition}"

    selenium_tool.input_text_with_mouse_move(
        By.ID, "input_text_chat", msg, no_scroll=no_scroll
    )
    selenium_tool.click_with_mouse_move(
        By.CLASS_NAME,
        "fa-send",
        timeout=5,
        no_scroll=True,
    )

    # end


def scenario_create_new_account_with_random_user(config, selenium_tool):
    def action_before():
        selenium_tool.click_with_mouse_move(By.NAME, "accept_global_policy")

    selenium_tool.scenario_create_new_account_with_random_user(
        show_cursor=True, def_action_before_submit=action_before
    )


def fill_parser(parser):
    ore_group = parser.add_argument_group(title="ORE execution")
    ore_group.add_argument(
        "--ore_test",
        action="store_true",
        help="ore test",
    )
    ore_group.add_argument(
        "--scenario",
        default="create_clan",
        help="Scenario to run",
    )


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""Selenium script to open web browser to ERPLibre adapted for ORE.""",
    )
    # Generate parser
    selenium_lib.fill_parser(parser)
    web_login.fill_parser(parser)
    fill_parser(parser)
    args = parser.parse_args()
    web_login.compute_args(args)
    # Instance selenium tool
    selenium_tool = selenium_lib.SeleniumLib(args)
    selenium_tool.configure()
    # Execute
    web_login.run(args, selenium_tool)
    run(args, selenium_tool)
    selenium_tool.stop_record()
    return 0


if __name__ == "__main__":
    sys.exit(main())