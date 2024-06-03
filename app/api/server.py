import json
import threading
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

        # создание модели
        self.app.add_url_rule('/create_model/<int:user_id>', view_func=self.add_model_info, methods=['POST'])

        # создание версии модели
        self.app.add_url_rule('/create_version_model/<int:user_id>', view_func=self.add_version_model, methods=['POST'])

        # создание схемы
        self.app.add_url_rule('/create_schema/<int:user_id>', view_func=self.add_schema_info, methods=['POST'])

        # блокировка схемы
        self.app.add_url_rule('/block_schema/<int:user_id>/<int:schema_id>', view_func=self.block_schema)

        self.app.add_url_rule('/unblock_schema/<int:user_id>/<int:schema_id>', view_func=self.unblock_schema)
        # ПЕРЕПИСАТЬ инфо об экземпляре
        # self.app.add_url_rule('/get_instance', view_func=self.get_instance_info, methods=['POST'])

        # отображение всех моделей
        # self.app.add_url_rule('/get_models', view_func=self.get_models_info)

        # каталог (с версиями)
        self.app.add_url_rule('/get_version_catalog', view_func=self.get_catalog_version_info)

        # отображение информации по созданию модели по номеру
        self.app.add_url_rule('/get_creating_info/<int:model_id>', view_func=self.get_creating_info)

        # отображение версии модели по номеру
        self.app.add_url_rule('/get_version/<int:version_id>', view_func=self.get_version_info)

        # инфо о массиве версий
        self.app.add_url_rule('/get_versions', view_func=self.get_versions_info, methods=['POST'])

        # отобразить все схемы
        self.app.add_url_rule('/show_all_schemas', view_func=self.show_all_schemas_info)

        # инфо о схеме по номеру
        self.app.add_url_rule('/show_schema/<int:id_schema>', view_func=self.show_schema_info)

        # генерация информации об экземпляре модели
        self.app.add_url_rule('/generate_instance/<int:id_model>/<int:vers_num>', view_func=self.generate_instance_info)

        # отображение сред
        self.app.add_url_rule('/get_envs', view_func=self.get_envs_info)

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

    #
    # def get_models_info(self):
    #     '''Возвращает json со всеми моделями'''
    #     try:
    #         models_info = self.db_connect.get_models_info()[0]
    #         return models_info, 200
    #     except ModelProblems as m_problem:
    #         abort(404, description=m_problem)

    def get_version_info(self, version_id):
        """Возвращает json с информацией о версии модели по ее номеру"""
        try:
            version_info = self.db_connect.get_version(version_id)
            return version_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    def get_creating_info(self, model_id):
        """Возвращает json информацией о создании модели"""
        try:
            creating_info = self.db_connect.get_creating_info(model_id)
            res = json.dumps(creating_info, ensure_ascii=False)
            return res, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    def get_catalog_version_info(self):
        '''Возвращает json со всеми моделями плюс каталогами плюс версии'''
        try:
            models_info = self.db_connect.get_catalog_version_info()
            return models_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    def get_envs_info(self):
        try:
            envs_info = self.db_connect.get_envs_info()
            return envs_info, 200
        except ParametrNotFoundException:
            abort(404, description=' envs not found')

    def get_versions_info(self):
        array_ids = dict(request.json)
        version_list = array_ids['Versions']
        try:
            versions_info = self.db_connect.get_versions_info(version_list)
            return versions_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    #
    def generate_instance_info(self, id_model, vers_num):
        try:
            instance_info = self.db_connect.generate_info_instance(id_model, vers_num)
            return instance_info, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    #
    def add_model_info(self, user_id):

        model_info = dict(request.json)
        js = json.dumps(model_info, ensure_ascii=False)
        model_id = self.db_connect.create_model(
            user_id=user_id,
            model_description=model_info['Description'],
            model_title=model_info['Title'],
            in_flows=model_info['InputFlows'],
            out_flows=model_info['OutputFlows'],
            default_params=model_info['DefaultParameters'],
            extra_params=model_info['ExtraParameters'],
            calculations=model_info['Expressions'],
            full_json=js,
            directory=model_info['DirectoryId']
        )
        if model_id == -1:
            return f'Модель не может быть добавлена', 400
        else:
            return f'Success added {model_id}', 201

    #
    def add_version_model(self, user_id):
        model_info = dict(request.json)
        model_id = model_info['ModelId']
        model_pk, version_id = self.db_connect.create_version(
            model_id=model_id,
            user_id=user_id,
            note=model_info['Note'],
            in_flows=model_info['InputFlows'],
            out_flows=model_info['OutputFlows'],
            default_params=model_info['DefaultParameters'],
            extra_params=model_info['ExtraParameters'],
            calculations=model_info['Expressions']
        )
        if model_id == -1:
            return f'Версия модели не может быть добавлена', 400
        else:
            return f'Success added version {version_id} for model {model_id} (record {model_pk})', 201

    #
    def add_schema_info(self, user_id):
        schema_info = dict(request.json)
        schema_id = self.db_connect.create_schema(
            user_id=user_id,
            title=schema_info['SchemaName'],
            instances=schema_info['BlockInstances'],
            interconnections=schema_info['BlockInterconnections']
        )
        if schema_id == -1:
            return f'Схема не может быть добавлена', 400
        else:
            return f'Success added {schema_id}', 201

    def block_schema(self, user_id, schema_id):
        schema_id = self.db_connect.block_schema(
            user_id=user_id,
            schema_id=schema_id
        )
        if schema_id == -1:
            return f'Схема не существует или была заблокирована другим пользователем', 400
        else:
            return f'Успешно заблокирована схема {schema_id}', 201
    def unblock_schema(self, user_id, schema_id):
        schema_id = self.db_connect.unblock_schema(
            user_id=user_id,
            schema_id=schema_id
        )
        if schema_id == -1:
            return f'Схема не существует или была заблокирована другим пользователем', 400
        else:
            return f'Успешно разблокирована схема {schema_id}', 201
    def show_all_schemas_info(self):
        try:
            all_schemas = self.db_connect.show_all_schemas()
            return all_schemas, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)

    #
    def show_schema_info(self, id_schema):
        try:
            schema = self.db_connect.show_schema(
                schema_id=id_schema
            )
            return schema, 200
        except ModelProblems as m_problem:
            abort(404, description=m_problem)
    #


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, dest='config')

    args = parser.parse_args()

    config = config_parser(args.config)

    server_host = config['SERVER_HOST']
    server_port = config['SERVER_PORT']

    db_host = os.environ.get('DB_HOST', config['DB_HOST'])
    print("DB_host", db_host)
    db_port = os.environ.get('DB_PORT', config['DB_PORT'])
    print("DB_port", db_port)
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
