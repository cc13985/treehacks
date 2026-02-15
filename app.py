"""
Flask backend: run band power extraction via /api/run.
"""

import os
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/run', methods=['POST', 'GET'])
def run_extraction():
    mat_path = os.environ.get('S52_MAT_PATH')
    try:
        from extract_band_power import run_analysis
        result = run_analysis(mat_path=mat_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
