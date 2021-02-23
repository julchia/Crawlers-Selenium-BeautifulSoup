import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
)


def driver_setup():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    return driver


def get_urls(total_urls=1):
    # Extrae urls de reviews de series de sansacine.com
    # total_urls: cantidad de urls que se desea extraer

    driver = driver_setup()
    main_url = "http://www.sensacine.com/series-tv/nota-espectadores/?page=12"
    driver.get(main_url)

    urls = []
    count = 0
    while count < total_urls:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//div[@class="gd-col-middle"]')
            )
        )

        for a in driver.find_elements_by_xpath(
            '//div[@class="rating-item-content"]/a[text()=" Usuarios "]'
        ):
            urls.append(a.get_attribute("href"))
            count += 1

        try:
            driver.find_element_by_xpath(
                '//nav[@class="pagination cf"]/a[@class="xXx button button-md button-primary-full button-right"]'
            ).click()
        except NoSuchElementException:
            break

    driver.quit()

    if len(urls) > total_urls:
        residual_urls = len(urls) - total_urls
        urls = urls[: len(urls) - residual_urls]

    return urls


def get_comments(url_to_extract, total_comments=1, polarity="default"):
    # Extrae comentarios de una serie de sansacine.com
    # url_to_extract: solicita una url de SansaCine, ejemplo: http://www.sensacine.com/series/serie-7157/criticas/
    # total_comments: cantidad de comentarios que se desea extraer por url
    # polarity: 'default' sigue el orden de la url, 'pos' para positivos, 'neg' para negativos

    driver = driver_setup()
    driver.get(url_to_extract)

    try:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@class="gd-col-left"]'))
        )
    except TimeoutException:
        return None

    try:
        if polarity == "pos":
            driver.find_element_by_css_selector(".title+ .item").click()
        elif polarity == "neg":
            driver.find_element_by_css_selector(".item:nth-child(7) .nb").click()
    except ElementClickInterceptedException:
        return None
    except NoSuchElementException:
        return None

    comments = []
    count = 0
    while count < total_comments:
        html = driver.page_source.encode("utf-8").strip()
        soup = BeautifulSoup(html, "html.parser")

        for i in soup.find_all("div", {"class": "content-txt review-card-content"}):
            comments.append(i.get_text().strip())
            count += 1

        try:
            driver.find_element_by_xpath(
                '//nav[@class="pagination cf"]/a[@class="xXx button button-md button-primary-full button-right"]'
            ).click()
        except NoSuchElementException:
            break

    driver.quit()

    if len(comments) > total_comments:
        residual_comments = len(comments) - total_comments
        comments = comments[: len(comments) - residual_comments]

    return comments


def scrap_sansa(total_urls, total_comments, polarity="default"):
    # Extracción completa, urls + comentarios
    # total_urls: cantidad de urls que se desea obtener
    # total_comments: cantindad de comentarios que se desea extraer por url
    # polarity: 'default' sigue el orden de la url, 'pos' para positivos, 'neg' para negativos

    print("\nSearching urls...")

    list_of_urls = get_urls(total_urls)

    with open("sansa_urls.txt", "w") as f:
        for urls in list_of_urls:
            f.write("%s\n" % urls)

    print("\nThe urls were saved as sansa_urls.txt\n")
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
    comments = scrap_sansa(150, 50, "neg")
    comments_df = pd.DataFrame(data=comments, columns=["Comment"])
    comments_df.to_csv("./sansa_neg_data_2.csv", index=False)
