import boto3
import logging
import csv
import re
import pymongo
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


client = pymongo.MongoClient("mongodb+srv://admin:<password>@dell-orders.qk20r.mongodb.net/dell-orders?retryWrites=true&w=majority")

db = client['dell_orders']
order_status = db.get_collection('order_status')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def checkOrderId(orderId):
    order = order_status.find_one({"_id": ObjectId(orderId)})

    if order is not None:
        return order['message']
    
    return "Order ID is incorrect"

def updateEmail(orderId, email):
    orderId = ObjectId(orderId)
    myquery = {"_id": orderId}
    newvalues = { "$set": { "email": email,"status": "success", "message": "Order processed" } }
    order_status.update_one(myquery, newvalues)

def updateZipCode(orderId, zipCode):
    orderId = ObjectId(orderId)
    myquery = {"_id": orderId}
    newvalues = { "$set": { "zipCode": zipCode,"status": "success", "message": "Order processed" } }
    order_status.update_one(myquery, newvalues)


def close(message):
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": message
            },
        }
    }






def elicit_slots(intent_name, slots, slot_to_elicit, message):
    return {
        "dialogAction": {
            "type": "ElicitSlot",
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {
                "contentType": "PlainText",
                "content": message
            }
        }
    }


def elicit_intent(session_attributes, message):
    return {
        'sessionAttributes': session_attributes,
        "dialogAction": {
            "type": "ElicitIntent",
            "message": {
                "contentType": "PlainText",
                "content": message
            }
        }
    }


def validate_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    return re.fullmatch(regex, email) != None


def validate_zip(zipCode):
    return zipCode.isnumeric()


def order_id(intent_request):
    slots = intent_request['currentIntent']['slots']
    orderId = slots['orderId']
    print(orderId)
    message = checkOrderId(orderId)
    session_attributes = {
        'orderId': orderId
    }
    if "incorrect" in message:
        return elicit_slots(
            intent_name=intent_request['currentIntent']['name'],
            slots=slots,
            slot_to_elicit='orderId',
            message='Enter proper order id'
        )
    else:
        error = message
        if "Email" in error:
            return elicit_intent(
                session_attributes=session_attributes,
                message='Your order is on hold \n please enter correct email address'
            )
        elif "zip" in error:
            return elicit_intent(
                session_attributes=session_attributes,
                message='Your order is on hold \n please enter correct zip code'
            )
        else:
            return close("Order successfully processed")

def addCorrectEmailToDB(intent_request):
    slots = intent_request['currentIntent']['slots']
    orderId = intent_request['sessionAttributes']['orderId']
    email = slots['email']
    print(email)

    if not validate_email(email):
        return elicit_slots(
            intent_name=intent_request['currentIntent']['name'],
            slots=slots,
            slot_to_elicit='orderId',
            message='Please enter proper email id'
        )
    
    updateEmail(orderId, email)
    return close("Order successfully processed")



def addCorrectZipToDB(intent_request):
    slots = intent_request['currentIntent']['slots']
    orderId = intent_request['sessionAttributes']['orderId']
    zipCode = slots['zipCode']
    print(zipCode)

    if not validate_zip(zipCode):
        return elicit_slots(
            intent_name=intent_request['currentIntent']['name'],
            slots=slots,
            slot_to_elicit='orderId',
            message='Please enter proper zip code'
        )
    
    updateZipCode(orderId, zipCode)
    return close("Order successfully processed")

def adminIntent(intent_request):
    slots = intent_request['currentIntent']['slots']
    date = slots['date']

    return fetchDate(date)


def fetchDate(date):
    valDate = datetime.strptime(date, '%Y-%m-%d')
    totalOrders = order_status.count_documents({
        "date": {
            '$gt': valDate,
            '$lt': valDate + timedelta(days=1)
        },

    })
   
    holdOrders = order_status.count_documents({
        "date": {
            '$gt': valDate,
            '$lt': valDate + timedelta(days=1)
        },
        'status': 'hold'
    })
    successfullOrders = totalOrders - holdOrders

    emailErrors = order_status.count_documents({
        "date": {
            '$gt': valDate,
            '$lt': valDate + timedelta(days=1)
        },
        'message': 'Email error'
    })

    zipErrors = order_status.count_documents({
        "date": {
            '$gt': valDate,
            '$lt': valDate + timedelta(days=1)
        },
        'message': 'zip code error'
    })
    message = f'''
    Total orders = {totalOrders}
    Successfull orders = {successfullOrders}
    on hold orders = {holdOrders} 
    email errors = {emailErrors}
    zip code errors = {zipErrors}
    '''

    return close(message)


def generateCSVFile(date):
    valDate = datetime.strptime(date, '%Y-%m-%d')
    print(valDate)
    holdOrders = order_status.find({
        "date": {
            '$gt': valDate,
            '$lt': valDate + timedelta(days=1)
        },
        'status': 'hold'
    })

    listHoldOrders = list(holdOrders)
    data = {
        "data": listHoldOrders
    }
    order_data = data['data']

    # now we will open a file for writing
    data_file = open('data_file.csv', 'w')

    # create the csv writer object
    csv_writer = csv.writer(data_file)

    # Counter variable used for writing
    # headers to the CSV file
    count = 0

    for order in order_data:
        if count == 0:

            # Writing headers of CSV file
            header = order.keys()
            csv_writer.writerow(header)
            count += 1

        # Writing data of CSV file
        csv_writer.writerow(order.values())

    data_file.close()

def mailCSV(email, sub):
    fromaddr = "saptarsiroy0@gmail.com"
    toaddr = email
    aws_region = "us-east-1"
    client = boto3.client('ses',region_name=aws_region)
    
    # instance of MIMEMultipart
    msg = MIMEMultipart()
    
    # storing the senders email address  
    msg['From'] = fromaddr
    
    # storing the receivers email address 
    msg['To'] = toaddr
    
    # storing the subject 
    msg['Subject'] = sub
    
    # string to store the body of the mail
    body = "Find the attachment below"
    
    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))
    
    # open the file to be sent 
    filename = "data_file.csv"
    attachment = open("data_file.csv", "rb")
    
    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')
    
    # To change the payload into encoded form
    p.set_payload((attachment).read())
    
    # encode into base64
    encoders.encode_base64(p)
    
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    
    # attach the instance 'p' to instance 'msg'
    msg.attach(p)

    

def sendEmail(intent_request):
    slots = intent_request['currentIntent']['slots']
    email = slots['email']
    date = slots['date']
    generateCSVFile(date)
    mailCSV(email, sub=f'order pattern for {date}')


def dispatch(intent_request):
     # userType = intent_request['sessionAttributes']['userType']
    userType = 'admin'
    if userType == 'public':
        intent_name = intent_request['currentIntent']['name']
        if intent_name == 'orderstatus':
            return order_id(intent_request)
        elif intent_name == 'emailIntent':
            return addCorrectEmailToDB(intent_request)
        elif intent_name == 'zipIntent':
            return addCorrectZipToDB(intent_request)
        else:
            return close('check session attributes')
    
    else:
        intent_name = intent_request['currentIntent']['name']
        if intent_name == 'AdminIntent':
            return adminIntent(intent_request)
        elif (intent_name == 'adminEmailIntent'):
            return sendEmail(intent_request)
    


def lambda_handler(event, context):
    # TODO implement
    print(str(event))

    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
