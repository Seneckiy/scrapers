import pymongo

DATABASE_HOST = 'localhost'
DATABASE_INDEX = 27017


def get_database():
    client = pymongo.MongoClient(DATABASE_HOST, DATABASE_INDEX)
    db = client.test_scrapers
    coll = db.mall_sales
    # db.mall_sales_second.drop()
    coll_second = db.mall_sales_second
    # return coll
    return coll_second


def adding_second_discount_to_db(coll, discount_info, mall_name):

    search_discount = coll.find_one(
        {'discount_description': discount_info['discount_description'],
         'shop_name': discount_info['shop_name']}
    )

    print(dir(coll.save(mall_name)))

    if not search_discount:
        print("Adding new discount: {}".format((discount_info.get('shop_name'))))
        mall_name.update(discount_info)
        if mall_name.get('_id'):
            del mall_name['_id']
        coll.save(mall_name)
    else:

        print("Discount already exists {}".format(discount_info.get('shop_name')))

    # finished_mall_discount = coll.find({'shop_name': discount_info.get('shop_name')})

    finished_mall_discount = coll.find({'shop_name': discount_info.get('shop_name')}).next()

    return finished_mall_discount


def adding_new_discount_to_db(coll, discount_info, mall_name):


    serch_discount = coll.aggregate(
        [
            {"$unwind": "$discount"},
            {'$match': {
                'discount.discount_description': discount_info['discount_description'],
                'discount.date_start': discount_info['date_start'],
                'discount.date_end': discount_info['date_end']
            }
            }
        ]
    )

    try:
        serch_discount.next()
        print("Discount already exists {}".format(discount_info.get('shop_name')))

    except StopIteration:

        coll.update({'mall_name': mall_name}, {"$push": {"discount": discount_info}})
        print("Adding new discount: {}".format(discount_info))

    finished_mall_discount = coll.find({'mall_name': mall_name}).next()

    return finished_mall_discount
