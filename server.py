import flask
import redis
import json
import traceback
import logging
import logging.config
import pymongo


#logging.config.fileConfig('logging.conf')


app = flask.Flask(__name__)
cache = redis.Redis(host = 'redis')
db = pymongo.MongoClient(host = '0.0.0.0')['csc']


def validate_request(action, key, message):
    if action is None or action not in ['GET', 'PUT', 'DELETE']:
        return False
    if key is None or type(key) != str:
        return False
    if action == 'PUT' and message is None:
        return False
    return True


def put(key, value):
    logging.debug('Put request for pair [{}, {}]'.format(key, value))
    cache.ping()
    if cache.exists(key):
        cache.set(key, value)
        return True
    cache.set(key, value)
    return False


def get(key):
    logging.debug('Get request for key [{}]'.format(key))
    cache.ping()
    if cache.exists(key):
        return cache.get(key)
    logging.warning('No data in cache, proceeding to the db')
    val = db.mongo_table.find_one({'key' : key})
    if val is None:
        logging.error('No data in db')
        return None
    logging.debug('Found data in db')
    cache.set(key, val['value'])
    return val['value']


def delete(key):
    logging.debug('Delete request for key [{}]'.format(key))
    cache.ping()
    if cache.exists(key):
        logging.debug('Successful delete')
        cache.delete(key)
        return True
    logging.error('Not such key in cache!')
    return False


@app.route('/')
def handle():
    try:
        action, key, message = [flask.request.args.get(x) for x in ['method', 'key', 'message']]
        logging.info('Incoming request with action = {}, key = {}, message = {}'.format(action, key, message))
        if not validate_request(action, key, message):
            logging.error('Incorrect request: {}'.format(flask.request.query_string))
            return flask.render_template('test.html', message = json.dumps({'status' : 'BAD_REQUEST'}))
        if action == 'GET':
            value = get(key)
            if value is None:
                return flask.render_template('test.html', message = json.dumps({'status' : 'NOT_FOUND'}))
            else:
                return flask.render_template('test.html', message = json.dumps({'status' : 'OK', 'message' : str(value)}))
        if action == 'PUT':
            if put(key, str(message)):
                return flask.render_template('test.html', message = json.dumps({'status' : 'OVERWRITTEN'}))
            else:
                return flask.render_template('test.html', message = json.dumps({'status' : 'CREATED'}))
        if action == 'DELETE':
            if delete(key):
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
