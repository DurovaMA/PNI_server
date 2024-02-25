import threading
# import requests
import argparse
import os

from flask import Flask, request, jsonify, abort
from app.api.utils import config_parser
from app.db.exceptions import ParametrNotFoundException, ModelProblems
from app.db.interaction.interaction import DbConnection


class Server:

    def __init__(self, host, port, db_host, db_port, user, password, db_name):
        self.host = host
        self.port = port
        self.db_connect = DbConnection(
            db_host=db_host,
            user=user,
            password=password,
            database=db_name,
            db_port=db_port
        )

        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.get_home)
        self.app.add_url_rule('/get_models', view_func=self.get_models_info)
        self.app.add_url_rule('/get_model_catalog', view_func=self.get_model_catalog_info)
        #self.app.add_url_rule('/get_catalog', view_func=self.get_catalog_info)
        self.app.add_url_rule('/get_info_model/<string:name_model>', view_func=self.get_info_model)
        self.app.add_url_rule('/create_model', view_func=self.add_model_info, methods=['POST'])
        self.app.add_url_rule('/create_schema', view_func=self.add_schema_info, methods=['POST'])
        self.app.add_url_rule('/show_all_schemas', view_func=self.show_all_schemas_info)
        self.app.add_url_rule('/show_schema/<int:id_schema>', view_func=self.show_schema_info)
        self.app.add_url_rule('/get_instance', view_func=self.get_instance_info, methods=['POST'])
        self.app.add_url_rule('/get_envs', view_func=self.get_envs_info)


        self.app.add_url_rule('/test_zapros', view_func=self.test, methods=['POST'])

        #удалить - для демонстрации сравнения реляционной базы с графовой
        self.app.add_url_rule('/insert_relations', view_func=self.insert_relations)
        self.app.add_url_rule('/insert_users', view_func=self.insert_users)


        self.app.register_error_handler(404, self.page_not_found)

    def insert_users(self):
        inserted = self.db_connect.insert_users()
        print(inserted)

        return f'Success added', 201
    def insert_relations(self):

        inserted = self.db_connect.insert_relations()
        print(inserted)

        return f'Success added', 201
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
        '''Возвращает json со всеми моделями'''
        try:

            models_info = self.db_connect.get_models_info()[0]
            return models_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    # def get_model_catalog_info(self):
    #     '''Возвращает json со всеми моделями плюс каталогами'''
    #     try:
    #         path = os.path.join(os.getcwd(),f'/app/db/scripts/catalogs.json');
    #         print("Путь до каталогов", path)
    #         #models_info = open(f'C:/GitHub/PNI_server/app/db/scripts/catalogs.json', 'r', encoding="utf-8")
    #         models_info = open(path, 'r', encoding="utf-8")
    #         res = models_info.read()
    #         return res, 200
    #     except ModelProblems as m_problem:
    #         abort(404, description=m_problem)

    def get_model_catalog_info(self):
        '''Возвращает json со всеми моделями плюс каталогами'''
        try:
            models_info = self.db_connect.get_model_catalog_info()
            return models_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)
    def get_info_model(self, name_model):
        '''Функция для создания аналога в графовой БД. Возвращает инфо об одной модели'''
        try:
            path = os.path.join(os.getcwd(), f'/app/db/scripts/{name_model}.json');
            print("Путь до каталогов", path)
            #models_info = open(f'C:/GitHub/PNI_server/app/db/scripts/{name_model}.json', 'r', encoding="utf-8")
            models_info = open(f'path', 'r', encoding="utf-8")
            res = models_info.read()
            return res, 200
        except ModelProblems as m_problem:
            abort(400, description=m_problem)

    def get_envs_info(self):
        try:
            envs_info = self.db_connect.get_envs_info()
            return envs_info, 200
        except ParametrNotFoundException:
            abort(404, description=' envs not found')

    def get_instance_info(self):
        model = dict(request.json)
        model_id = model['model']
        try:
            instance_info = self.db_connect.get_info_instance(model_id)
            return instance_info, 200
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
            calculations=model_info['Expressions']
        )
        if model_id == -1:
            return f'Модель не может быть добавлена', 400
        else:
            return f'Success added {model_id}', 201

    def add_schema_info(self):
        schema_info = dict(request.json)
        schema_id = self.db_connect.create_schema(
            title=schema_info['Title'],
            instances=schema_info['BlockInstances'],
            interconnections=schema_info['BlockInterconnections']
        )
        if schema_id == -1:
            return f'Схема не может быть добавлена', 400
        else:
            return f'Success added {schema_id}', 201
    def show_all_schemas_info(self):
        try:
            all_schemas = self.db_connect.show_all_schemas( )
            return all_schemas, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    def show_schema_info(self, id_schema):
        try:
            schema = self.db_connect.show_schema(
                schema_id=id_schema
            )
            return schema, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, dest='config')

    args = parser.parse_args()

    config = config_parser(args.config)

    server_host = config['SERVER_HOST']
    server_port = config['SERVER_PORT']

    db_host = os.environ.get('DB_HOST',config['DB_HOST'])
    print("DB_host",db_host)
    db_port = os.environ.get('DB_PORT',config['DB_PORT'])
    print("DB_port",db_port)
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
