from flask import Blueprint, render_template, request
from .translator import translation
from .translator import prettier
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
	return render_template('index.html', translation="", example_sent = example_sent, last_input = example_sent)

@views.route('/_submit_sentence', methods=['POST'])
def submit_sentence():
	sentence = request.form.get('sentence')
	lis = translation(sentence)
	try: 
		lis = prettier(lis)
	except:
		if type(lis) is list and all(lis):
			temp = "<h5>Ambiguous Sentence</h5><br>"
			temp += "<br>".join([prettier(i) for i in lis])
			lis = temp
	return lis
