import threading
import requests
import argparse

from flask import Flask, request, jsonify, abort
from app.api.utils import config_parser
from app.db.exceptions import ParametrNotFoundException, ModelProblems
from app.db.interaction.interaction import DbInteraction, DbConnection


class Server:

    def __init__(self, host, port, db_host, db_port, user, password, db_name):
        self.host = host
        self.port = port

        self.db_interaction = DbInteraction(
            host=db_host,
            port=db_port,
            user=user,
            password=password,
            db_name=db_name
        )

        self.db_connect = DbConnection(
            host=db_host,
            user=user,
            password=password,
            database=db_name
        )

        self.app = Flask(__name__)
        self.app.add_url_rule('/shutdown', view_func=self.shutdown)
        self.app.add_url_rule('/', view_func=self.get_home)
        self.app.add_url_rule('/home', view_func=self.shutdown)
        self.app.add_url_rule('/add_parametr', view_func=self.add_parametr_info, methods=['POST'])
        self.app.add_url_rule('/get_parametr/<parametr_id>', view_func=self.get_parametr_info)
        self.app.add_url_rule('/edit_parametr/<parametr_id>', view_func=self.edit_param_info, methods=['PUT'])

        self.app.add_url_rule('/get_envs', view_func=self.get_envs_info)
        self.app.add_url_rule('/get_models', view_func=self.get_models_info)
        self.app.add_url_rule('/create_model', view_func=self.add_model_info, methods=['POST'])
        self.app.add_url_rule('/test_zapros', view_func=self.test, methods=['POST'])
    #    self.app.add_url_rule('/get_params_env/<parametr_id>', view_func=self.get_parametr_info)
    #    self.app.add_url_rule('/create_model', view_func=self.create_model, methods=['POST'])

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

    def shutdown_server(self):
        request.get(f'http://{self.host}:{self.port}/shutdown')

    def shutdown(self):
        terminate_func = request.environ.get('werkzeug.server.shutdown')
        if terminate_func:
            terminate_func()

    def get_home(self):
        return 'Hello, api server!'

    def add_parametr_info(self):
        request_body = dict(request.json)
        add_parametr_id = request_body['id']
        add_title = request_body['title']
        add_symbol = request_body['symbol']
        add_unit = request_body['units']
        add_type = request_body['param_type']
        self.db_interaction.add_param_info(
            parametr_id=add_parametr_id,
            title=add_title,
            symbol=add_symbol,
            unit=add_unit,
            type=add_type
        )
        return f'Success added {add_parametr_id}', 201

    def get_parametr_info(self, parametr_id):
        try:
            parametr_info = self.db_interaction.get_parametr_info(parametr_id)
            return parametr_info, 200
        except ParametrNotFoundException:
            abort(404, description='Parametr not found')

    def edit_param_info(self, parametr_id):
        request_body = dict(request.json)
        #new_parametr_id = request_body['parametrid']
        new_title = request_body['title']
        new_symbol = request_body['symbol']
        new_unit = request_body['unit']
        new_type = request_body['type']
        self.db_interaction.edit_parametr_info(
            parametr_id=parametr_id,
            #new_parametr_id=new_parametr_id,
            new_title=new_title,
            new_symbol=new_symbol,
            new_unit=new_unit,
            new_type=new_type
        )
        return f'Success edited {parametr_id}', 200


    def get_envs_info(self):
        try:
            envs_info = self.db_connect.get_envs_info()
            return envs_info, 200
        except ParametrNotFoundException:
            abort(404, description=' envs not found')

    def get_models_info(self):
        try:
            models_info = self.db_connect.get_models_info()
            return models_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    def add_model_info(self):
        model_info = dict(request.json)
        print(model_info)
        model_title = model_info['Title']
        model_description = model_info['Description']
        in_flow_count = len(model_info['InputFlows'])
        out_flow_count = len(model_info['OutputFlows'])

        # in_flows = []
        # for flow in model_info['InputFlows']:
        #     flow_key = ['FlowVariableIndex', 'Enviroment']
        #     flows = []
        #     for key in flow_key:
        #         flows.append(flow[key])
        #     in_flows.append(flows)  # формируется список списков со всеми параметрами потоков
        #
        # out_flows = []
        # for flow in model_info['OutputFlows']:
        #     flow_key = [x for x in flow.keys()]
        #     flows = []
        #     for key in flow_key:
        #         flows.append(flow[key])
        #     out_flows.append(flows)  # формируется список списков со всеми параметрами потоков
        #
        # default_params = []
        # for def_param in model_info['DefaultParameters']:
        #     def_param_key = [x for x in def_param.keys()]
        #     params = []
        #     for key in def_param_key:
        #         params.append(def_param[key])
        #     default_params.append(params)  # формируется список списков со всеми параметрами по умолчанию
        #
        # extra_params = []
        # for extr_param in model_info['ExtraParameters']:
        #     extr_param_key = [x for x in extr_param.keys()]
        #     params = []
        #     for key in extr_param_key:
        #         params.append(extr_param[key])
        #     extra_params.append(params)  # формируется список списков со всеми дополнительными параметрами
        #
        # calculations = []
        # for calculation in model_info['Expressions']:
        #     calculation_key = [x for x in calculation.keys()]
        #     params = []
        #     for key in calculation_key:
        #         params.append(calculation[key])
        #     calculations.append(params)  # формируется список списков со всеми расчетными выражениями

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
