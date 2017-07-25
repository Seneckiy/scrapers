from scrapers_karavan import scrapers_karavan_page
from scrapers_dafi import scrapers_dafi_page

DAFI_PAGE = "http://kharkov.dafi.ua/mall-promo/"
KARAVAN_PAGE = 'https://kharkov.karavan.com.ua/mtype/sales-ru/'

scrapers_karavan_page(KARAVAN_PAGE)
scrapers_dafi_page(DAFI_PAGE)