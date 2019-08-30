---
summary: In this tutorial you will create a game contest player, test it, and make it available at a public URL
---

# The Player

[Feedback](https://github.com/GoogleCloudPlatform/serverless-game-contest/issues)


## Introduction

Contestants in the example programming contest create their solutions as web services that make one move at a time. Each move is requested by an external entity sending the service a request with a JSON body specifying the state of the game, and the player service responds with the JSON representation of a single move.

### **The game**

Since the point of this tutorial is learning how to create and deploy a serverless solution, the game to be played is as simple as possible: guess a number. The player is given a minimum and maximum integer and guesses an integer in that range. The player is provided with a history of its prior guesses as well, so it does not need to keep track of them itself.

The same concepts used here can be applied to more sophisticated single or many-player games such as Battleship, hangman, or checkers.

### **Input and output**

The input to the player is an HTTP request sent to a URL chosen by the player, with a JSON body representing the state of the game prior to the move. The JSON object has properties **minimum** (an integer greater than or equal to zero), **maximum** (an integer greater than or equal to **minimum**), and **history** (an array of guesses, in the order they were made). Each guess is an object with properties **guess** (an integer between minimum and maximum, inclusive), and **result** (the string "higher" or "lower"). Example:

```
{
  "minimum": 1,
  "maximum": 10,
  "history": [
    {"guess": 5, "result": "higher"},
    {"guess": 8, "result": "lower"}
  ]
}
```

The output represents the game player's move as an HTTP response with a JSON body containing a single integer, the player's guess. Example:

```
6
```

### **What you will build**

In this tutorial, you're going to build a web service implemented as a Cloud Function. The web service will play the contest game by making a single move in response to a request describing the prior state of the game. Your app will:

* Determine the prior state of the game from the contents of the HTTP request
* Make a guess and return that guess as a single integer

### **What you'll learn**

* How to write and deploy a simple Cloud Function using Python 3.7
* How to test the Cloud Function

### **What you'll need**

* A modern web browser such as  [Chrome](https://www.google.com/chrome/browser/).
* Basic knowledge of the Python programming language


## Getting set up
Duration: 03:00


All software deployed on GCP will be part of a GCP Project. You can use the same project as for other components of the game playing system, or you can create a new project at  [console.cloud.google.com](https://console.cloud.google.com/).

You will work in the Cloud Shell command line environment. Start by opening that environment.

### **Launch the Console and Cloud Shell**

Open the Cloud Console at  [console.cloud.google.com](https://console.cloud.google.com/) and select your project.


## Step 1 - Create a Cloud Function

You will create a Cloud Function triggered by HTTP requests.

1. Using the menu in the top left corner of the console, select **Cloud Functions** from the **Compute** section.
2. If this is the first time you are using Cloud Functions in this project, you will see a message that the Cloud Functions API is not enabled. Click the **Enable API** button to proceed.
3. The next message displays a **Create function** button. Click it to create a new Cloud Function.

Use the displayed Create function page to specify your new Cloud Function.

1. Fill in the name box with **player**.
2. Choose the amount of memory needed. Leave the default value of **256 MB** selected.
3. We will use an **HTTP** trigger. A URL for the function is displayed, in the form https:// *region* - *project_id* .cloudfunctions.net/ *function_name* .
4. Use the **Inline editor** to create a simple function.
5. Select **Python 3.7 (Beta)** as the Runtime. A skeletal Python Cloud Function is already filled in.

Use the inline editor to replace the code skeleton with one that plays the game, shown below. You can edit the function body in **main.py** and a list of required non-standard libraries in **requirements.txt**. Our example does not use any non-standard libraries, so the requirements.txt file will remain empty.

This function will be sent an HTTP POST request whose body is a JSON object with the smallest and largest possible guesses and a list of prior guesses. The function code will make a guess based on that input and return the guess in JSON format. The function code to enter is shown below.

```
import json

def make_guess(request):
    game = request.get_json()

    min = game['minimum']
    max = game['maximum']
    guess = (min + max) // 2

    return json.dumps(guess)
```

Key steps in this function code are:

1. Import the standard **json** module for interpreting the request data and formatting the response. If this were a non-standard module we would have had to add it to **requirements.txt**
2. The request handler function is named **make_guess**. Any valid Python name can be used, but it must be filled in the **Function to execute** field below the code editor.
3. The body of the function retrieves the **`minimum`** and **`maximum`** properties of the JSON request object, calculates the integer average of them to be the guess, and returns the guess as a JSON object. (The JSON version of a number is simply that number.) This is a very bad game player because it ignores the list of previous moves that is sent to it and thus does not learn or improve on subsequent moves.

Fill in the name of the **Function to execute** as **make_guess**, and click the **Create** button. A spinner icon will appear next to the function name near the top of the page. After a few minutes, it should change to a green check mark. Hovering over that icon will show the message **Function is active**.

** *If something goes wrong:* ** * the spinner icon will show a red exclamation point. Click the function name and look at the details of the Deployment failure messages in the General tab to figure out how to fix it and try again.* 


## Step 2 - Test the function

We are now ready to test the function. Click the function name to open the **Function details** page, and then click the **Testing** tab to start.

1. Fill in the **Triggering Event** box with a JSON object representing a request to make a move, as shown below.

```
{
  "minimum": 1,
  "maximum": 10,
  "history": []
}
```

2. Click **Test the function**.
3. The **Output** should show **5**. There should be no quotation marks. If there are, it means that the function incorrectly returned a string instead of an integer.
4. In a few minutes, the most recent **Logs** should be displayed at the bottom of the page.

You can also test with a history of previous guesses to the request, as below.

```
{
  "minimum": 1,
  "maximum": 10,
  "history": [
    {"guess": 5, "result": "higher"},
    {"guess": 8, "result": "lower"}
  ]
}
```

Since this is not a very smart game player, it will not learn from the history of prior guesses and will always return **5**, even though the history shows the right answer at this point must be **6** or **7**.

The function seems to be working as designed.


## Step 3 - Call the function



Perform one last check to make sure the function works properly when invoked via an HTTP POST request using the URL assigned to it. Simply using a web browser to view that URL will result in an error response because the browser's request will not contain a valid JSON body. Instead, you will use the  [curl](https://curl.haxx.se/) command line tool installed in the Cloud Shell. You can use  [Postman](https://www.getpostman.com/) instead if you are more familiar with that tool.

1. Use the code editor to create a file called **game.json** with either of the sample input JSON objects shown above in it.
2. Run the following command in the Cloud Shell, replacing the  *url*  parameter with the actual URL of your cloud function (you can find this URL in the Trigger section of the details page for your function):

```
curl -X POST -H "Content-type: application/json" \
--data-binary @game.json url
```

This command sends an HTTP **`POST`** request to the given ** *url* **. The request has a header that specifies the request body is in **`application/json`** form, and the body itself is the contents of the **`game.json`** file you created.

3. The command should output **`5`**. at the beginning of the following line.  Because the function does not return an end-of-line marker after the response, the prompt for the next command will be displayed immediately after the 5 instead of beginning a new line, such as shown below:

```
5user@host$
```

You have created, deployed, tested, and called a Cloud Function that is a valid **player** for the competition.


