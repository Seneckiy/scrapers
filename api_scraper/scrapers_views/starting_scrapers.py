import logging
import os
from scrapper_dafi_class import ScrapperDafi
from scrapper_karavan_class import ScrapperKaravan
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, TOPIC_ARN, BUCKET_NAME, DATABASE_INDEX, PUBLIC_IP, REGION_NAME, \
    MALL_NAME_DAFI, MALL_NAME_KARAVAN

DAFI_PAGE = "http://kharkov.dafi.ua/mall-promo/"
DAFI_MAIN_PAGE = "http://kharkov.dafi.ua/"
KARAVAN_PAGE = 'https://kharkov.karavan.com.ua/mtype/sales-ru/'
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
logging.basicConfig(
    filename='{}/scrapers_views/logs/scarper.log'.format(BASE_DIR),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_SETTINGS = {
    'database_host': PUBLIC_IP,
    'database_index': DATABASE_INDEX,
}

CREDENTIALS = {
    'access_key': AWS_ACCESS_KEY,
    'secret_key': AWS_SECRET_KEY,
    'region_name': REGION_NAME,
    'bucket_name': BUCKET_NAME,
    'topic_arn': TOPIC_ARN
}

start_scrapper_karavan = ScrapperKaravan(
    url=KARAVAN_PAGE,
    settings=DB_SETTINGS,
    mall_name=MALL_NAME_KARAVAN,
    credentials=CREDENTIALS
)
# start_scrapper_karavan.scrapper()

start_scrapper_dafi = ScrapperDafi(
    url=DAFI_PAGE,
    settings=DB_SETTINGS,
    mall_name=MALL_NAME_DAFI,
    credentials=CREDENTIALS,
    main_url=DAFI_MAIN_PAGE
)
start_scrapper_dafi.scrapper()

