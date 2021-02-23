import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


def driver_setup():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    return driver


def get_urls(total_urls=1):
    # Extrae urls de quejas de apestan.com
    # total_urls: cantidad de urls que se desea extraer

    driver = driver_setup()
    main_url = "https://www.apestan.com/countries/countryid_10"
    driver.get(main_url)

    urls = []
    count = 0
    while count < total_urls:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "content"))
        )

        for a in driver.find_elements_by_xpath('//div[@class="heading-4"]/a'):
            urls.append(a.get_attribute("href"))

        driver.execute_script("window.scrollTo(30, document.body.scrollHeight);")

        try:
            driver.find_element_by_xpath('//a[@class="hidden-xs_inline last"]').click()
        except NoSuchElementException:
            break

    driver.quit()

    if len(urls) > total_urls:
        residual_urls = len(urls) - total_urls
        urls = urls[: len(urls) - residual_urls]

    return urls


def get_comments(url_to_extract):
    # Extrae el texto de una queja de apestan.com
    # url_to_extract: solicita una url de Apestan, ejemplo: https://www.apestan.com/cases/liderlogo-maracaibo-zulia-venezuela_97230.html

    driver = driver_setup()
    driver.get(url_to_extract)

    try:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "content"))
        )
    except TimeoutException:
        return None

    for span in driver.find_elements_by_xpath('//div[@class="text-block"]/span[1]'):
        return span.text


def scrap_apestan(total_comments):
    # Extracción completa, urls + comentarios
    # total_comments: cantidad de comentarios que se desea extraer

    print("\nSearching urls...")

    list_of_urls = get_urls(total_comments)

    with open("apestan_urls.txt", "w") as f:
        for urls in list_of_urls:
            f.write("%s\n" % urls)

    print("\nThe urls were saved as apestan_urls.txt\n")
    print("Initializing comment extraction...")

    url_num = 0
    url_error = []
    comments = []
    for url in list_of_urls:
        url_comments = get_comments(url)
        if url_comments is None:
            url_num += 1
            url_error.append(url_num)
            print("\nThere was a problem with url", url_num)
            print(url, "\n")
        else:
            comments.append(url_comments)
            url_num += 1
            print("\nUrl", url_num, "extracted")

    print("\nDone")
    print("The urls", url_error, "could not be extracted")
    print("Total comments extracted:", len(comments))

    return comments


def main():
    comments = scrap_apestan(200)
    comments_df = pd.DataFrame(data=comments, columns=["Comment"])
    comments_df.to_csv("./apestan_neg_data_2.csv", index=False)


x = get_urls(1)
print(x)