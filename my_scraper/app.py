from flask import Flask, render_template, request, jsonify
import sys
import os
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(__file__))

os.environ['PYTHONIOENCODING'] = 'utf-8'

app = Flask(__name__)

engine = None

def init_engine():
    global engine
    if engine is not None:
        return engine
    
    from connecting_trains import ConnectionEngine
    import io
    import contextlib
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    
    try:
        engine = ConnectionEngine()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    return engine

@app.route('/')
def index():
    eng = init_engine()
    stations = sorted(eng.all_stations)
    return render_template('index.html', stations=stations)

@app.route('/api/connections')
def get_connections():
    source = request.args.get('source', '')
    destination = request.args.get('destination', '')
    
    if not source or not destination:
        return jsonify({'error': 'Please select both source and destination'}), 400
    
    eng = init_engine()
    connections = eng.get_connections(source, destination)
    
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        elif hasattr(obj, 'item'):
            return obj.item()
        else:
            return obj
    
    return jsonify({
        'connections': make_serializable(connections),
        'source': source,
        'destination': destination
    })

@app.route('/api/stations')
def get_stations():
    eng = init_engine()
    return jsonify(sorted(eng.all_stations))

if __name__ == '__main__':
    print("\n[INFO] Loading Indian Railway Connection Finder...")
    print("[INFO] Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, port=5000, use_reloader=False)
