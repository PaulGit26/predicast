import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

_lock  = threading.Lock()
_state = {'status': 'idle', 'started_at': None, 'finished_at': None, 'error': None, 'logs': []}


def _log(msg):
    with _lock:
        _state['logs'].append(msg)
        if len(_state['logs']) > 1000:
            _state['logs'] = _state['logs'][-1000:]
    print(msg, flush=True)


def _execute():
    try:
        import run_pipeline  # lazy: load heavy ML libs only when pipeline runs
        run_pipeline.main(log_callback=_log)
        with _lock:
            _state['status'] = 'done'
            _state['finished_at'] = datetime.now(timezone.utc).isoformat()
    except Exception as exc:
        with _lock:
            _state['status'] = 'error'
            _state['error'] = str(exc)
            _state['finished_at'] = datetime.now(timezone.utc).isoformat()
        _log(f'[ERROR] {exc}')


@app.get('/health')
def health():
    return jsonify({'status': 'ok'})


@app.post('/run')
def run():
    with _lock:
        if _state['status'] == 'running':
            return jsonify({'error': 'Pipeline ya está en ejecución'}), 409
        _state.update({
            'status': 'running',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'finished_at': None,
            'error': None,
            'logs': [],
        })
    threading.Thread(target=_execute, daemon=True).start()
    return jsonify({'status': 'started'})


@app.get('/status')
def status():
    with _lock:
        return jsonify(dict(_state))


@app.get('/logs')
def logs():
    with _lock:
        return jsonify(_state['logs'])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
