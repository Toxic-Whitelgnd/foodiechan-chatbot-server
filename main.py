from fastapi import FastAPI, HTTPException , Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import httpx
import db_helper
import generic_helper
import db_mongodb

global order_total
global order_id

import razorpay

# razorpay_client.set_app_details({"title" : "Tarun's Paradise Briyani", "version" : "1.5.0"})

app = FastAPI()
# to handle the orders
inprogress_orders = {}
inprogress_userdetails = {}

# Dictionary to store payment links associated with order IDs
order_payment_links = {}

templates = Jinja2Templates(directory="templates")

@app.post('/')
async def webhook_handler(request: Request):
    payload = await request.json()

    #After getting the payload resonse let us extract
    intent = payload["queryResult"]["intent"]["displayName"]
    parameter = payload["queryResult"]["parameters"]
    output_context = payload["queryResult"]["outputContexts"]
    session_id = generic_helper.extract_session_id(output_context[0]['name'])


    handle_intent_req = {
        'track.order context:ongoing-order': track_orderid,
        'order.add - context:ongoing-order': add_order,
        'order.remove - context: ongoing-order': remove_order,
        'order.complete context: ongoing-order': complete_order,
        'order.cancel context:ongoing order': cancel_order,
        'user.name':get_user_name,
        'user.mobno context:ongoing-details':get_user_mobileno,
        'user.address context:ongoing-details':get_user_address,
        'change name mob address':change_user_Details,
        'payment.details':handle_payment_details,
        'payment details ongoing:payment':get_payment_details,
        'my cart':get_cart_item,
    }

    return handle_intent_req[intent](parameter, session_id)


def get_cart_item(parameter,session_id):
    cartkey = parameter["cartitems"]

    res = generic_helper.get_cart_word(cartkey)
    if(res == 1):
        # call the inprogress orders
        #and show the avilable order
        
        your_cart = ""

        print(inprogress_orders[session_id])
        for i in inprogress_orders[session_id].keys():
            print(i)
            your_cart += i
            
        print(i)
        fulfilment_text = f"Your Cart : {inprogress_orders[session_id]}"
        
    else:
        fulfilment_text = "Error while fetching the details"
    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })


def get_user_address(parameter,session_id):
    zipcode = parameter['zip-code']
    address = parameter['street-address'][0]['street-address']
    city  = parameter['street-address'][0]['city']
    busadd = parameter['street-address'][0]['business-name']


    print(zipcode)
    print(address)
    print(city + busadd)

    user_add = ''

    user_add+=address
    user_add+=busadd
    user_add+=', '+city
    user_add+=', '+zipcode

    print(user_add)


    if session_id not in inprogress_userdetails:
        fulfilment_text = "Please Enter your name and then come to mobile number"
    else:
        inprogress_userdetails[session_id].update({'address':user_add})

    name = inprogress_userdetails[session_id]['name']
    mob = inprogress_userdetails[session_id]['mobileno']
    address = inprogress_userdetails[session_id]['address']

    print(name, mob, address)

    print(inprogress_userdetails)
    if session_id not in inprogress_orders:
        fulfilment_text = "I am having trouble finding your order id!! please make the order again!"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)
        if order_id == -1:
            fulfilment_text = "Sorry unfortunately I cant place the order due to server error"
        else:
            order_total = db_mongodb.get_total_order(order_id)
            fulfilment_text = f"Thank you for your information! Here is your order id#{order_id}" \
                              f"And your total is {order_total}" \
                              f"your food will be delivered shortly" \
                              f"Review your details here {name}," \
                              f"{mob},{address}" \
                              f"You can change the details here by saying " \
                              f"CHANGE <Wrong Name> to <correct name>,pass your name to CHANGE MOBILENO=, CHANGE ADDRESS=" \
                              f"if no you can say CONTINUE [Feature Not usable]" \


        del inprogress_orders[session_id]
        #review changes to the user details if they want to change then keyword is "change details"

        db_mongodb.save_user_details(inprogress_userdetails[session_id],order_id)

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })

