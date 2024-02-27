from flask import Flask

server = Flask(__name__)

@server.route('/search')
def hello_world():
    return 'hello elasticsearch'