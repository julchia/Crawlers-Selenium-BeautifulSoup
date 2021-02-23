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
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
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
    # Extrae urls de reviews de restaurantes de trustpilot.com
    # total_urls: cantidad de urls que se desea extraer

    driver = driver_setup()
    main_url = "https://www.tripadvisor.com.ar/Search?q=argentina&searchSessionId=1C39B74AFFBCBBD2D4CE1B168C6D53D21595425856331ssid&searchNearby=false&geo=312741&sid=026D431B7842AEB8CC1F3263CE7156EC1595439773315&blockRedirect=true&rf=6&ssrc=e"
    driver.get(main_url)

    urls = []
    count = 0
    while count < total_urls:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//div[@class="ui_columns sections_wrapper"]')
            )
        )

        for a in driver.find_elements_by_css_selector(".review_count"):
            urls.append(a.get_attribute("href"))
            count += 1

        try:
            driver.find_element_by_xpath(
                '//*[@id="BODY_BLOCK_JQUERY_REFLOW"]/div[2]/div/div[2]/div/div/div/div/div[1]/div/div[1]/div/div[3]/div/div[2]/div/div/div/a[2]'
            ).click()
        except NoSuchElementException:
            break

    driver.quit()

    if len(urls) > total_urls:
        residual_urls = len(urls) - total_urls
        urls = urls[: len(urls) - residual_urls]

    return urls


def get_comments(url_to_extract, total_comments=1, polarity="default"):
    # Extrae comentarios de una url de un negocio asociado a tripadvisor.com.ar
    # url_to_extract: solicita una url de TripAdvisor, ejemplo: https://www.tripadvisor.com.ar/Restaurant_Review-g312741-d1066728-Reviews-Don_Julio-Buenos_Aires_Capital_Federal_District.html#REVIEWS
    # total_comments: cantidad de comentarios que se desea extraer por url
    # polarity: 'default' sigue el orden de la url, 'pos' para positivos, 'neg' para negativos

    driver = driver_setup()
    driver.get(url_to_extract)

    try:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "taplc_detail_filters_rr_resp_0"))
        )
    except TimeoutException:
        return None

    try:
        if polarity == "pos":
            driver.find_element_by_css_selector(
                "#filters_detail_checkbox_trating__5+ .label"
            ).click()
        elif polarity == "neg":
            driver.find_element_by_css_selector(
                "#filters_detail_checkbox_trating__1+ .label"
            ).click()
            time.sleep(3)
            driver.find_element_by_css_selector(
                "#filters_detail_checkbox_trating__2+ .label"
            ).click()
    except StaleElementReferenceException:
        return None
    except ElementClickInterceptedException:
        return None
    except NoSuchElementException:
        return None

    comments = []
    count = 0
    while count < total_comments:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.ID, "taplc_location_reviews_list_resp_rr_resp_0")
            )
        )
        time.sleep(5)

        try:
            driver.find_element_by_xpath(
                '//span[@class="taLnk ulBlueLinks"]'
            ).click()  # Click on "Más"
        except StaleElementReferenceException:
            pass
        except ElementClickInterceptedException:
            pass
        except NoSuchElementException:
            pass

        html = driver.page_source.encode("utf-8").strip()
        soup = BeautifulSoup(html, "html.parser")

        for i in soup.find_all("p", {"class": "partial_entry"}):
            comments.append(i.get_text().strip())
            count += 1

        try:
            driver.find_element_by_css_selector(".ui_pagination .primary").click()
        except StaleElementReferenceException:
            break
        except ElementClickInterceptedException:
            break
        except NoSuchElementException:
            break

    driver.quit()

    if len(comments) > total_comments:
        residual_comments = len(comments) - total_comments
        comments = comments[: len(comments) - residual_comments]

    return comments


def scrap_trip(total_urls, total_comments, polarity="default"):
    # Extracción completa, urls + comentarios
    # total_urls: cantidad de urls que se desea obtener
    # total_comments: cantindad de comentarios que se desea extraer por url
    # polarity: 'default' sigue el orden de la url, 'pos' para positivos, 'neg' para negativos

    print("\nSearching urls...")

    list_of_urls = get_urls(total_urls)

    with open("tripadvisor_urls.txt", "w") as f:
        for urls in list_of_urls:
            f.write("%s\n" % urls)

    print("\nThe urls were saved as tripadvisor_urls.txt\n")
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
    comments = scrap_trip(75, 50, "neg")
    comments_df = pd.DataFrame(data=comments, columns=["Comment"])
    comments_df.to_csv("./tripadvisor_neg_data_2.csv", index=False)