def change_user_Details(parameter,session_id):
    try:
        old_name = parameter['person'][0]
        new_name = parameter['person'][1]
    except:
        old_name = parameter['person']

    mobnumber = parameter['number']
    address = parameter['street-address']
    zip_code = parameter['zip-code']

    fulfilment_text = "Default response"

    print(old_name , new_name , mobnumber , address , zip_code)

    # get the orderid by using the name parameter
    curr_orderid = int(db_mongodb.get_order_id(old_name))
    print(curr_orderid)

    if session_id not in inprogress_userdetails:
        inprogress_userdetails[session_id]= {'name':new_name['name']}
    
    
    
    print(mobnumber)
    if(mobnumber != ''):
        inprogress_userdetails[session_id].update({'mobileno':mobnumber})

    if(len(address) != 0):
        saddress = address['street-address']
        city  = address['city']
        busadd = address['business-name']
            
        user_add = ''

        user_add+=saddress
        user_add+=busadd
        user_add+=', '+city
        user_add+=', '+zip_code

        print(user_add)
        inprogress_userdetails[session_id].update({'address': user_add})

        res = db_mongodb.update_user_details(inprogress_userdetails[session_id], curr_orderid)
        if(res == "Updated successfully"):
            fulfilment_text = f"Successfully Changed your Details {inprogress_userdetails}" \
                                "How would You like to pay?"\
                                "1. Cash on delivery " \
                                "2. Credit card "\
                                "3. Upi option " \
                                "4. Debit card " \
                                "5. Net banking" \
                                
        else:
            fulfilment_text = "Failed due to some technical error"
    
    # for updating the name only
    if(mobnumber == '' and len(address) == 0):
        res = db_mongodb.update_name_field(inprogress_userdetails[session_id]['name'],curr_orderid)
        if(res == "Updated successfully"):
            fulfilment_text = f"Successfully Changed the username" \
                                "How would You like to pay?"\
                                "1. Cash on delivery " \
                                "2. Credit card "\
                                "3. Upi option " \
                                "4. Debit card " \
                                "5. Net banking" 
                                
        else:
            fulfilment_text = "Failed due to some technical error"

    print(fulfilment_text)

    # for updating the name and mobileno
    if(mobnumber != '' and len(address) == 0):
        res = db_mongodb.update_nameAndmob_field(inprogress_userdetails[session_id],curr_orderid)
        if(res == "Updated successfully"):
            fulfilment_text = f"Successfully Changed the username and mobile number."\
                                "How would You like to pay?"\
                                "1. Cash on delivery " \
                                "2. Credit card "\
                                "3. Upi option " \
                                "4. Debit card " \
                                "5. Net banking" \
                               
        else:
            fulfilment_text = "Failed due to some technical error"


    # del inprogress_userdetails[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })


def get_user_mobileno(parameter,session_id):
    mobilno = parameter['number']

    if session_id not in inprogress_userdetails:
        fulfilment_text = "Please Enter your name and then come to mobile number"
    else:
        inprogress_userdetails[session_id].update({'mobileno':str(mobilno)})

    fulfilment_text = "Thank you for providing your phone number. Could you additionally provide me your delivery address!"

    print(inprogress_userdetails)

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })


def get_user_name(parameter,session_id):

    username = parameter['person']

    if session_id not in inprogress_userdetails:
        inprogress_userdetails[session_id] = username

    fulfilment_text = "Thank you for providing your Name. Could you additionally provide me your Phone Number!"

    print(inprogress_userdetails)

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })



def track_orderid(parameter,session_id):
    orderid = parameter['number']
    print(int(orderid))
    # the database call has been processed here
    order_status = db_mongodb.get_order_status(int(orderid))


    if order_status:
        if (order_status == "Your order is out for delivery"):
        #get the delivery boi details
            deliverdetails = db_mongodb.get_delivery_boy()
            fullfilment_text = f"Your order id #{orderid} is  {order_status} is " \
                               f"Deliverying by {deliverdetails[0]} and his contact number {deliverdetails[1]}"
        else:
            fullfilment_text = f"Your order id #{orderid} is  {order_status}"
    else:
        fullfilment_text = f"No order found ;["


    return JSONResponse(content={
        "fulfillmentText":fullfilment_text
    })


