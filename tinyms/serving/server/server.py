# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
import subprocess
import signal
import sys
import logging

from flask import request, Flask, jsonify
from ..servable import predict, servable_search
from ..client import server_started

app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict_server():
    """
    Handle the request sent by client, call the servable_search, predict function in tinyms.serving.servable and return the json result to the client.

    Whether the server started or not will be detected first.

    Returns:
        A json object of predicted result will be sent back to the client.

    Examples:
        >>> # In the client part, the request will be routed and processed here 
        >>> url = "http://127.0.0.1:5000/predict"
        >>> res = requests.post(url=url, headers=headers, data=json.dumps(payload))
    """

    if server_started() is True:
        json_data = request.get_json()
        instance = json_data['instance']
        servable_name = json_data['servable_name']
        strategy = json_data['strategy']

        res = servable_search(servable_name)
        if res['status'] != 0:
            return jsonify(res)
        servable = res['servables'][0]
        res = predict(instance, servable_name, servable['model'], strategy)
        return jsonify(res)
    else:
        return 'No server detected'


@app.route('/servables', methods=['GET'])
def list_servables():
    """
    Handle the list_servables request sent by client, call the servable search in tinyms.serving.servable

    Whether the server started or not will be detected first.

    Returns:
        A json object of servable information in the backend will be sent back to the client.

    Examples:
        >>> # In the client part, the servable search request will be routed and processed here 
        >>> res = requests.get(url=url, headers=headers)
        >>> res_body = res.json()
    """

    if server_started() is True:
        return jsonify(servable_search())
    else:
        return 'No server detected'


def run_flask(host='127.0.0.1', port=5000):
    """
    Start the flask server, only be used to trigger starting the flask server in subprocess.

    Directly calling this function is not recommended, please use start_server(). Only Error message will be displayed.

    Args:
        host (str): the ip address of the flask server
        port (int): the port of the server

    Returns:
        Server Started

    Examples:
        >>> # In the start_server function 
        >>> cmd = ['python -c "from tinyms.serving import run_flask; run_flask()"']
        >>> server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    """

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host=host, port=port)


def start_server(host='127.0.0.1', port=5000):
    """
    Start the flask server in a subprocess.

    Catch the signal of CTRL + D to shutdown, otherwise call shutdown() function to shutdown the server, if the ip and port already in use, server won't start for a second time.

    Args:
        host (str): the ip address of the flask server
        port (int): the port of the server

    Returns:
        Start the server in a sub process.

    Examples:
        >>> # In the client part 
        >>> start_server()
        Server starts at host 127.0.0.1, port 5000
    """

    if server_started() is True:
        print('Server already started at host %s, port %d'%(host, port))
    else:
        cmd = ['python -c "from tinyms.serving import run_flask; run_flask()"']
        server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        print('Server starts at host %s, port %d' %(host, port))

    def signal_handler(signal, frame):
        shutdown()    
        sys.exit(0)
    
    for sig in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM]:
        signal.signal(sig, signal_handler)
   

def shutdown():
    """
    Shutdown the flask server.

    Search fot the pid of the process running on port 5000, and kill it. This function will be automatically called when SIGINT, SIGHUP and SIGTERM signals catched.

    Returns:
        A string message of server shutting down or not.

    Examples:
        >>> # In the client part, after predict()
        >>> shutdown()
        'Server shutting down...'
    """

    if server_started() is True:
        server_pid = subprocess.getoutput("netstat -anp | grep 5000 | awk '{printf $7}' | cut -d/ -f1")
        subprocess.run("kill -9 " + str(server_pid), shell=True)
        return 'Server shutting down...'
    else:
        return 'No server detected'
