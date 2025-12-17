from flask import Flask,render_template
import os
import yaml


web = Flask(__name__)

@web.route('/')
def homepage():
    return render_template('index.html')

@web.route('/')
def 