//=============== AWS IDs ===============
var userPoolId = "";
var clientId = "";
var region = "";
var identityPoolId = "";
//=============== AWS IDs ===============

// set the focus to the input box
document.getElementById("wisdom").focus();
// Initialize the Amazon Cognito credentials provider
AWS.config.region = region; // Region
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    // Provide your Pool Id here
    IdentityPoolId: identityPoolId,
});

var cognitoUser;
var idToken;
var userPool;

var poolData = {
    UserPoolId: userPoolId,
    ClientId: clientId,
};

var lexruntime = new AWS.LexRuntime();
var lexUserId = "chatbot-demo" + Date.now();
var sessionAttributes = {
    userType: "public",
};

function pushChat() {
    console.log(sessionAttributes);
    // if there is text to be sent...
    var wisdomText = document.getElementById("wisdom");
    if (wisdomText && wisdomText.value && wisdomText.value.trim().length > 0) {
        // disable input to show we're sending it
        var wisdom = wisdomText.value.trim();
        wisdomText.value = "...";
        wisdomText.locked = true;

        // send it to the Lex runtime
        var params = {
            botAlias: "$LATEST",
            botName: "OrderBot",
            inputText: wisdom,
            userId: lexUserId,
            sessionAttributes: sessionAttributes,
        };
        showRequest(wisdom);
        lexruntime.postText(params, function (err, data) {
            if (err) {
                console.log(err, err.stack);
                showError("Error:  " + err.message + " (see console for details)");
            }
            if (data) {
                // capture the sessionAttributes for the next cycle
                sessionAttributes = data.sessionAttributes;
                // show response and/or error/dialog status
                showResponse(data);
            }
            // re-enable input
            wisdomText.value = "";
            wisdomText.locked = false;
        });
    }
    // we always cancel form submission
    return false;
}

function showRequest(daText) {
    var conversationDiv = document.getElementById("conversation");
    var requestPara = document.createElement("P");
    requestPara.className = "userRequest";
    requestPara.appendChild(document.createTextNode(daText));
    conversationDiv.appendChild(requestPara);
    conversationDiv.scrollTop = conversationDiv.scrollHeight;
}

function showError(daText) {
    var conversationDiv = document.getElementById("conversation");
    var errorPara = document.createElement("P");
    errorPara.className = "lexError";
    errorPara.appendChild(document.createTextNode(daText));
    conversationDiv.appendChild(errorPara);
    conversationDiv.scrollTop = conversationDiv.scrollHeight;
}

function showResponse(lexResponse) {
    var conversationDiv = document.getElementById("conversation");
    var responsePara = document.createElement("P");
    responsePara.className = "lexResponse";
    if (lexResponse.message) {
        responsePara.appendChild(document.createTextNode(lexResponse.message));
        responsePara.appendChild(document.createElement("br"));
    }
    if (lexResponse.dialogState === "ReadyForFulfillment") {
        responsePara.appendChild(document.createTextNode("Ready for fulfillment"));
        // TODO:  show slot values
    }
    // else {
    //     responsePara.appendChild(document.createTextNode(
    //         '(' + lexResponse.dialogState + ')'));
    // }
    conversationDiv.appendChild(responsePara);
    conversationDiv.scrollTop = conversationDiv.scrollHeight;
}

function logIn() {
    let buttonType = document.getElementById("admin-button").textContent;
    let username, password
    if (buttonType.includes('Admin')) {
        username = prompt("Enter username: ");
        password = prompt("Enter password");
    }
    
    
    var authenticationData = {
        Username: username,
        Password: password,
    };
    var authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(
        authenticationData
    );
    
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

    var userData = {
        Username: username,
        Pool: userPool,
    };
    cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    if (buttonType.includes('Admin')) {
        cognitoUser.authenticateUser(authenticationDetails, {
            onSuccess: function (result) {
                sessionAttributes["userType"] = "admin";
                document.getElementById("admin-button").textContent = "LogOut";
                console.log("success\n" + result);
            },

            onFailure: function (err) {
                /*logMessage(err.message);*/
                console.log(err);
                alert("Cannot log in");
            },
        });
    } else {
        cognitoUser.signOut();
        document.getElementById("admin-button").textContent = "Admin";
        sessionAttributes['userType'] = 'public';
        console.log("Logged out")
    }
}
