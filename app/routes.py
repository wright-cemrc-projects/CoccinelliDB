from flask import Blueprint, render_template, jsonify
from flask_cors import CORS

main = Blueprint('main', __name__)
CORS(main)

@main.route('/')
def index():
    return "Hello, World!"

@main.route('/home', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World"})