# -*- coding: utf-8 -*-
import abc
import boto3
import json
import pymongo
import time
import datetime
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.request import urlopen
from selenium.common.exceptions import NoSuchElementException
from abc import ABCMeta
from config import TOPIC_ARN
from botocore.exceptions import ClientError
from config import BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_KEY


CREDENTIALS = {
    'access_key': AWS_ACCESS_KEY,
    'secret_key': AWS_SECRET_KEY,
    'region_name': 'us-east-2',
    'bucket_name': BUCKET_NAME
}

DB_SETTINGS = {
    'database_host': '18.220.30.245',
    'database_index': 27017,
}


class Scrapper(metaclass=ABCMeta):
    MONTH = (
        (1, 'Января'),
        (2, 'Февраля'),
        (3, 'Марта'),
        (4, 'Апреля'),
        (5, 'Мая'),
        (6, 'Июня'),
        (7, 'Июля'),
        (8, 'Августа'),
        (9, 'Сентября'),
        (10, 'Октября'),
        (11, 'Ноября'),
        (12, 'Декабря')
    )

    def __init__(self, url, settings, mall_name, credentials, main_url=None):
        """
        :param url: <str> url: 'https://some_adress/'
        :param settings: <dict> database settings
                        settings = {'database_host': <str> some host, 'database_index': <int> some index}
        :param mall_name: <str> mall name 'Karavan-KHA' or something like that
        :param credentials: <dict> cred = {'access_key': some access_key , 'secret_key': some secret_key,
                                           'region_name': some region_name, 'bucket_name': some bucket_name
                                           }
        """
        self.mall_link = url
        self.host = settings['database_host']
        self.index = settings['database_index']
        self.mall_name = mall_name
        self.access_key = credentials['access_key']
        self.secret_key = credentials['secret_key']
        self.region_name = credentials['region_name']
        self.bucket_name = credentials['bucket_name']
        self.main_url = main_url if main_url else ''

    @abc.abstractmethod
    def scrapper(self):
        pass

    @staticmethod
    def get_database(host, index):
        client = pymongo.MongoClient(host, index)
        db = client.test_scrapers
        # coll = db.mall_sales
        # db.mall_sales_second.drop()
        coll_second = db.mall_sales_second
        # return coll
        return coll_second

    def _get_client(self):

        s3 = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region_name
            )
        return s3

    def check_mall_image(self, link, mall_name):
        s3 = self._get_client()

        try:
            s3.head_object(Bucket=self.bucket_name, Key=mall_name)
            image_link = '{}/{}/{}'.format(s3.meta.endpoint_url, self.bucket_name, mall_name)
        except ClientError:
            response = urllib.request.urlopen(link)
            image = response.read()
            s3.put_object(ACL='public-read', Body=image, Bucket=self.bucket_name, Key=mall_name)
            image_link = '{}/{}/{}'.format(s3.meta.endpoint_url, self.bucket_name, mall_name)
        return image_link

    def _get_discount_day(self, date_list):
        """
        This method generate date from string to date in this format : datetime.datetime(2017, 6, 19, 0, 0),
        and return <list> wiht sorted date
        :param date_list: <list> example: ['19', 'some_month', '-', '09', 'some_month', '2017']
        :return: <list> sorted list in format like this: [datetime.datetime(2017, 6, 19, 0, 0),
                                                          datetime.datetime(2017, 7, 9, 0, 0)]
        """
        new_date_list = []

        year_new = int(date_list[-1])
        year_old = int(date_list[2]) if len(date_list) == 7 else year_new
        day_start = int(date_list[0])
        day_end = int(date_list[-3])

        for month in self.MONTH:
            if month[1].lower() == date_list[1]:
                start_date = datetime.datetime(year_old, month[0], day_start, 0, 0)
                new_date_list.append(start_date)
            if len(date_list) == 7:
                if month[1].lower() == date_list[5]:
                    end_date = datetime.datetime(year_new, month[0], day_end, 0, 0)
                    new_date_list.append(end_date)
            else:
                if month[1].lower() == date_list[4]:
                    end_date = datetime.datetime(year_new, month[0], day_end, 0, 0)
                    new_date_list.append(end_date)

        new_date_list.sort()

        return new_date_list

    def get_start_end_date(self, discount_date, discount_start=''):
        """
        This method generate a right <list> of date and return start date and end date in format:
        datetime.datetime(2016, 12, 18, 0, 0)
        :param discount_date: <list> Contains information about the date: for example:
               ['19', 'month', '-', '09', 'month', '2017'] or ['-', '31', 'month', '2017'] etc.
               Also <list> can be empty
        :param discount_start: <str> from html format for example '2017-06-01'
        :return: <dict> with keys: start_date and end_date in format like this: datetime.datetime(2016, 12, 18, 0, 0)
        """
        if len(discount_date) == 0:
            date_start = datetime.datetime.strptime(discount_start, '%Y-%m-%d')
            date_start_end = {
                'start_date': date_start,
                'end_date': date_start
            }
        else:
            if len(discount_date) == 5:
                discount_date.insert(1, discount_date[-2])

            if len(discount_date) == 4:
                date_start_list = discount_start.split('-')
                discount_date.insert(0, date_start_list[2])
                for i in self.MONTH:
                    if i[0] == int(date_start_list[1]):
                        discount_date.insert(1, i[1].lower())
                        discount_date.insert(2, date_start_list[0])

            date_list = self._get_discount_day(discount_date)
            date_start_end = {
                'start_date': date_list[0],
                'end_date': date_list[1]
            }

        return date_start_end

    @staticmethod
    def mongo_db(coll, discount_info, mall_name):
        search_discount = coll.find_one(
            {'discount_description': discount_info['discount_description'],
             'shop_name': discount_info['shop_name']}
        )

        if not search_discount:
            print("Adding new discount: {}".format((discount_info.get('shop_name'))))
            mall_name.update(discount_info)
            if mall_name.get('_id'):
                del mall_name['_id']
            coll.save(mall_name)

            get_discount = coll.find_one({'_id': mall_name['_id']})

            if get_discount['discount_image']:

                data = {'link': get_discount['discount_image'], 'id': str(get_discount['_id'])}

                client = boto3.client(
                    'sns',
                    aws_access_key_id=AWS_ACCESS_KEY,
                    aws_secret_access_key=AWS_SECRET_KEY,
                    region_name='us-east-2'
                )

                client.publish(TopicArn=TOPIC_ARN, Message=json.dumps(data))
        else:

            print("Discount already exists {}".format(discount_info.get('shop_name')))

        finished_mall_discount = coll.find({'shop_name': discount_info.get('shop_name')}).next()

        return finished_mall_discount


