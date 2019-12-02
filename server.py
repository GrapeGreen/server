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
    if key is None or type(key) != str:
        return False
    if action == 'POST' and message is None:
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


@app.route('/', methods = ['GET'])
def handle_get():
    try:
        key, message = [flask.request.args.get(x) for x in ['key', 'message']]
        if not validate_request('GET', key, message):
            return flask.render_template('test.html', message = json.dumps({'status' : 'BAD_REQUEST'})), 400
        value = kvs.get(key)
        if value is None:
            return flask.render_template('test.html', message = json.dumps({'status' : 'NOT_FOUND'})), 404
        else:
            return flask.render_template('test.html', message = json.dumps({'status' : 'OK', 'message' : str(value)})), 200
    except KeyboardInterrupt:
        exit(0)
    except:
        traceback.print_exc()
        return flask.render_template('test.html', message = json.dumps({'status' : 'INTERNAL_ERROR'})), 500


@app.route('/', methods = ['POST'])
def handle_post():
    try:
        key, message = [flask.request.args.get(x) for x in ['key', 'message']]
        if not validate_request('POST', key, message):
            return flask.render_template('test.html', message = json.dumps({'status' : 'BAD_REQUEST'})), 400
        if kvs.put(key, str(message)):
            return flask.render_template('test.html', message = json.dumps({'status' : 'OVERWRITTEN'})), 200
        else:
            return flask.render_template('test.html', message = json.dumps({'status' : 'CREATED'})), 200
    except KeyboardInterrupt:
        exit(0)
    except:
        traceback.print_exc()
        return flask.render_template('test.html', message = json.dumps({'status' : 'INTERNAL_ERROR'})), 500


@app.route('/', methods = ['DELETE'])
def handle_delete():
    try:
        key, message = [flask.request.args.get(x) for x in ['key', 'message']]
        if not validate_request('DELETE', key, message):
            return flask.render_template('test.html', message = json.dumps({'status' : 'BAD_REQUEST'})), 400
        if kvs.delete(key):
            return flask.render_template('test.html', message = json.dumps({'status' : 'DELETED'})), 200
        else:
            return flask.render_template('test.html', message = json.dumps({'status' : 'NOT_FOUND'})), 404
    except KeyboardInterrupt:
        exit(0)
    except:
        traceback.print_exc()
        return flask.render_template('test.html', message = json.dumps({'status' : 'INTERNAL_ERROR'})), 500


if __name__ == '__main__':
    app.run(host = '0.0.0.0')
