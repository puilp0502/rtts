import eventlet
eventlet.monkey_patch()

from flask import Flask, redirect, url_for, session, request, abort, render_template
from flask_socketio import SocketIO
import tweepy

from config import CONSUMER_TOKEN, CONSUMER_SECRET, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)


class ThreadStoppedException(Exception):
    pass


class Listener(tweepy.StreamListener):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def on_data(self, data):
        context = self.context
        # print('[%s] Data received: Topic %s' % (context.sid, context.topic))
        if getattr(context, 'stopped', lambda: False)():
            print('[%s] Stop signal received (%d)' % (context.sid, context.ident))
            raise ThreadStoppedException('Thread stop signal received')
        sid = getattr(context, 'sid', -1)
        greenpool.spawn_n(socketio.emit, 'tweet', data, room=sid)

    def keep_alive(self):
        context = self.context
        print("[%s] keepalive: Topic %s" % (context.sid, context.topic))
        if getattr(context, 'stopped', lambda: False)():
            print('[%s] Stop signal received (%d)' % (context.sid, context.ident))
            raise ThreadStoppedException('Thread stop signal received')

    def on_error(self, status):
        greenpool.spawn_n(socketio.emit, 'error', status, room=self.context.sid)
        return False  # stop stream


class StreamGreenlet(object):
    def __init__(self, sid, topic, auth):
        print('[%s] Thread created with topic: %s' % (sid, topic))
        self.sid = sid
        self.topic = topic
        self.auth = auth

    def run(self):
        l = Listener(self)
        stream = tweepy.Stream(self.auth, l, timeout=180, chunk_size=512)  # 64 / 4 * 30 / 60 = about 8min
        try:
            stream.filter(track=self.topic)
        except ThreadStoppedException:
            print('[%s] Stopping thread..' % self.sid)
            stream.disconnect()
            return


greenlet_dict = {}
greenpool = eventlet.GreenPool(size=1000)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/authenticate')
def authenticate():
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET,
                               'http://rtt.hakk.kr/oauth_callback')
    try:
        redirect_url = auth.get_authorization_url()
        session['request_token'] = auth.request_token
        return redirect(redirect_url)
    except tweepy.TweepError as e:
        print(e)
        return 'Failed to get request token.<br><a href="%s">Go to index</a>' % \
               url_for('hello_world')


@app.route('/revoke')
def revoke():
    try:
        del session['request_token']
        del session['access_token']
        del session['access_token_secret']
    except KeyError:
        pass
    return redirect(url_for('index'))


@app.route('/oauth_callback')
def oauth_callback():
    verifier = request.args.get('oauth_verifier')
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    try:
        token = session['request_token']
        session.pop('request_token')
        auth.request_token = token
    except KeyError:
        abort(401)

    try:
        auth.get_access_token(verifier)
        session['access_token'] = auth.access_token
        session['access_token_secret'] = auth.access_token_secret
        return redirect(url_for('realtime'))
    except tweepy.TweepError as e:
        print(e)
        return 'Failed to get request token.<br><a href="%s">Go to index</a>' % \
               url_for('hello_world')


@app.route('/search')
def realtime():
    if session.get('access_token', None) is None:
        return redirect(url_for('authenticate'))
    return render_template('realtime.html')


@socketio.on('set query')
def update_query(string):
    access_token = session['access_token']
    access_token_secret = session['access_token_secret']
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    auth.set_access_token(access_token, access_token_secret)
    sid = request.sid
    try:
        greenlet_dict[sid].kill(ThreadStoppedException())
        del greenlet_dict[sid]
    except KeyError:
        pass
    if len(greenlet_dict) < 50:
        greenlet = StreamGreenlet(sid,
                                  list(map(lambda x: x.strip(), string.split(','))),
                                  auth)
        greenlet_dict[sid] = greenpool.spawn(greenlet.run)


@socketio.on('disconnect')
def close_connection():
    stop_stream(request.sid)


@socketio.on('stop query')
def stop_query():
    stop_stream(request.sid)


def stop_stream(sid):
    try:
        greenlet_dict[sid].kill()
        del greenlet_dict[sid]
    except KeyError:
        pass


if __name__ == '__main__':
    socketio.run(app)
