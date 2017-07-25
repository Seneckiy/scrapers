import time
import os
import selenium
from selenium import webdriver
from scrapers_karavan import get_start_end_date
from db_info_and_adding import get_database, adding_new_discount_to_db, adding_second_discount_to_db

DAFI_MAIN_PAGE = "http://kharkov.dafi.ua/"
# DAFI_PAGE = "http://kharkov.dafi.ua/mall-promo/"


def show_all_discount(shop_link):
    """
    Run headless Chrome
    :param shop_link: <str> Mall link page with discount
    :return: <class 'selenium.webdriver.chrome.webdriver.WebDriver'>
    """
    print("========START SELENIUM========")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('window-size=1200x600')
    driver = webdriver.Chrome(executable_path=os.path.abspath('chromedriver'), chrome_options=options)

    # driver = webdriver.Firefox()
    driver.get(shop_link)

    for _ in range(1):
        button = driver.find_element_by_class_name('load-content')
        if button:
            button.click()
            time.sleep(1)
        else:
            break
    return driver


def get_mall_info(driver_page):
    """
    Get main Mall info
    :param driver_page: <class> 'selenium.webdriver.chrome.webdriver.WebDriver'
    :return: <dict> with mall info
    """
    mall_main_info = driver_page.find_element_by_xpath('//div[@class="col-xs-6 col-sm-3 col-md-2"]')
    mall_name = mall_main_info.find_element_by_css_selector('a').get_attribute('title')
    mall_main_link = mall_main_info.find_element_by_css_selector('a').get_attribute('href')
    mall_image = mall_main_info.find_element_by_css_selector('img').get_attribute('src')

    mall_info = {
        'mall_name': mall_name,
        'mall_link': mall_main_link,
        'mall_image': mall_image
    }

    return mall_info


def get_all_discount_links(driver_page):
    """
    This method create list with all discount links
    :param driver_page: <class> 'selenium.webdriver.chrome.webdriver.WebDriver'
    :return: <list> list with all discount links
    """
    discount_links = []
    all_elements = driver_page.find_elements_by_xpath('//div[@class="col-sm-6 col-md-4"]')

    for link in all_elements:
        mall_discount_link = link.find_element_by_css_selector('a').get_attribute('href')
        discount_links.append(mall_discount_link)

    return discount_links


def get_date_discount(driver_page):
    """
    Getting starting and ending discount date
    :param driver_page: <class> 'selenium.webdriver.chrome.webdriver.WebDriver'
    :return: <dict> dictionary with starting and ending discount date
    """
    time_list = driver_page.find_elements_by_css_selector('time')
    time_start = time_list[0].text
    time_end = time_list[1].text
    finish_date = (time_start + '{}' + time_end).format(' - ').split()
    discount_date = get_start_end_date(finish_date)

    return discount_date


def get_shop_info(driver_page):
    """
    Getting information about shop which have discount
    :param driver_page: <class> 'selenium.webdriver.chrome.webdriver.WebDriver'
    :return: <dict> Short shop info
    """
    shop_image = driver_page.find_element_by_xpath(
        '//img[@class="img-responsive shop__logo-img"]'
    ).get_attribute('data-src')
    shop_image = DAFI_MAIN_PAGE[:-1] + shop_image

    shop_sale_image = driver_page.find_element_by_xpath(
        '//img[@class="img-responsive shop__action-img"]'
    ).get_attribute('data-src')
    shop_sale_image = DAFI_MAIN_PAGE[:-1] + shop_sale_image

    shop_name = driver_page.find_element_by_xpath('//div[@class="shop__name"]').text
    # button = driver_page.find_element_by_class_name('shop__name')
    button = driver_page.find_element_by_xpath('//div[@class="shop__name"]')
    button.click()
    # shop_text = driver_page.find_elements_by_class_name('col-sm-6')
    shop_text = driver_page.find_elements_by_xpath('//div[@class="col-sm-6"]')
    shop_link = shop_text[1].find_element_by_css_selector('a').get_attribute('href')

    shop_info = {
        'shop_name': shop_name,
        'shop_image': shop_image,
        'discount_image': shop_sale_image,
        'shop_link': shop_link
    }

    return shop_info


def scrapers_dafi_page(shop_link):
    """
    This method create a new discount in db from page
    :param shop_link: <str> link of parse page
    :return: Returns a record in the database
    """
    driver = show_all_discount(shop_link)
    discount_links = get_all_discount_links(driver)
    discount_list = []
    mall_main_info = get_mall_info(driver)

    database = get_database()

    # if database.find({'mall_name': mall_main_info.get('mall_name')}).count() == 0:
    #     mall_main_info['discount'] = []
    #     database.save(mall_main_info)

    for link in discount_links:
        driver.get(link)
        discount_date = get_date_discount(driver)
        discount_discription = driver.find_element_by_css_selector('p').text
        shop_discount_info = {
            'date_start': discount_date.get('start_date'),
            'date_end': discount_date.get('end_date'),
            'discount_description': discount_discription,
            'discount_link': link
        }

        if driver.find_elements_by_xpath('//div[@id="collapse-shops"]'):
            shop_discount_info.update(get_shop_info(driver))
            discount_list.append(shop_discount_info)

        else:
            shop_name = driver.find_element_by_css_selector('h1').text
            get_div_image = driver.find_element_by_xpath('//div[@class="event__posters"]')
            discount_image = get_div_image.find_element_by_css_selector('div').get_attribute('style')
            discount_image = ('{}' + discount_image.split('"')[1]).format(DAFI_MAIN_PAGE[:-1])
            shop_discount_info.update({'shop_name': shop_name, 'discount_image': discount_image})
            # shop_discount_info['shop_name'] = shop_name
            # shop_discount_info['discount_image'] = discount_image
            discount_list.append(shop_discount_info)

        # adding_new_discount_to_db(database, shop_discount_info, mall_main_info.get('mall_name'))

        adding_second_discount_to_db(database, shop_discount_info, mall_main_info)

    # finished_mall_discount = database.find({'mall_name': mall_main_info.get("mall_name")}).next()

    finished_mall_discount = [discount for discount in database.find({'mall_name': mall_main_info.get("mall_name")})]

    return finished_mall_discount

DAFI_PAGE = "http://kharkov.dafi.ua/mall-promo/"
scrapers_dafi_page(DAFI_PAGE)
