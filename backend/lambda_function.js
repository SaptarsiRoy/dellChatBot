/*
This file contains lambda function code for integration
*/

// Import the MongoDB driver
const {ObjectId, MongoClient} = require("mongodb");
// Define our connection string. Info on where to get this will be described below. In a real world application you'd want to get this string from a key vault like AWS Key Management, but for brevity, we'll hardcode it in our serverless function here.
const MONGODB_URI =
  "mongodb+srv://admin:saptarsi22@dell-orders.qk20r.mongodb.net/myFirstDatabase?retryWrites=true&w=majority";
// Once we connect to the database once, we'll store that connection and reuse it so that we don't have to connect to the database on every request.
let cachedDb = null;
async function connectToDatabase() {
  if (cachedDb) {
    return cachedDb;
  }
  // Connect to our MongoDB database hosted on MongoDB Atlas
  const client = await MongoClient.connect(MONGODB_URI);
  // Specify which database we want to use
  const db = await client.db("dell_orders");
  cachedDb = db;
  return db;
}

//shows the order patterns to admin for a given day
async function showOrderPatternsDay(db, intent_request) {
    let queryDate = new Date(intent_request['currentIntent']['date']);
    let nextDate = new Date(queryDate.getFullYear(), queryDate.getMonth(), queryDate.getDate() + 1);
    
    //queries the number of successfull orders on a particular date
    let successfullOrders = await db.collection("order_status").find({
        "date": { "$gte": queryDate, "$lt": nextDate }, 
        "status": "success"
    }).count();
    
    //queries the number of orders on hold on a particular date
    let holdOrders = await db.collection("order_status").find({
        "date": { "$gte": queryDate, "$lt": nextDate }, 
        "status": "hold"
    }).count();
    
    //queries the number of orders having incorrect email
    let incorrectEmailOrders = await db.collection("order_status").find({
        "date": { "$gte": queryDate, "$lt": nextDate }, 
        "status": "Email error"
    }).count();
    
    //queries the number of orders having incorrect zipcode
    let incorrectZipOrders = await db.collection("order_status").find({
        "date": { "$gte": queryDate, "$lt": nextDate }, 
        "status": "zip code error"
    }).count();

    return patterns({
        successfullOrders,
        holdOrders,
        incorrectEmailOrders,
        incorrectZipOrders
    });
    
}

//shows the order patterns to admin for a given month
async function showOrderPatternsMonth(db, intent_request) {
    let queryYear = intent_request['currentIntent']['year'];
    let queryMonth = new Date(queryYear, intent_request['currentIntent']['month']);
    let nextMonth = new Date(queryYear, queryMonth + 1);
    
    //queries the number of successfull orders on a particular date
    let successfullOrders = await db.collection("order_status").find({
        "date": { "$gte": queryMonth, "$lt": nextMonth }, 
        "status": "success"
    }).count();
    
    //queries the number of orders on hold on a particular date
    let holdOrders = await db.collection("order_status").find({
        "date": { "$gte": queryMonth, "$lt": nextMonth }, 
        "status": "hold"
    }).count();
    
    //queries the number of orders having incorrect email
    let incorrectEmailOrders = await db.collection("order_status").find({
        "date": { "$gte": queryMonth, "$lt": nextMonth }, 
        "status": "Email error"
    }).count();
    
    //queries the number of orders having incorrect zipcode
    let incorrectZipOrders = await db.collection("order_status").find({
        "date": { "$gte": queryMonth, "$lt": nextMonth }, 
        "status": "zip code error"
    }).count();

    return patterns({
        successfullOrders,
        holdOrders,
        incorrectEmailOrders,
        incorrectZipOrders
    });
    
}

//validates if order id is correct or not
async function checkOrderId(db, orderId) {
    let userOrder = await db.collection("order_status").findOne({"_id": ObjectId(orderId)});
    
    if(userOrder === null) {
       return "Order ID is incorrect";
    }
    
    return userOrder.message;
}

//updates the email id for a particular order
async function updateEmail(db, orderId, email) {
  await db.collection("order_status").update({"_id": ObjectId(orderId)},
  {
    "$set": {
      "email": email
    }
  });
}

//updates the zip code for a particular order
async function updateZipCode(db, orderId, zipCode) {
  await db.collection("order_status").update({"_id": ObjectId(orderId)},
  {
    "$set": {
      "zipCode": zipCode
    }
  });
}

