import datetime
from rest_framework.views import APIView
from rest_framework.response import Response


import pymongo

DATABASE_HOST = 'localhost'
DATABASE_INDEX = 27017

client = pymongo.MongoClient(DATABASE_HOST, DATABASE_INDEX)
db = client.test_scrapers
# coll = db.mall_sales
coll = db.mall_sales_second


class ToDoView(APIView):

    def get(self, request):

        data = {}
        search_list = []
        mall_name = request.GET.get('mall_name')
        shop_name = request.GET.get('shop_name')
        selected_date = request.GET.get('date')

        if mall_name:
            data['mall_name'] = mall_name
        if shop_name:
            data['shop_name'] = {"$regex": ".*{}.*".format(shop_name)}
        if selected_date:
            data['date_end'] = {'$gte': datetime.datetime.strptime(selected_date, "%Y-%m-%d")}

        search_discount = coll.find(data)
        if search_discount.count():
            print(search_discount.count())
            for discount in search_discount:
                del discount['_id']
                search_list.append(discount)
                print(discount)
        else:
            print('oo')

        return Response(search_list)
