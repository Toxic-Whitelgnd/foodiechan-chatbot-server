import mysql.connector

# Define your MySQL database connection parameters
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "tarun_briyani",
}


def get_order_status(order_id):
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(**db_config)

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Define the SQL query to fetch the status for the given order_id
        query = "SELECT status FROM order_tracking WHERE order_id = %s"

        # Execute the query with the provided order_id
        cursor.execute(query, (order_id,))

        # Fetch the result (status)
        result = cursor.fetchone()
        connection.commit()
        if result:
            status = result[0]
            return {"order_id": order_id, "status": status}
        else:
            return {"error": "Order not found"}



    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return {"error": "Database error"}

    finally:
        # Close the cursor and the database connection
        cursor.close()
        # connection.close()

def get_nxt_order_id():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = "Select max(order_id) from orders"
    cursor.execute(query)

    result = cursor.fetchone()[0]

    if result is None:
        return 1
    else:
        return result+1

def insert_to_db(fooditem,quantity,nxtorderid):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.callproc('insert_order_item',(fooditem,quantity,nxtorderid))

        connection.commit()

        cursor.close()

        print("Inserted successfully to the databse")

        return 1

    except mysql.connector.Error as e:

        print(f"Error: {e}")
        connection.rollback()
        return -1

    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
        return -1

def get_total_order(orderid):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = f"Select get_total_order_price({orderid})"

        cursor.execute(query)
        result = cursor.fetchone()[0]
        cursor.close()

        return result

    except mysql.connector.Error as e:

        print(f"Error: {e}")
        connection.rollback()
        return -1

def insert_into_tracking(orderid,status):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = "Insert into order_tracking values (%s,%s) "

    cursor.execute(query,(orderid,status))

    connection.commit()
    cursor.close()

def update_the_tracking(orderid,status1):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = f"""update order_tracking set status ='{status1}' where order_id = {orderid};"""

    cursor.execute(query)

    connection.commit()

    cursor.close()
    print(f"updated the #{orderid} with the status of {status1} to database")

def get_progress_order_tracking():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = """select order_id from order_tracking where status ='Your order is in prepration' """

    cursor.execute(query)

    result = cursor.fetchall()


    cursor.close()
    print("details have been fetched")
    ls= []
    ls.append(result)
    return ls

def get_delivered_order():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = """select order_id from order_tracking where status ='Your order has been successfully delivered' """

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    print("details have been fetched")
    ls = []
    ls.append(result)
    return ls

def get_dispatched_order():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = """select order_id from order_tracking where status ='Your order has been dispatched' """

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    print("details have been fetched")
    ls = []
    ls.append(result)
    return ls

def get_out_for_delivery():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    query = """select order_id from order_tracking where status ='Your order is out for delivery' """

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    print("details have been fetched")
    ls = []
    ls.append(result)
    return ls

def save_userdetails(ud: dict , oid : int):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    un = ud['name']
    um = ud['mobileno']
    ua = ud['address']

    query = 'Insert into user_details values (%s,%s,%s,%s)'

    cursor.execute(query,(oid,un,um,ua));

    connection.commit()

    cursor.close()

    print("user detail saved successfullly")


# insert into food_items values(1,"chicken briyani",100),
# (2,"mutton briyani",120),(3,"prawn briyani",150),(4,"veg briyani",80),(5,"panner briayni",80),(6,"egg briyani",90),
# (7,"chicken fried rice",80),(8,"pepper chicken",130),(9,"chicken tikka masala",150),(10,"panner starter",120),
# (11,"egg gravy",100);

