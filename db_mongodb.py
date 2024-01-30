import pymongo
import random

# odLPpZbJETcnzrWg

client = pymongo.MongoClient("mongodb+srv://whitelegend56:odLPpZbJETcnzrWg@restaurant.lgfalwj.mongodb.net/?retryWrites=true&w=majority")

db = client.get_database("tarunsbriyani")

#DEFINING THE COLLECTIONS [5]
food_item = db.food_item
user_details_col = db.user_details
orders = db.orders
order_tracking = db.order_tracking
deliveryboi = db.delivery_person


# 1. to get the nxt order id
def get_next_orderid():
    nxt_o_id = orders.count_documents(filter={})
    return int(nxt_o_id)+1

# 3. inserting the intial status
def insert_intial_status(orderid,status):
    doc = {
        "order_id":str(orderid),
        "status":status
    }
    order_tracking.insert_one(doc)

# 2.Inserting into the databae
def create_orders(food,quantity,ctorders):
    foodls = []

    for f in food:
        print(f)
        foodls.append(food_item.find({"name":f}))


    fi = []
    fp = []

    for fs in foodls:
        for fsa in fs:
            print(fsa)
            fi.append(fsa.get('item_id'))
            fp.append(fsa.get('price'))

    print(fi,fp)

    totalprice = 0

    #now need to multiply the price with quantity
    for price,qty in zip(fp,quantity):
        totalprice +=(int(price)*int(qty))

    print(totalprice)

    doc = {
        "order_id":str(ctorders),
        "item_id":fi,
        "quantity":quantity,
        "total":totalprice
    }

    try:
        orders.insert_one(doc)
    except:
        return -1

    insert_intial_status(ctorders,"Your order is in progress")
    return 1

# create_orders(['egg briyani', 'mutton briyani'] ,[1.0, 2.0] ,6)


# 4. Save user deatils to db
def save_user_details(user_details:dict,orderid: int):
    doc = {
        "order_id":str(orderid),
        "username":user_details['name'],
        "mobileno":user_details['mobileno'],
        "address":user_details['address']
    }

    user_details_col.insert_one(doc)

jsa = {
    "name":"komali",
    "mobileno":"989898988",
    "address":"131, 8 Cross Sampige, Malleshwaram, Bengaluru, 560003"
}

# 5.Updating the entire user details
def update_user_details(user_details:dict,orderid: int):
    print(type(orderid))
    print(user_details)
    update_query = {"order_id": str(orderid)}
    update_values = {"$set": {"username": user_details['name'], "address": user_details['address'], "mobileno": str(user_details['mobileno'])}}

    s = user_details_col.update_one(update_query,update_values)
    
    print(s.matched_count)
    try:
        s = user_details_col.update_one(update_query,update_values)
        if(s.matched_count == 1):
            return "Updated successfully"
    except:
        return "Can't update user details"

# 6. updating just the name
def update_name_field(name , orderid):
    update_query = {"order_id": str(orderid)}
    update_values = {"$set": {"username": name}}

    s = user_details_col.update_one(update_query,update_values)
    
    print(s.matched_count)
    try:
        s = user_details_col.update_one(update_query,update_values)
        if(s.matched_count == 1):
            return "Updated successfully"
    except:
        return "Can't update user details"

# 7. Updating the name and mobileno
def update_nameAndmob_field(user_details, orderid):
    update_query = {"order_id": str(orderid)}
    update_values = {"$set": {"username": user_details['name'], "mobileno": str(user_details['mobileno'])}}

    s = user_details_col.update_one(update_query,update_values)
    
    print(s.matched_count)
    try:
        s = user_details_col.update_one(update_query,update_values)
        if(s.matched_count == 1):
            return "Updated successfully"
    except:
        return "Can't update user details"

def get_order_id(user_name):
    print(user_name['name'])
    usr = user_name['name']
    res = user_details_col.find({'username':str(usr)})
    
    orderid = ''
    for i in res:
        print(i)
        orderid += i.get('order_id') 
    
    return orderid

def get_name_with_orderid(orderid):
    res = user_details_col.find({'order_id':str(orderid)})
    
    name = ''
    for i in res:
        print(i)
        name += i.get('username') 
    
    return name

def get_order_id_mob(mobileno):
    print(mobileno['mobileno'])
    usr = mobileno['mobileno']
    res = user_details_col.find({'mobileno':str(usr)})
    
    orderid = ''
    for i in res:
        print(i)
        orderid += i.get('order_id') 
    
    return orderid

