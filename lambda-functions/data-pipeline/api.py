import json
from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/helloworld')
def hello():
    response = {
        "statusCode": 200,
        "body": "hi"
    }
    id = request.args.get('id')

    return f"Hi {id}!"

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
