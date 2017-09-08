# -*- coding: utf-8 -*-
import abc
import boto3
import json
import pymongo
import datetime
import urllib.request
from abc import ABCMeta
from botocore.exceptions import ClientError


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
                                           'region_name': some region_name, 'bucket_name': some bucket_name,
                                           'topic_arn': some topic arn
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
        self.topic_arn = credentials['topic_arn']
        self.main_url = main_url if main_url else ''

    @abc.abstractmethod
    def scrapper(self):
        pass

    @staticmethod
    def get_database(host, index):
        client = pymongo.MongoClient(host, index)
        db = client.test_scrapers
        # coll = db.mall_sales
        db.mall_sales_second.drop()
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
        mall_name = "{}{}".format(mall_name, ".svg")
        try:
            s3.head_object(Bucket=self.bucket_name, Key=mall_name)
            image_link = '{}/{}/{}'.format(s3.meta.endpoint_url, self.bucket_name, mall_name)
        except ClientError:
            response = urllib.request.urlopen(link)
            image = response.read()
            s3.put_object(ACL='public-read', Body=image, Bucket=self.bucket_name, Key=mall_name, ContentType='image/svg+xml')
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

    def mongo_db(self, coll, discount_info, mall_name):
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
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region_name
                )

                client.publish(TopicArn=self.topic_arn, Message=json.dumps(data))
        else:

            print("Discount already exists {}".format(discount_info.get('shop_name')))

        finished_mall_discount = coll.find({'shop_name': discount_info.get('shop_name')}).next()

        return finished_mall_discount