def add_order(parameter,session_id):
    food_items = parameter['food-item']
    quantity = parameter['number']

    new_food_dict = dict(zip(food_items,quantity))

    if session_id in inprogress_orders:
        #if it is already there then update to the current dict
        curr_food_dict = inprogress_orders[session_id]
        curr_food_dict.update(new_food_dict)
        inprogress_orders[session_id] = curr_food_dict

    else:
        inprogress_orders[session_id] = new_food_dict

    # extract it to str
    orders = generic_helper.extract_str(inprogress_orders[session_id])
    if len(food_items) != len(quantity):
        fulfilment_text = "Sorry I cant understand the food item and quantity can u specify it again!!"
    else:
        fulfilment_text = f"So far you have {orders} in your cart, Anything else or you can say cancel order to cancel your current order?"

    print("*******************")
    print(inprogress_orders)
    print("*******************")

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })

def remove_order(parameter,session_id):

    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "Please make some orders!!"
        })

    foods_items = parameter['food-item'] #items to be removed
    current_order = inprogress_orders[session_id] #contains the current itemsets

    not_foodorder = []
    removed_order = []

    for fooditem in foods_items:
        if fooditem not in current_order:
            not_foodorder.append(fooditem)
        else:
            removed_order.append(fooditem)
            del current_order[fooditem]

    if len(removed_order) > 0:
        fulfilment_text = f"Removed {','.join(removed_order)} from your cart"
    if len(not_foodorder) > 0:
        fulfilment_text = f"Your current order does not have {','.join(not_foodorder)}"

    if len(current_order.keys()) == 0:
        fulfilment_text = "Your cart is empty"
    else:
        order_str = generic_helper.extract_str(current_order)
        fulfilment_text = f"Here is what left in your cart {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })

def cancel_order(parameter,session_id):


    food_dict = inprogress_orders[session_id]
    print("$$$$$$$$$$$$$$$$$")
    print(food_dict)
    if(len(food_dict.keys()) > 0):
        for fi,q in food_dict.items():
            del food_dict[fi]

    fulfilment_text = "Your order has been successfully removed"

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })

def complete_order(parameter,session_id):
    if session_id not in inprogress_orders:
        fulfilment_text = "I am having trouble finding your order id!! please make the order again!"
    else:
        fulfilment_text = "Your order has been successfully placed " \
                             f"could you provide me your name? or you" \
                              f"can cancel order here!"
    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })


# for getting the payment details
def handle_payment_details(parameter,session_id):
    payment_meth = parameter['payment-method']
    print(payment_meth[0])

    if(payment_meth[0] == "cash on delivery"):
        orderid = db_mongodb.get_order_id_mob(inprogress_userdetails[session_id])
        res = db_mongodb.save_COD_payment_details(orderid)
        if(res == 1):

            fulfilment_text = "Thank you for choosing the Cash on Delivery"\
                                "Your Money will be collected at the time of delivery"
        else:
            fulfilment_text = "Some error in Database"

        return JSONResponse(content={
        "fulfillmentText": fulfilment_text
        })
    
    
    #then other methods are redirected to razorpay payment gateway

    fulfilment_text = f"Thank you for choosing the payment method : {payment_meth}"\
                    "Your Money will be charged"
    

    try:
        print(inprogress_userdetails)
        name = inprogress_userdetails[session_id]['name']
        print(name)
        orderid = db_mongodb.get_order_id_mob(inprogress_userdetails[session_id])
        print(orderid)
        p_met = payment_meth[0]
        #order id will be passed as a parameter and method of payment fro backend
        fulfilment_text = f"http://localhost:8000/paymentgateway/{p_met}/{orderid}" \
                            "Click or copy the above url open in your browser for payment gateway"
              
    except:
        fulfilment_text = "Some error occurred while trying pls start from new order"

    

    return JSONResponse(content={
        "fulfillmentText": fulfilment_text
    })


