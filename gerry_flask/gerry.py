import eventlet
eventlet.monkey_patch()
# without this monkey patch the sockets wouldn't emit
import asyncio
from flask import Flask
from flask_socketio import SocketIO, send, emit

from .database import db_session
from .fish_scales import State, full_JSON, make_feature, make_feature_collection

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['GP_SECRET_KEY']
socketio = SocketIO(app)


@app.teardown_appcontext
def shutdown_session(exception=None):
    """End db_session when app closes."""
    db_session.remove()


def spew(tract_generator, n=10):
    """Spew."""
    features = list(next(tract_generator) for _ in range(n))
    if features:
        feature_collection = make_feature_collection(features)
        emit('tractjson', feature_collection, json=True)
    else:
        print('Spewing complete geojson.')
        fulljson = full_JSON(db_session)
        emit('districtjson', fulljson, json=True)


@socketio.on('subscribeToGeoJson')
def spew_geojson():
    """Spew geojson as each tract is assigned to a district."""
    state = State(db_session, 7)
    criteria = {
        'county': 1,
        'compactness': 1
    }
    print('Building and spewing.')
    tract_generator = state.fill_state(criteria)

    socketio.on_event('gotGeoJson', lambda: spew(tract_generator))
    spew(tract_generator)


if __name__ == '__main__':
    socketio.run(app, log_output=True)
