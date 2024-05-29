# from flask import Flask
from lytix_py.LLLogger.LLogger import LLogger
from lytix_py.MetricCollector.MetricCollector import MetricCollector

# app = Flask(__name__)

# @app.route('/sampleEndpoint')
# def hello_world():
#     return 'Hello, World!'

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    test = MetricCollector()
    logger  = LLogger("test-logger")
    # test.increment("refresh", 1, {"env": "python"})
    logger.info("Hello world")
    logger.warn("wtf")
