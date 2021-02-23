import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import time


def driver_setup():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    return driver


def get_urls(total_urls=1):
    # Extrae urls de reviews de restaurantes de pedidosya.com
    # total_urls: cantidad de urls que se desea extraer

    driver = driver_setup()
    main_url = "https://www.pedidosya.com.ar/"
    driver.get(main_url)

    driver.find_element_by_css_selector(
        ".top_cities li:nth-child(1) a"
    ).click()  # Click on "Top ciudades > Buenos Aires"

    urls = []
    count = 0
    while count < total_urls:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "resultListContainer"))
        )

        for a in driver.find_elements_by_xpath("//h3/a"):
            urls.append(a.get_attribute("href"))
            count += 1

        try:
            driver.find_element_by_xpath('//li[@class="arrow next"]').click()
        except NoSuchElementException:
            break

    driver.quit()

    if len(urls) > total_urls:
        residual_urls = len(urls) - total_urls
        urls = urls[: len(urls) - residual_urls]

    return urls


def get_comments(url_to_extract, total_comments=1, polarity="default"):
    # Extrae comentarios de una url de un negocio asociado a pedidosya.com.ar
    # url_to_extract: solicita una url de PedidosYa, ejemplo: https://www.pedidosya.com.ar/restaurantes/buenos-aires/la-farola-de-cabildo-menu
    # total_comments: cantidad de comentarios que busca por url
    # polarity: 'default' sigue el orden de la url, 'pos' para positivos, 'neg' para negativos

    driver = driver_setup()
    driver.get(url_to_extract)

    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "profileContainer"))
    )

    try:
        driver.find_element_by_css_selector(".active~ button+ button").click()
    except NoSuchElementException:
        return None

    if polarity == "pos":
        Select(driver.find_element_by_css_selector("#orderBy")).select_by_visible_text(
            "Puntuación de mayor a menor"
        )
    elif polarity == "neg":
        Select(driver.find_element_by_css_selector("#orderBy")).select_by_visible_text(
            "Puntuación de menor a mayor"
        )

    comments = []
    count = 0
    while count < total_comments:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "reviewList"))
        )

        html = driver.page_source.encode("utf-8").strip()
        soup = BeautifulSoup(html, "html.parser")

        for i in soup.find_all("p", {"itemprop": "description"}):
            comments.append(i.get_text().strip())
            count += 1

        try:
            driver.find_element_by_xpath('//li[@class="arrow next"]').click()
        except NoSuchElementException:
            break

    driver.quit()

    if len(comments) > total_comments:
        residual_comments = len(comments) - total_comments
        comments = comments[: len(comments) - residual_comments]

    return comments


def scrap_pedidos(total_urls, total_comments, polarity="default"):
    # Extracción completa, urls + comentarios
    # total_urls: cantidad de urls que se desea obtener
    # total_comments: cantindad de comentarios que busca por url
    # polarity: 'default' sigue el orden de la url, 'pos' para positivos, 'neg' para negativos

    print("\nSearching urls...")

    list_of_urls = get_urls(total_urls)

    with open("pedidosya_urls.txt", "w") as f:
        for urls in list_of_urls:
            f.write("%s\n" % urls)

    print("\nThe urls were saved as pedidosya_urls.txt\n")
    print("Initializing comment extraction...")

    url_num = 0
    url_error = []
    comments = []
    for url in list_of_urls:
        url_comments = get_comments(url, total_comments, polarity)
        if url_comments is None:
            url_num += 1
            url_error.append(url_num)
            print("\nThere was a problem with url", url_num)
            print(url, "\n")
        else:
            comments.extend(url_comments)
            url_num += 1
            print("\nUrl", url_num, "extracted")

    print("\nDone")
    print("The urls", url_error, "could not be extracted")
    print("Total comments extracted:", len(comments))

    return comments


def main():
    comments = scrap_pedidos(100, 50, "neg")
    comments_df = pd.DataFrame(data=comments, columns=["Comment"])
    comments_df.to_csv("./pedidosya_neg_data.csv", index=False)
