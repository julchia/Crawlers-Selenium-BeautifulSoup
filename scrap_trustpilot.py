import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException


def driver_setup():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    return driver


def scrap_trust(url_to_extract, total_comments=1):
    # Extrae comentarios de una url de un negocio asociado a trustpilot.com
    # url_to_extract: solicita una url de TrustPilot, ejemplo: https://es.trustpilot.com/review/ivisa.com?page=1
    # total_comments: cantidad de comentarios que busca por url

    driver = driver_setup()
    try:
        driver.get(url_to_extract)
    except Exception:
        return None

    comments = []
    count = 0
    next_page = 1
    while count < total_comments:
        html = driver.page_source.encode("utf-8").strip()
        soup = BeautifulSoup(html, "html.parser")

        try:
            for i in soup.find_all("a", {"class": "link link--large link--dark"}):
                comments.append(i.get_text().strip())
                count += 1
        except NoSuchElementException:
            pass

        try:
            for i in soup.find_all("p", {"class": "review-content__text"}):
                comments.append(i.get_text().strip())
        except NoSuchElementException:
            pass

        next_page += 1
        next_url = re.sub(r"(?<=page=)(\d+)", str(next_page), url_to_extract)
        if next_url == "https://es.trustpilot.com/review/mrw.es":
            break
        else:
            driver.get(next_url)

    if len(comments) > total_comments:
        residual_comments = len(comments) - total_comments
        comments = comments[: len(comments) - residual_comments]

    return comments


def main():

    list_of_urls = [
        "https://es.trustpilot.com/review/ivisa.com?page=1&stars=5",
        "https://es.trustpilot.com/review/westwing.es?page=1&stars=5",
        "https://es.trustpilot.com/review/mobilerecharge.com?page=1&stars=5",
        "https://es.trustpilot.com/review/www.mielectro.es?page=1&stars=5",
        "https://es.trustpilot.com/review/www.packlink.es?page=1&stars=5",
        "https://es.trustpilot.com/review/www.cabreramedina.com/es?page=1&stars=5",
        "https://es.trustpilot.com/review/wiberrentacar.com?page=1&stars=5",
        "https://es.trustpilot.com/review/doyouspain.com?page=1&stars=5",
        "https://es.trustpilot.com/review/www.wish.com?page=1&stars=5",
        "https://es.trustpilot.com/review/trustpilot.com?page=1&stars=5",
        "https://es.trustpilot.com/review/latostadora.com?page=1&stars=5",
        "https://es.trustpilot.com/review/twothirds.com?page=1&stars=5",
        "https://es.trustpilot.com/review/www.flashbay.es?page=1&stars=5",
        "https://es.trustpilot.com/review/xtralife.com?page=1&stars=5",
    ]

    url_num = 0
    url_error = []
    comments = []
    for url in list_of_urls:
        url_comments = scrap_trust(url, 800)
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

    comments_df = pd.DataFrame(data=comments, columns=["Comment"])
    comments_df.to_csv("./trustpilot_pos_data_1.csv", index=False)
