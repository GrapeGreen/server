import flask
import redis
import json
import traceback
import logging
import logging.config
import pymongo


#logging.config.fileConfig('logging.conf')


app = flask.Flask(__name__)
cache = redis.Redis(host = 'redis_meow')
client = pymongo.MongoClient(host = '0.0.0.0')
database = client['csc']
db = database['csc']


def validate_request(action, key, message):
    if action is None or action not in ['GET', 'PUT', 'DELETE']:
        return False
    if key is None or type(key) != str:
        return False
    if action == 'PUT' and message is None:
        return False
    return True


class KeyValueStorage:
    def __init__(self, cache, db):
        self.cache = cache
        self.db = db

    def put(self, key, value):
        logging.debug('Put request for pair [{}, {}]'.format(key, value))
        self.cache.ping()
        if self.cache.exists(key):
            self.cache.set(key, value)
            return True
        self.cache.set(key, value)
        return False

    def get(self, key):
        logging.debug('Get request for key [{}]'.format(key))
        self.cache.ping()
        if self.cache.exists(key):
            return self.cache.get(key)
        logging.warning('No data in cache, proceeding to the db')
        val = self.db.find_one({'key' : key})
        if val is None:
            logging.error('No data in db')
            return None
        logging.debug('Found data in db')
        self.cache.set(key, val['value'])
        return val['value']

    def delete(self, key):
        logging.debug('Delete request for key [{}]'.format(key))
        self.cache.ping()
        if self.cache.exists(key):
            logging.debug('Successful delete')
            self.cache.delete(key)
            return True
        logging.error('Not such key in cache!')
        return False


kvs = KeyValueStorage(cache, db)


@app.route('/')
def handle():
    try:
        action, key, message = [flask.request.args.get(x) for x in ['method', 'key', 'message']]
        logging.info('Incoming request with action = {}, key = {}, message = {}'.format(action, key, message))
        if not validate_request(action, key, message):
            logging.error('Incorrect request: {}'.format(flask.request.query_string))
            return flask.render_template('test.html', message = json.dumps({'status' : 'BAD_REQUEST'}))
        if action == 'GET':
            value = kvs.get(key)
            if value is None:
                return flask.render_template('test.html', message = json.dumps({'status' : 'NOT_FOUND'}))
            else:
                return flask.render_template('test.html', message = json.dumps({'status' : 'OK', 'message' : str(value)}))
        if action == 'PUT':
            if kvs.put(key, str(message)):
                return flask.render_template('test.html', message = json.dumps({'status' : 'OVERWRITTEN'}))
            else:
                return flask.render_template('test.html', message = json.dumps({'status' : 'CREATED'}))
        if action == 'DELETE':
            if kvs.delete(key):
                return flask.render_template('test.html', message = json.dumps({'status' : 'DELETED'}))
            else:
                return flask.render_template('test.html', message = json.dumps({'status' : 'NOT_FOUND'}))
    except KeyboardInterrupt:
        exit(0)
    except:
        logging.error('Something went wrong')
        traceback.print_exc()
        return flask.render_template('test.html', message = json.dumps({'status' : 'INTERNAL_ERROR'}))


if __name__ == '__main__':
    app.run(host = '0.0.0.0')