class ScrapperKaravan(Scrapper):

    @staticmethod
    def get_all_discount_page(shop_sales_link):
        """
         This method pulling data out of HTML files
        :param shop_sales_link: <str> shop sales link 'https://kharkov.karavan.com.ua/mtype/sales-ru/'
        :return: <dict> with key mall_info with value: list which include div with class 'container header'
                 and key all_sales with value: list  which include all div with class:
                 'col no_gutter col_4 tablet_col_4 mobile_full main_block_content_grid'
        """

        page = urlopen(shop_sales_link)
        soup = BeautifulSoup(page.read(), "lxml")
        view_all_page = soup.find(
            'div', {'class': 'pagination-all'}
        ).find('a').get('href')
        page = urlopen(view_all_page)
        soup = BeautifulSoup(page.read(), "lxml")
        all_sales = soup.findAll(True, 'col no_gutter col_4 tablet_col_4 mobile_full main_block_content_grid')
        mall_info = soup.findAll(True, 'container header')

        data_from_mall = {
            'mall_info': mall_info,
            'all_sales': all_sales
        }

        return data_from_mall

    def get_mall_info(self, mall_header, mall_name):
        """
        This method takes html page tags and pulls the required information for mall
        :param mall_header: <list> with <tag>
        :param mall_name: <str>
        :return: <dict> key: mall_name value: <str>
                        key: mall_link value: <str>
                        key: mall_image value: <str>
        """
        all_mall_sales_info = {}

        for mall in mall_header:
            mall_image = mall.find(
                'div', {'class': 'col no_gutter col_2 tablet_col_12 mobile_full header_top_logo'}
            ).find('img').get('src')
            mall_image = Scrapper.check_mall_image(self, mall_image, mall_name)

            mall_main_link = mall.find(
                'li',
                {'class': 'menu-item menu-item-type-post_type menu-item-object-page menu-item-home menu-item-1690'}
            ).find('a').get('href')

            mall_name = mall.find(
                'div', {'class': 'col no_gutter col_2 tablet_col_12 mobile_full header_top_logo'}
            ).find('img').get('title')

            all_mall_sales_info = {
                'mall_name': mall_name.lower(),
                'mall_link': mall_main_link,
                'mall_image': mall_image
            }

        return all_mall_sales_info

    def get_info_discount(self, discount_page_info):
        """
        This method takes html page tags and pulls the required information for discount
        :param discount_page_info: <tag> with discount info
        :return:<dict> key: discount_description value: <str> shop description;
                       key: discount_date value: <dict> with keys 'end_date' and 'start_date'
                       format like this: datetime.datetime(2016, 1, 5, 0, 0);
                       key: discount_image value:<str> for example 'https://something.jpeg';
                       key: link_shop_discount value: <str> discount link
        """

        discount_date_str = discount_page_info.find(
            'time', {'class': 'main_block_content_grid_header_time'}
        ).text

        discount_date_list = [
            date_discount for date_discount in
            discount_date_str.replace('-', ' - ').strip().split(' ')
            if date_discount != ''
        ]

        if len(discount_date_list) != 0 and '-' not in discount_date_list:
            discount_date_list.insert(0, '-')

        if len(discount_date_list) != 0 and discount_date_list[-1] == '-':
            discount_date_list.insert(0, discount_date_list[-1])
            del discount_date_list[-1]

        discount_date_without_start = discount_page_info.find(
            'time', {'class': 'main_block_content_grid_header_time'}
        ).get('datetime')

        link_shop_discount = discount_page_info.find(
            'div', {'class': 'main_block_content_inner fadeInUp animated animated_delay_'}
        ).find('a').get('href')

        discount_image_all = discount_page_info.find(
            'div', {'class': 'main_block_content_grid_img main_block_content_grid_img_default'}
        ).find('img')

        if discount_image_all:
            discount_image_all = discount_image_all.get('srcset')
        else:
            discount_image_all = ''

        discount_description = discount_page_info.find('div', {'class': 'main_block_content_grid_header_text'}).text
        discount_image = discount_image_all.split(',')[1][:-5] if len(discount_image_all) != 0 else ''
        discount_date = Scrapper.get_start_end_date(self, discount_date_list, discount_date_without_start)

        discount_info = {
            'date_start': discount_date.get('start_date'),
            'date_end': discount_date.get('end_date'),
            'link_shop_discount': link_shop_discount,
            'discount_image': discount_image,
            'discount_description': discount_description,
            'shop_name': discount_description.lower()
        }

        return discount_info

    def scrapper(self):

        mall = ScrapperKaravan.get_all_discount_page(self.mall_link)
        mall_main_info = ScrapperKaravan.get_mall_info(self, mall.get('mall_info'), self.mall_name)
        database = Scrapper.get_database(self.host, self.index)

        for sales in mall.get('all_sales'):
            discount_info = ScrapperKaravan.get_info_discount(self, sales)
            Scrapper.mongo_db(database, discount_info, mall_main_info.copy())
        finished_mall_discount = [
            discount for discount in database.find({'mall_name': mall_main_info.get("mall_name")})
        ]

        return finished_mall_discount


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

            Scrapper.mongo_db(database, shop_discount_info, mall_main_info)
        finished_mall_discount = [discount for discount in database.find(
            {'mall_name': mall_main_info.get("mall_name")}
        )]

        return finished_mall_discount


# test = ScrapperKaravan(
#     url='https://kharkov.karavan.com.ua/mtype/sales-ru/',
#     settings=DB_SETTINGS,
#     mall_name='Karavan-KHA',
#     credentials=CREDENTIALS,
# )
#
# test.scrapper()

# test = ScrapperDafi(
#     url='http://kharkov.dafi.ua/mall-promo/',
#     settings=DB_SETTINGS,
#     mall_name='Dafi-KHA',
#     credentials=CREDENTIALS,
#     main_url='http://kharkov.dafi.ua/'
# )
#
# test.scrapper()
