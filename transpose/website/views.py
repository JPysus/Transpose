from flask import Blueprint, render_template, request
from .translator import translate, prettier
import random

example_list = [
    "Product of a number, 5 less than 1, 1 and sum of 4, a number, and seventy seven, times 4",
    "y added to the product of 2, forty four, eight, and a number.",
    "2y plus the product of two, 4, eight and twice x",
    "Three diminished by the sum of two and four",
    "Quotient of a number and a sum of 4, a number, and 7, times 4"
]

views = Blueprint('views', __name__)
@views.route('/')
def index():
	example_sent = example_list[random.randint(0, len(example_list) - 1)]
	return render_template('home.html', translation="", example_sent = example_sent, last_input = example_sent)

@views.route('/Home')
def home():
	example_sent = example_list[random.randint(0, len(example_list) - 1)]
	return render_template('home.html', translation="", example_sent = example_sent, last_input = example_sent)

@views.route('/Learn')
def learn():
	return render_template('learn.html')
    
@views.route('/How_To_Use')
def how_to_use():
	return render_template('how_to_use.html')
    
@views.route('/About_Us')
def about_us():
	return render_template('about_us.html')

@views.route('/_submit_sentence', methods=['POST'])
def submit_sentence():
	sentence = request.form.get('sentence')
	lis = translate(sentence)
	print(lis)
	if lis == None:
		lis = "No Translation: Input Unrecognized"
	elif type(lis) is list:
		temp = "<h5><b>Output:</b></h5>"
		if len(lis) > 1:
		    temp += "<h5>Ambiguous Sentence</h5>"
		temp += "<br>".join([prettier(i) for i in lis])
		lis = temp
	return lis
