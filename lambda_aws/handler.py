import json
import pymongo
import logging
import os
from bson.objectid import ObjectId
from s3_storage import get_image_link_s3

PUBLIC_IP = os.environ['public_ip']
DATABASE_INDEX = os.environ['database_index']
PRIVATE_IPS = os.environ['private_ips']


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_database():
    client = pymongo.MongoClient(PUBLIC_IP, DATABASE_INDEX)
    db = client.test_scrapers
    discount = db.mall_sales_second
    return discount


def lambda_handler(event, context):
    data = json.loads(event['Records'][0]['Sns']['Message'])
    base = get_database()
    get_discount = base.find_one({'_id': ObjectId(data['id'])})
    get_discount['discount_image'] = get_image_link_s3(data['link'], data['id'])
    base.save(get_discount)
    return