@app.get("/paymentgateway/{p_met}/{orderid}", response_class=HTMLResponse)
def read_root(request: Request):

    # get the orderid from the req parameter and get the basci details and put it in the data
    item_id = request.path_params['orderid']
    payment_meth = request.path_params['p_met']
    print(payment_meth)
    print("From payment gateway")
    print(item_id)

    # things to get for nxt step: totalamt , name , orderid
    totalorderamt = db_mongodb.get_total_order(item_id)
    uname = db_mongodb.get_name_with_orderid(item_id)



    # Initialize Razorpay client
    razorpay_client = razorpay.Client(auth=("rzp_test_AZ9LyozDGv5aSK", "k7q5Fkbd9EAoJaJ5JPl5dzrH"))

    data = {
        
    "amount": int(totalorderamt) * 100,
    "currency": "INR",
    "receipt": str(uname)+"-"+str(item_id),
    "notes": {
        "key1": "value3",
        "key2": "value2"
        }
    }

    totalorderamt = totalorderamt * 100

    payment = razorpay_client.order.create(data = data)

    print(totalorderamt, uname , item_id , payment_meth)

    # Render the HTML template using the Jinja2Templates instance
    return templates.TemplateResponse("payment.html", {"request": request ,"payment":payment,
                                                    "orderid": item_id ,"amount":totalorderamt
                                                    ,"user_name":uname,"payment_method":payment_meth})

@app.post("/api/endpoint")
async def receive_json_data(json_data: dict):
    # Process the received JSON data
    print("Received JSON data:", json_data)

    # Perform any processing or validation as needed
    itemid = json_data["item_id"]
    payment_method = json_data["payment_method"]
    order_id = json_data["order_id"]
    payment_id = json_data["payment_id"]
    signature = json_data["signature"]

    print(itemid , payment_method , order_id , signature , payment_id)

   
    try:
        res = db_mongodb.save_payment_details(item_id=itemid, payment_id=payment_id,paid_method=payment_method,
                                        order_id=order_id,signature=signature)
        print(res)
        if (res == 1):
            return {"message": "JSON data received successfully and updated successfully"}
        else:
            return {"message": "Some error occurred while updating in db"
                    }
    except:
             return {"message": "Error in Database"
                    }
    

@app.get("/api/successfulendpoint")
async def successful_page(request: Request):
     return templates.TemplateResponse("successful.html", {"request": request })
   
@app.get("/api/failurendpoint")
async def failure_page(request: Request):
    return templates.TemplateResponse("failure.html", {"request":request})
    

def get_payment_details(parameter,session_id):
    orderid = parameter["number"]
    fullfilment_text = "Can't fetch due to some technical issues"
    try:
        res = db_mongodb.get_payment_details(orderid)
        status = res['status']
        paid_by = res['paid_by']
        reciept = res['reciept']
        fullfilment_text = f"Your Orderid:{int(orderid)}, status:{status}, paid_by:{paid_by}, reciept:{reciept}"\
                            "Thank you for your order"
    except:
        fullfilment_text = "Error fetching payment details"

    return JSONResponse(content={
        "fulfillmentText": fullfilment_text
    })



# iMPORTANT PART TO SAVING THE ORDER IN db
def save_to_db(order: dict):
    # get the new order id
    nxt_order_id = db_mongodb.get_next_orderid()

    fi = []
    qt = []

    # extracting one item and pushing to db
    for fooditems,quantity in order.items():

        fi.append(fooditems)
        qt.append(quantity)

    print(fi,qt,nxt_order_id)

    rcode = db_mongodb.create_orders(
        fi,
        qt,
        nxt_order_id
    )

    if rcode == -1:
        return -1


    return nxt_order_id