def get_order_status(orderid :int):
    res = order_tracking.find({"order_id":str(orderid)})
    status = ''
    for i in res:
        status += i.get('status')

    if(status == ''):
        return "No such order found ;["

    print(status)

    return status



def get_total_order(orderid):
    res = orders.find({"order_id":str(orderid)})
    total = 0
    for i in res:
        total = i.get('total')

    return total


def get_delivery_boy():
    print("return the delivery boi name some random")
    op = random.randint(1,10)
    deliverydetails = deliveryboi.find({"delivery_person_id":str(op)})
    d_d = []
    for i in deliverydetails:
        d_d.append(i.get('delivery_person_name'))
        d_d.append(i.get('delivery_person_mobileno'))
    print(d_d)
    return d_d


def save_payment_details(item_id,order_id,payment_id,signature,paid_method):
    print("Inside the payment details")
    update_query = {"order_id": str(item_id)}
    update_values = {"$set": { "paid_by": paid_method,"paid_status": "Paid",
        "payment_id": payment_id,"payment_order_id": order_id,"signature": signature}}

    s = orders.update_one(update_query,update_values)
    
    print(s.matched_count)
    try:
        s = orders.update_one(update_query,update_values)
        if(s.matched_count == 1):
            return 1
    except:
        return 0

def save_COD_payment_details(item_id):
    print("Inside the payment details")
    update_query = {"order_id": str(item_id)}
    update_values = {"$set": {"paid_status": "unpaid","paid_by":"cash on delivery"}}

    s = orders.update_one(update_query,update_values)
    
    print(s.matched_count)
    try:
        s = orders.update_one(update_query,update_values)
        if(s.matched_count == 1):
            return 1
    except:
        return 0

def get_payment_details(orderid):
    print(str(int(orderid)))
    print("Inside the payment details page to get the details of the order")
    res = orders.find({"order_id":str(int(orderid))})
    print(res)
    payment_det = {}
    for i in res:
        payment_det['paid_by'] = i.get('paid_by')
        payment_det['status'] = i.get('paid_status')
        payment_det['reciept'] = i.get('payment_id')

    print(payment_det)
    return payment_det

# ------------------------------INSERT OPERATION AND TESTING --------------------------------------


# my food items
order_id = ["3","4","5","6","7","8","9","10","11","12","13","14",
"15",
"16",
"17",
"18",
"19"]
food = ["prawn briyani","veg briyani","panner briayni","egg briyani","chicken fried rice","pepper chicken","chicken tikka masala","panner starter"
    ,"egg gravy","chicken kebab","chicken 65","chicken tandoori red","prawns masala","Tangdi kebab","chicken crispy","Dragon Chicken","Seekh kebab"]
price = [150.00,
80.00,
80.00,
90.00,
80.00,
130.00,
150.00,
120.00,
100.00,
230.00,
150.00,
250.00,
200.00,
190.00,
230.00,
280.00,
180.00]

def insert_to_fooditem():
    docs = []
    for o,f,p in zip(order_id,food,price):
        doc = {
            "item_id":o,
            "name":f,
            "price":p
        }
        docs.append(doc)

    food_item.insert_many(docs)


def create_order_tracking():
    order_id = ["1","3"]
    status = ["Your food is in processing","Your food has been delivered"]

    for o,s in zip(order_id,status):
        doc = {
            "order_id":o,
            "status":s
        }
        order_tracking.insert_one(doc)


def create_user_details(oi,name,mob,add):
    order_id = orders.find({"order_id":oi})
    print(list(order_id))
    doc = {
        "order_id":oi,
        "username":name,
        "mobileno":mob,
        "address":add,
    }

    

    user_details_col.insert_one(doc)


def insert_to_deliveryboi():
    delivery_id = ["1", "2","3","4","5","6","7","8","9","10"]
    name = ["Raja ram", "Ramesh", "Suresh" , "Lavanaya" ,"Kavya" , "Vasan" , "Shanmugam" ,"Mahaesh","Venki","Irfan"]
    mobileno = ["9098452143","9898452143","9698452178","9798452145","9498452136","9898452163","9798454521","9998452174","9598452185","9758452415"]

    for o, s,e in zip(delivery_id, name,mobileno):
        doc = {
            "delivery_person_id": o,
            "delivery_person_name": s,
            "delivery_person_mobileno":e,
        }
        deliveryboi.insert_one(doc)

