from urllib.request import urlopen
from bs4 import BeautifulSoup
from scrappers_class import Scrapper


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
            Scrapper.mongo_db(self, database, discount_info, mall_main_info.copy())
        finished_mall_discount = [
            discount for discount in database.find({'mall_name': mall_main_info.get("mall_name")})
        ]

        return finished_mall_discount
