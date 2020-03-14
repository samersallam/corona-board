from data_visualization import render_dashboard
from flask import Flask
import codecs	

application = Flask(__name__)
title = 'Corona Board'

@application.route('/')
def bokeh():
	file_name = "template/dash_board.html"
	render_dashboard(file_name = file_name)
	f = codecs.open(file_name, 'r')
	layout = f.read()
	
	return 	layout


if __name__ == '__main__':
	application.run(debug=True)
