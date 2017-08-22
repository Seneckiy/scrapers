import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from scrappers_class import Scrapper


class ScrapperDafi(Scrapper):
    
    @staticmethod
    def dafi_show_all_discount(shop_link):
        """
        Run headless Chrome
        :param shop_link: <str> Mall link page with discount
        :return: <class 'selenium.webdriver.chrome.webdriver.WebDriver'>
        """
        print("========START SELENIUM========")

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('window-size=1200x900')
        driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver", chrome_options=options)
        driver.get(shop_link)

        for _ in range(1):
            button = driver.find_element_by_class_name('load-content')
            if button:
                button.click()
                time.sleep(1)
            else:
                break
        return driver

    @staticmethod
    def dafi_get_all_discount_links(driver_page):
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

    def dafi_get_mall_info(self, driver_page, mall_main_name):
        """
        Get main Mall info
        :param driver_page: <class> 'selenium.webdriver.chrome.webdriver.WebDriver'
        :param mall_main_name: <str> mall name
        :return: <dict> with mall info
        """
        mall_main_info = driver_page.find_element_by_xpath('//div[@class="col-xs-6 col-sm-3 col-md-2"]')
        mall_name = mall_main_info.find_element_by_css_selector('a').get_attribute('title')
        mall_main_link = mall_main_info.find_element_by_css_selector('a').get_attribute('href')
        mall_image = mall_main_info.find_element_by_css_selector('img').get_attribute('src')
        mall_image = Scrapper.check_mall_image(self, mall_image, mall_main_name)

        mall_info = {
            'mall_name': mall_name.lower(),
            'mall_link': mall_main_link,
            'mall_image': mall_image
        }

        return mall_info

    def get_date_discount(self, driver_page):
        """
        Getting starting and ending discount date
        :param driver_page: <class> 'selenium.webdriver.chrome.webdriver.WebDriver'
        :return: <dict> dictionary with starting and ending discount date
        """
        time_list = driver_page.find_elements_by_css_selector('time')
        time_start = time_list[0].text
        time_end = time_list[1].text
        finish_date = (time_start + '{}' + time_end).format(' - ').split()
        discount_date = Scrapper.get_start_end_date(self, finish_date)

        return discount_date

    @staticmethod
    def get_shop_info(driver_page, main_url):
        """
        Getting information about shop which have discount
        :param driver_page: <class> 'selenium.webdriver.chrome.webdriver.WebDriver'
        :param main_url: <str> main mall url
        :return: <dict> Short shop info
        """
        shop_image = driver_page.find_element_by_xpath(
            '//img[@class="img-responsive shop__logo-img"]'
        ).get_attribute('data-src')
        shop_image = main_url[:-1] + shop_image

        shop_sale_image = driver_page.find_element_by_xpath(
            '//img[@class="img-responsive shop__action-img"]'
        ).get_attribute('data-src')
        shop_sale_image = main_url[:-1] + shop_sale_image

        shop_name = driver_page.find_element_by_xpath('//div[@class="shop__name"]').text
        button = driver_page.find_element_by_xpath('//div[@class="shop__name"]')
        button.click()
        time.sleep(2)
        shop_text = driver_page.find_elements_by_xpath('//div[@class="col-sm-6"]')
        shop_link = shop_text[1].find_element_by_css_selector('a').get_attribute('href')

        shop_info = {
            'shop_name': shop_name.lower(),
            'shop_image': shop_image,
            'discount_image': shop_sale_image,
            'shop_link': shop_link
        }

        return shop_info

    def scrapper(self):

        driver = ScrapperDafi.dafi_show_all_discount(self.mall_link)
        discount_links = ScrapperDafi.dafi_get_all_discount_links(driver)
        mall_main_info = ScrapperDafi.dafi_get_mall_info(self, driver, self.mall_name)
        database = Scrapper.get_database(self.host, self.index)

        for link in discount_links:
            driver.get(link)
            discount_date = ScrapperDafi.get_date_discount(self, driver)
            try:
                discount_description = driver.find_element_by_css_selector('p').text
            except NoSuchElementException:
                discount_description = ''

            shop_discount_info = {
                'date_start': discount_date.get('start_date'),
                'date_end': discount_date.get('end_date'),
                'discount_description': discount_description,
                'discount_link': link
            }

            if driver.find_elements_by_xpath('//div[@id="collapse-shops"]'):
                shop_discount_info.update(ScrapperDafi.get_shop_info(driver, self.main_url))
            else:
                shop_name = driver.find_element_by_css_selector('h1').text
                get_div_image = driver.find_element_by_xpath('//div[@class="event__posters"]')
                discount_image = get_div_image.find_element_by_css_selector('div').get_attribute('style')
                discount_image = ('{}' + discount_image.split('"')[1]).format(self.main_url[:-1])
                shop_discount_info.update({'shop_name': shop_name.lower(), 'discount_image': discount_image})

            Scrapper.mongo_db(self, database, shop_discount_info, mall_main_info)
        finished_mall_discount = [discount for discount in database.find(
            {'mall_name': mall_main_info.get("mall_name")}
        )]

        return finished_mall_discount
