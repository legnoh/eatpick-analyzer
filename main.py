import logging, os, platform, time, yaml, csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By

log_format = '%(asctime)s[%(filename)s:%(lineno)d][%(levelname)s] %(message)s'
log_level = os.getenv("LOGLEVEL", logging.INFO)
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S%z', level=log_level)

SCROLL_PAUSE_TIME = 2

if __name__ == '__main__':

    logging.info("initializing chromium options...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-dev-shm-usage')

    if platform.system() == 'Linux':
        logging.info("initializing chromium...")
        driver = webdriver.Chrome(service=ChromiumService(), options=options)
    else:
        logging.info("initializing chrome...")
        driver = webdriver.Chrome(service=ChromeService(), options=options)
    driver.implicitly_wait(10)

    logging.info("loading config file...")
    with open('config.yml', 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    
    recipes = []
    
    for genre,appliance in config['kitchen-appliances'].items():
        driver.get(appliance['url'])

        # Scroll down to bottom
        # https://stackoverflow.com/a/27760083
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # get all recipes
        recipes_html = driver.find_elements(By.CSS_SELECTOR, "li.p-postList__item > div.c-card")

        for recipe in recipes_html:
            link = recipe.find_element(By.CSS_SELECTOR, "a").get_attribute('href').split('?')[0]
            id = link.replace("https://www.eatpick.com/recipe/group-detail/", "")
            title = recipe.find_element(By.CSS_SELECTOR, "div.c-card__body > h3.c-card__title > a").text.strip()
            desc = recipe.find_element(By.CSS_SELECTOR, "div.c-card__body > p.c-card__excerpt").text.strip()
            view = recipe.find_element(By.CSS_SELECTOR, "div.c-card__body > div.c-card__footer > p.c-card__view > span.c-card__number").text.strip()

            logging.info("[{genre}] {title} : {url}".format(genre=genre, title=title, url=link))

            recipes.append({
                "id": id,
                "genre": genre,
                "title": title,
                "view": view,
                "desc": desc,
                "link": link,
            })
    
    # write to csv
    with open('recipes.csv', 'w') as f:
        writer = csv.DictWriter(f, ["id", "genre", "title", "view", "desc", "link"])
        writer.writeheader()
        writer.writerows(recipes)
