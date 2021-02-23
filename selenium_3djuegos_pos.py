import time
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException


def get_3djuegos_comments(number_of_pages=1):
    # Extrae 25 reviews de videojuegos de 3djuegos.com
    # number_of_pages: cantidad de páginas que se desea extraer, extrae 25 reviews por página

    driver.get(
        "https://www.3djuegos.com/novedades/juegos-generos/juegos-pc/0f1f0f0/mejor-valorados/"
    )

    comments = []
    page = 0
    while page < number_of_pages:

        time.sleep(3)

        html = driver.page_source.encode("utf-8").strip()
        soup = BeautifulSoup(html, "html.parser")

        for i in soup.find_all("p", {"class": "mar_t3 mar_b5 c5"}):
            comments.append(i.get_text().strip())

        page += 1
        print("Page:", page)

        try:
            driver.find_element_by_css_selector(".wi100+ .vat .nw").click()
        except NoSuchElementException:
            pass

    return comments