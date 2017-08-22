# -*- coding: utf-8 -*-

import datetime
import lxml
from bs4 import BeautifulSoup
from urllib.request import urlopen
from db_info_and_adding import get_database, adding_new_discount_to_db, adding_second_discount_to_db
from aws_storage import check_mall_image


MALL_NAME = 'Karavan-KH'

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


def get_discount_day(date_list):
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

    for month in MONTH:
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


def get_start_end_date(discount_date, discount_start=''):
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
            for i in MONTH:
                if i[0] == int(date_start_list[1]):
                    discount_date.insert(1, i[1].lower())
                    discount_date.insert(2,date_start_list[0])

        date_list = get_discount_day(discount_date)
        date_start_end = {
            'start_date': date_list[0],
            'end_date': date_list[1]
        }

    return date_start_end


def get_info_discount(discount_page_info):
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
    discount_date = get_start_end_date(discount_date_list, discount_date_without_start)

    discount_info = {
        'date_start': discount_date.get('start_date'),
        'date_end': discount_date.get('end_date'),
        'link_shop_discount': link_shop_discount,
        'discount_image': discount_image,
        'discount_description': discount_description,
        'shop_name': discount_description.lower()
    }

    return discount_info


def get_mall_info(mall_header):
    """
    This method takes html page tags and pulls the required information for mall
    :param mall_header: <list> with <tag>
    :return: <dict> key: mall_name value: <str>
                    key: mall_link value: <str>
                    key: mall_image value: <str>
    """
    all_mall_sales_info = {}

    for mall in mall_header:
        mall_image = mall.find(
            'div', {'class': 'col no_gutter col_2 tablet_col_12 mobile_full header_top_logo'}
        ).find('img').get('src')

        mall_image = check_mall_image(mall_image, MALL_NAME)

        mall_main_link = mall.find(
            'li', {'class': 'menu-item menu-item-type-post_type menu-item-object-page menu-item-home menu-item-1690'}
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


def scrapers_karavan_page(shop_link):
    """
    This method create a new discount in db from page
    :param shop_link: <str> link of parse page
    :return: Returns a record in the database
    """

    mall = get_all_discount_page(shop_link)
    all_sales = mall.get('all_sales')
    mall_main_info = get_mall_info(mall.get('mall_info'))

    database = get_database()

    # if database.find({'mall_name': mall_main_info.get('mall_name')}).count() == 0:
    #     mall_main_info['discount'] = []
    #     database.save(mall_main_info)

    for sales in all_sales:
        discount_info = get_info_discount(sales)
        adding_second_discount_to_db(database, discount_info, mall_main_info.copy())

        # adding_new_discount_to_db(database, discount_info, mall_main_info.get('mall_name'))

    # finished_mall_discount = database.find({'mall_name': mall_main_info.get("mall_name")}).next()

    finished_mall_discount = [discount for discount in database.find({'mall_name': mall_main_info.get("mall_name")})]
    print(len(finished_mall_discount))
    return finished_mall_discount

