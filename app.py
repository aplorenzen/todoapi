from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from pymongo import MongoClient
import signal
import sys
import os
import logging
from bson.json_util import ObjectId
from flask_cors import CORS

# configure logging
logger = logging.getLogger('todoapp')
logLevelString = os.getenv('LOG_LEVEL', 'INFO')
logLevel = logging.getLevelName(logLevelString)
if logLevel is None:
    logLevel = logging.INFO
logger.setLevel(logLevel)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

# get mongodb settings
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT', '27017')


# Set up method to handle exit signal
def sigint_handler(signal, frame):
    logger.info("Received SIGINT, exiting...")
    sys.exit(0)


def sigterm_handler(signal, frame):
    logger.info("Received SIGTERM, exiting...")
    sys.exit(0)


# Todo
#   show a single todo item and lets you delete them
class Todo(Resource):
    def get(self, todo_id):
        item = todoCollection.find_one({'_id': {'$in': [ObjectId(todo_id)]}})

        if isinstance(item, dict):
            newId = str(item['_id'])
            del item['_id']
            item['_id'] = newId

        return item

    def delete(self, todo_id):
        result = todoCollection.delete_one({'_id': {'$in': [ObjectId(todo_id)]}})
        return result.raw_result, 204

    def put(self, todo_id):
        args = parser.parse_args()
        todoItem = {'task': args['task'], 'done': args['done']}

        todoCollection.insert_one(todoItem)
        newId = str(todoItem['_id'])
        del todoItem['_id']
        todoItem['_id'] = newId
        return todoItem, 201


# TodoList
#   shows a list of all todos, and lets you POST to update new tasks
class TodoList(Resource):
    def get(self):
        cursor = todoCollection.find({})
        allItems = []
        for item in cursor:
            newId = str(item['_id'])
            del item['_id']
            item['_id'] = newId
            allItems.append(item)

        return allItems

    def post(self):
        args = parser.parse_args()
        todoItem = {'task': args['task'], 'done': args['done']}
        mongoResult = todoCollection.update_one({'_id': ObjectId(args['_id'])}, {"$set": todoItem}, upsert=False)
        return mongoResult.raw_result, 201


# Setup the flask API app
app = Flask(__name__)
api = Api(app)
CORS(app)

api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<string:todo_id>')

mongoClient = MongoClient("mongodb://%s:%s/" % (MONGO_HOST, MONGO_PORT))
mongoDb = mongoClient["todo"]
todoCollection = mongoDb["todo"]

parser = reqparse.RequestParser()
parser.add_argument('task', type=str, help='The task title')
parser.add_argument('done', type=bool, help='Has the task been completed?')
parser.add_argument('_id', type=str, help='Id of the task')

if __name__ == '__main__':
    logger.info("Starting service")
    # Hook up the exit signal handlers for SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    app.run(host='0.0.0.0')
