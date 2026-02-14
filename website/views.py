from flask import Blueprint, render_template, request
from .translator import translate as tl, prettier
import random
import json, os
import requests
#top directory
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
views = Blueprint('views', __name__)

@views.route('/')
def index():
	return render_template('index.html')
    
#looks for the file phrases.json
#in static/json directory, using the top directory as a prefix
json_url_phrases = os.path.join(SITE_ROOT, "static/json", "phrases.json")
data_phrases = json.load(open(json_url_phrases))

@views.route('/translate')
def translate():
	example_sent = data_phrases[random.randint(0, len(data_phrases) - 1)]
	return render_template('translate.html', example_list=sorted(data_phrases, key=str.casefold), example_sent = example_sent)

@views.route('/learn')
def learn():
	return render_template('learn.html')

@views.route('/layout')
def layout():
	return render_template('layout.html')

#looks for the file problems.json
#in static/json directory, using the top directory as a prefix
json_url_problems = os.path.join(SITE_ROOT, "static/json", "problems.json")
data_problems = json.load(open(json_url_problems))
json_url_quiz = os.path.join(SITE_ROOT, "static/json", "quiz.json")
data_quiz = json.load(open(json_url_quiz))

@views.route('/practice')
def practice():
	return render_template('practice.html', problems=data_problems, quiz=data_quiz)
    
@views.route('/about_us')
def about_us():
	return render_template('about_us.html')

@views.route('/_submit_sentence', methods=['POST'])
def submit_sentence():
    sentence = request.form.get('sentence')
    print(sentence)
    lis = tl(sentence)
    if type(lis) is list and all(lis):
        temp = "<p><b>Output:</b>"
        if len(lis) > 1:
            temp += "<br/>Ambiguous Sentence"
        temp += "</p>"
        temp += "<br/> <hr/>".join(["`"+prettier(i)+"`" for i in lis])
        lis = temp
    return lis

@views.route('/_steam')
def steam():
	req = requests.get("https://steamcommunity.com/miniprofile/235021538")
	return req.text