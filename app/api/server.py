import threading
import requests
import argparse

from flask import Flask, request, jsonify, abort
from app.api.utils import config_parser
from app.db.exceptions import ParametrNotFoundException, ModelProblems
from app.db.interaction.interaction import  DbConnection


class Server:

    def __init__(self, host, port, db_host, db_port, user, password, db_name):
        self.host = host
        self.port = port

        self.db_connect = DbConnection(
            host=db_host,
            user=user,
            password=password,
            database=db_name
        )

        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.get_home)
        self.app.add_url_rule('/get_models', view_func=self.get_models_info)
        self.app.add_url_rule('/create_model', view_func=self.add_model_info, methods=['POST'])
        self.app.add_url_rule('/test_zapros', view_func=self.test, methods=['POST'])

        self.app.register_error_handler(404, self.page_not_found)

    def test(self):
        request_body = dict(request.json)
        print(request_body)
        return f'Success added', 201

    def page_not_found(self, err_description):
        return jsonify(error=str(err_description)), 404

    def run_server(self):
        self.server = threading.Thread(target=self.app.run, kwargs={'host': self.host, 'port': self.port})
        self.server.start()
        return self.server

    def get_home(self):
        return 'Hello, api server!'

    def get_models_info(self):
        try:
            models_info = self.db_connect.get_models_info()
            return models_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    def add_model_info(self):
        model_info = dict(request.json)
        model_id = self.db_connect.create_model(
            model_description=model_info['Description'],
            model_title=model_info['Title'],
            in_flows=model_info['InputFlows'],
            out_flows=model_info['OutputFlows'],
            default_params=model_info['DefaultParameters'],
            extra_params=model_info['ExtraParameters'],
            calculations = model_info['Expressions']
        )
        return f'Success added {model_id}', 201


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, dest='config')

    args = parser.parse_args()

    config = config_parser(args.config)

    server_host = config['SERVER_HOST']
    server_port = config['SERVER_PORT']

    db_host = config['DB_HOST']
    db_port = config['DB_PORT']
    db_user = config['DB_USER']
    db_password = config['DB_PASSWORD']
    db_name = config['DB_NAME']

    server = Server(
        host=server_host,
        port=server_port,
        db_host=db_host,
        db_port=db_port,
        user=db_user,
        password=db_password,
        db_name=db_name
    )
    server.run_server()
