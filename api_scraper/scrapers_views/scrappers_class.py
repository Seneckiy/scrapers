# -*- coding: utf-8 -*-
import abc
import boto3
import json
import pymongo
from abc import ABCMeta
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, TOPIC_ARN
# from db_info_and_adding import get_database
from scrapers_karavan import get_all_discount_page, get_mall_info, get_info_discount

DATABASE_HOST = '18.220.30.245'
DATABASE_INDEX = 27017


class Scrapper(metaclass=ABCMeta):

    @abc.abstractmethod
    def scrapper(self):
        pass

    def get_database(self):
        client = pymongo.MongoClient(DATABASE_HOST, DATABASE_INDEX)
        db = client.test_scrapers
        coll = db.mall_sales
        db.mall_sales_second.drop()
        coll_second = db.mall_sales_second
        # return coll
        return coll_second

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

    def scrapper(self):
        mall = get_all_discount_page(self)
        all_sales = mall.get('all_sales')
        mall_main_info = get_mall_info(mall.get('mall_info'))

        database = Scrapper.get_database(self)

        for sales in all_sales:
            discount_info = get_info_discount(sales)
            Scrapper.mongo_db(self, database, discount_info, mall_main_info.copy())
        finished_mall_discount = [discount for discount in database.find({'mall_name': mall_main_info.get("mall_name")})]

        return finished_mall_discount

KARAVAN_PAGE = 'https://kharkov.karavan.com.ua/mtype/sales-ru/'
print(ScrapperKaravan.scrapper(KARAVAN_PAGE))
