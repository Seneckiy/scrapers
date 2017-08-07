import logging
from scrapers.settings import BASE_DIR
from scrapers_karavan import scrapers_karavan_page
from scrapers_dafi import scrapers_dafi_page

DAFI_PAGE = "http://kharkov.dafi.ua/mall-promo/"
KARAVAN_PAGE = 'https://kharkov.karavan.com.ua/mtype/sales-ru/'

logging.basicConfig(
    filename='{}/scrapers_views/logs/scarper.log'.format(BASE_DIR),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

scrapers_karavan_page(KARAVAN_PAGE)
scrapers_dafi_page(DAFI_PAGE)
