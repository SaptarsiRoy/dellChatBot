import json
import logging
import re
import pymongo
from bson.objectid import ObjectId


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


def delegate(slots):
    return {
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
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
                message='Enter email address'
            )
        elif "zip" in error:
            return elicit_intent(
                session_attributes=session_attributes,
                message='Enter zip code'
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
            message='Enter proper email id'
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
            message='Enter proper zip code'
        )
    
    updateZipCode(orderId, zipCode)
    return close("Order successfully processed")


def dispatch(intent_request):

    intent_name = intent_request['currentIntent']['name']
    if intent_name == 'orderstatus':
        return order_id(intent_request)
    elif intent_name == 'emailIntent':
        return addCorrectEmailToDB(intent_request)
    elif intent_name == 'zipIntent':
        return addCorrectZipToDB(intent_request)


def lambda_handler(event, context):
    # TODO implement
    print(str(event))

    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
