import json
import random
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def validate(orderId):
    if len(orderId) < 5:
        return False
    return True


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


def checkDb(orderId):
    return 3
    


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


def elicit_intent(message):
    return {
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
    if not validate(orderId):
        return elicit_slots(
            intent_name=intent_request['currentIntent']['name'],
            slots=slots,
            slot_to_elicit='orderId',
            message='Enter proper order id'
        )
    else:
        error = checkDb(orderId)
        if error == 1:
            return elicit_intent(
                message='Enter email address'
            )
        elif error == 2:
            return elicit_intent(
                message='Enter zip code'
            )
        else:
            return close("Order successfully processed")

def addCorrectEmailToDB(intent_request):
    slots = intent_request['currentIntent']['slots']
    email = slots['email']
    print(email)

    if not validate_email(email):
        return elicit_slots(
            intent_name=intent_request['currentIntent']['name'],
            slots=slots,
            slot_to_elicit='orderId',
            message='Enter proper email id'
        )
    return close("Order successfully processed")



def addCorrectZipToDB(intent_request):
    slots = intent_request['currentIntent']['slots']
    zipCode = slots['zipCode']
    print(zipCode)

    if not validate_zip(zipCode):
        return elicit_slots(
            intent_name=intent_request['currentIntent']['name'],
            slots=slots,
            slot_to_elicit='orderId',
            message='Enter proper zip code'
        )
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
