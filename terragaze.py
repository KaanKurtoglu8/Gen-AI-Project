from flask import Flask, render_template, request, session, redirect, url_for, send_file, jsonify
import os
import openai
import numpy as np
from flask_session import Session
from wtforms import StringField, SubmitField
import cv2
import base64
import markdown
import api_key

openai.api_key = api_key.API_KEY

app =  Flask(__name__)
app.secret_key = "hello"

Session(app)

image_in_memory  = None
messages_list = []
initial_output = ""
user_response = ""
bot_response = ""
chat_history = []

system_prompt = """You are an AI that specializes in analyzing images of tourist 
attractions and landmarks, uploaded by tourists. Identify the name of the tourist attraction. 
Give brief, interesting information and some historical facts about there. If you are not sure about your 
identification, don't make a guess, express that you could not identified the landmark, and feel
free to ask the user some extra information to identify correctly. If you are in doubt, ask the name of the city. 
If the uploaded image is not a tourist attraction/landmark, let the user know."""

temperature_variable = 0.7 
max_tokens_variable = 3000


@app.route('/')
def index():
    global image_in_memory 
    image_in_memory  = None

    return render_template("index.html")


@app.route('/upload', methods=['GET','POST'])
def upload():
    global image_in_memory, messages_list, initial_output
    messages_list = []
    image_in_memory = None

    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400
    
    # Save the image to a global variable
    image_in_memory = base64.b64encode(file.read()).decode("utf-8")
    
    # Getting the initial output of GPT
    messages_list = [
        {'role': 'system', 'content': system_prompt},

        {"role": "user", "content": [
            {"type": "text", "text": "Here is the image of the tourist attraction:"},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{image_in_memory}"}
            }
        ]}
    ]

    response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages_list,
            temperature= temperature_variable,
            max_tokens= max_tokens_variable
        )
    
    # Extracting the initial output to a global variable
    initial_output = response.choices[0].message.content
    initial_output = initial_output.replace('"', "'")

    # Appending GPT's initial output to our messages_list
    messages_list.append({"role": "assistant", "content": initial_output})

    initial_output = markdown.markdown(initial_output)

    # Redirect to /chat page
    return redirect(url_for('chat'))


@app.route('/get', methods=['GET', 'POST']) 
def get():
    global messages_list, user_response
    user_response = request.form["msg"] # Getting the user input
    messages_list.append({"role": "user", "content": user_response}) # Appending user input to messages_list

    return get_openai_response(messages_list)


def get_openai_response(msg_list):
    global messages_list, bot_response, chat_history

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=msg_list,
        temperature=temperature_variable,
        max_tokens=max_tokens_variable)

    bot_response = response.choices[0].message.content # Getting the GPT output
    messages_list.append({"role": "assistant", "content": bot_response})

    return markdown.markdown(bot_response)





@app.route('/chat', methods=['GET','POST'])
def chat():
    global image_in_memory, initial_output, messages_list, user_response, bot_response

    #if image_in_memory is None:
    #    return "No image uploaded", 400
    # initial_output = markdown.markdown(initial_output)
    
    return render_template('chat.html', image_in_memory=image_in_memory,
                               initial_output=initial_output.strip().replace('\n', '<br>'), user_response=user_response, bot_response=bot_response)



@app.route('/home')
def home():
    global image_in_memory, messages_list, initial_output
    
    #image_in_memory = None
    #messages_list = []
    #initial_output = ""
    return render_template("index.html")


@app.route('/about')
def about():

    return render_template("about.html")

@app.route('/how_to_use')
def how_to_use():

    return render_template("how_to_use.html")

@app.route('/contact')
def contact():

    return render_template("contact.html")


if __name__ == '__main__':
    app.run(debug=True)