//returns a json showing the patterns for admin
function patterns(message) {
     return {
        "dialogAction": {
            "type": "Patterns",
            "message": {
                "contentType": "PlainText",
                "content": message
            },
        }
    };
}

//returns a json when request is fullfiled
function close(message)  {
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": message
            },
        }
    };
}

//returns a message when elicit slots are present
function elicit_slots(intent_name, slots, slot_to_elicit, message) {
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
    };
}

//returns a json when elicit intents are there
function elicit_intent(session_attributes, message) {
    return {
        'sessionAttributes': session_attributes,
        "dialogAction": {
            "type": "ElicitIntent",
            "message": {
                "contentType": "PlainText",
                "content": message
            }
        }
    };
}



function delegate(slots) {
    return {
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    };
}

//uses regex to validate an email
function validate_email(email) {
	return String(email)
    .toLowerCase()
    .match(
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    );
}

//used to validate a zipcode
function validate_zip(zipCode) {
    return +zipCode.isNaN();
}

//processes an order
async function order_id(db, intent_request) {
    let slots = intent_request['currentIntent']['slots'];
    let orderId = slots['orderId'];
    let message = await checkOrderId(db, orderId);
    let session_attributes = {
        'orderId': orderId
    }
    if (message === "Order ID is incorrect") {
        return elicit_slots(
            intent_request['currentIntent']['name'],
            slots,
            'orderId',
            'Enter proper order id'
        );
    }
    else {
        let error = message
        if ("Email error" === error) {
            return elicit_intent(
                session_attributes,
                'Enter email address'
            );
        }
        else if ("zip code error" === error) {
            return elicit_intent(
                session_attributes,
                'Enter zip code'
            );
        }
        else {
            return close("Order successfully processed");
        }
    }
}

//this function is used to add a correct email to db if its wrong
async function addCorrectEmailToDB(db, intent_request) {
    let slots = intent_request['currentIntent']['slots']
    let orderId = intent_request['sessionAttributes']['orderId']
    let email = slots['email']

    if (validate_email(email) === false) {
        return elicit_slots(
            intent_request['currentIntent']['name'],
            slots,
            'orderId',
            'Enter proper email id'
        );
    }
    
    await updateEmail(db, orderId, email);
    return close("Order successfully processed");
}

//this function adds correct zip code to db if its wrong
async function addCorrectZipToDB(db, intent_request) {
    let slots = intent_request['currentIntent']['slots'];
    let orderId = intent_request['sessionAttributes']['orderId'];
    let zipCode = slots['zipCode'];

    if (validate_zip(zipCode) === false) {
        return elicit_slots(
            intent_request['currentIntent']['name'],
            slots,
            'orderId',
            'Enter proper zip code'
        );
    }
    
    await updateZipCode(db, orderId, zipCode);
    return close("Order successfully processed");
}

//dispatches the correct function based on the intent request
async function dispatch(db, intent_request) {
    let intent_name = intent_request['currentIntent']['name'];
    let userType = intent_request['sessionAttributes']['userType'];

    if(intent_name === 'AdminIntent' && userType === 'admin') {
        return await showOrderPatternsDay(db, intent_request);
    }
    if (intent_name === 'orderstatus') {
        return await order_id(db, intent_request);
    }
    else if (intent_name === 'emailIntent') {
        return await addCorrectEmailToDB(db, intent_request);
    }
    else if (intent_name === 'zipIntent') {
        return await addCorrectZipToDB(db, intent_request);
    }
}

//lambda function handler
exports.handler = async (event, context) => {
  /* By default, the callback waits until the runtime event loop is empty before freezing the process and returning the results to the caller. Setting this property to false requests that AWS Lambda freeze the process soon after the callback is invoked, even if there are events in the event loop. AWS Lambda will freeze the process, any state data, and the events in the event loop. Any remaining events in the event loop are processed when the Lambda function is next invoked, if AWS Lambda chooses to use the frozen process. */
  context.callbackWaitsForEmptyEventLoop = false;
  // Get an instance of our database
  const db = await connectToDatabase();
  // Make a MongoDB MQL Query to go into the movies collection and return the first 20 movies.
  let res = await dispatch(db, event);
  return res;
};