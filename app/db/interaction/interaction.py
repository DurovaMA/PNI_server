from app.db.client.client import PostgreSQLConnection
from app.db.exceptions import ParametrNotFoundException, UserNotFoundException, ModelProblems
from app.db.models.models import Base, User, Parametr, Environment
import psycopg2
import json


class DbInteraction:

    def __init__(self, host, port, user, password, db_name):
        self.postgresql_connection = PostgreSQLConnection(
            host=host,
            user=user,
            port=port,
            password=password,
            db_name=db_name
        )
        # self.postgresql_connection.autocommit = True

        self.engine = self.postgresql_connection.connection.engine

    # def create_table_users(self):
    #    Base.metadata.tables['users'].create(self.engine)

    # def add_user_info(self, username, email, password):
    #    user = User(
    #        username=username,
    #        password=password,
    #        email=email
    #    )
    #    try:
    #        self.postgresql_connection.session.add(user)
    #    except:
    #        self.postgresql_connection.session.rollback()
    #        raise
    #    else:
    #        self.postgresql_connection.session.commit()
    #    return self.get_user_info(username)

    def add_param_info(self, parametr_id, title, symbol, unit, type):
        param = Parametr(
            id=parametr_id,
            title=title,
            symbol=symbol,
            units=unit,
            param_type=type
        )
        try:
            self.postgresql_connection.session.add(param)
        except:
            self.postgresql_connection.session.rollback()
            raise
        else:
            self.postgresql_connection.session.commit()
        return self.get_parametr_info(parametr_id)

    # def get_user_info(self, username):
    #     user = self.postgresql_connection.session.query(User).filter_by(username=username).first()
    #     if user:
    #         self.postgresql_connection.session.expire_all()
    #         return {'username': user.username, 'email': user.email, 'password': user.password}
    #     else:
    #         raise UserNotFoundException('User not found!')

    def get_parametr_info(self, parametr_id):
        par = self.postgresql_connection.session.query(Parametr).filter_by(id=parametr_id).first()
        if par:
            self.postgresql_connection.session.expire_all()
            return {'title': par.title, 'symbol': par.symbol, 'units': par.units, 'param_type': par.param_type}
        else:
            raise ParametrNotFoundException('Parameter not found!')

    def edit_parametr_info(self, parametr_id, new_parametrid=None, new_title=None, new_symbol=None, new_unit=None,
                           new_type=None):
        par = self.postgresql_connection.session.query(Parametr).filter_by(id=parametr_id).first()
        if par:
            if new_parametrid is not None:
                par.id = new_parametrid
            if new_title is not None:
                par.title = new_title
            if new_symbol is not None:
                par.symbol = new_symbol
            if new_unit is not None:
                par.units = new_unit
            if new_type is not None:
                par.param_type = new_type

            self.postgresql_connection.session.commit()
            return self.get_parametr_info(parametr_id if new_parametrid is None else new_parametrid)
        else:
            raise ParametrNotFoundException('Parameter not found!')


#######     Возврат всех доступных сред

# def get_envs_info(self):
#    envs = self.postgresql_connection.session.query(Environment).all()
#    list = []
#    for e in envs:
#        list.append({'id': e.id, 'type_of_environment': e.type_of_environment})
#    self.postgresql_connection.session.expire_all()
#    if list:
#        return list
#    else:
#        raise ParametrNotFoundException('Environments not found!')


class DbConnection:
    def __init__(self, host, user, password, database):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.connection.autocommit = True

    def get_envs_info(self):

        request_dict = {}
        param_list = []
        env_list = []

        qry = f"""select * from parametr where param_type='base';"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            parametrs = cursor.fetchall()

        qry = f"""select * from environment;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            envs = cursor.fetchall()


        for parametr in parametrs:
            param_list.append({'ParameterId': parametr[0], 'Title': parametr[1],
                               'Symbol': parametr[2], 'Units': parametr[3]})

        env_list = []
        for e in envs:
            qry = f"""select par_id from return_avail_env({e[0]});"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                params = cursor.fetchall()
            p_of_e = []  # список параметров текущей среды
            for p in params:
                p_of_e.append( p[0])
            env_list.append({'FlowEnviromentId': e[0], 'FlowEnvironmentType': e[1], 'BaseParametres': p_of_e})

        request_dict["BaseParametres"] = param_list
        request_dict["FlowEnvironments"] = env_list

        if request_dict:
            return request_dict
        else:
            raise ParametrNotFoundException('Environments not found!')

    def get_models_info(self):
        qry = f"""select * from model_of_block;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            models = cursor.fetchall()

        description_list = []
        for m in models:
            print(m)
            id =  m[0]
            title = m[1]
            description = m[2]
            input_flows = m[4]
            output_flows = m[5]
            default_params = m[6]
            all_params = m[7]
            expressions = m[8]

            input_flows_list = []
            output_flows_list = []
            all_params_list = []
            expressions_text = []
            default_params_list = []

            try:
                for i_f in input_flows:
                    qry = f"""select * from flow where id={i_f};"""
                    with self.connection.cursor() as cursor:
                        try:
                            cursor.execute(qry)
                            flow_info = cursor.fetchall()[0]
                        except Exception:
                            raise ModelProblems("Данные для входного потока %s из модели номер %d не найдены" % (i_f, id))
                        else:
                            try:
                                dict_all = {'id': flow_info[0], 'FlowVariableIndex': flow_info[1], 'FlowEnviroment': flow_info[3]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (flow_info, id))
                            else:
                                input_flows_list.append(dict_all)
            except TypeError:
                raise ModelProblems("Словарь %s из модели номер %d пуст" % ("input_flows", id))

            try:
                for o_f in output_flows:
                    qry = f"""select * from flow where id={o_f};"""
                    with self.connection.cursor() as cursor:
                        try:
                            cursor.execute(qry)
                            flow_info = cursor.fetchall()[0]
                        except Exception:
                            raise ModelProblems("Данные для выходного потока %s из модели номер %d не найдены" % (o_f, id))
                        else:
                            try:
                                dict_all = {'id': flow_info[0], 'FlowVariableIndex': flow_info[1], 'FlowEnviroment': flow_info[3]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (flow_info, id))
                            else:
                                output_flows_list.append(dict_all)
            except TypeError:
                raise ModelProblems("Словарь %s из модели номер %d пуст" % ("input_flows", id))

            try:
                for p in all_params:
                    qry = f"""select * from show_parameters_info where id={p};"""
                    with self.connection.cursor() as cursor:
                        try:
                            cursor.execute(qry)
                            param_info = cursor.fetchall()[0]
                        except Exception:
                            raise ModelProblems("Данные для параметра %s из модели номер %d не найдены" % (p, id))
                        else:
                            try:
                                dict_all = {'id': param_info[0], 'name': param_info[1], 'value': param_info[2],
                                        'title': param_info[3], 'units': param_info[4]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (param_info, id))
                            else:
                                all_params_list.append(dict_all)
            except TypeError:
                raise ModelProblems("Словарь %s из модели номер %d пуст" % ("all_params", id))

            try:
                for d_p in default_params:
                    qry = f"""select * from show_parameters_info where id={d_p};"""
                    with self.connection.cursor() as cursor:
                        try:
                            cursor.execute(qry)
                            param_info = cursor.fetchall()[0]
                        except Exception:
                            raise ModelProblems("Данные для параметра по умолчанию %s из модели номер %d не найдены" % (d_p, id))
                        else:
                            try:
                                dict_all = {'id': param_info[0], 'name': param_info[1], 'value': param_info[2],
                                        'title': param_info[3], 'units': param_info[4]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (param_info, id))
                            else:
                                default_params_list.append(dict_all)
            except TypeError:
                ModelProblems("Словарь %s из модели номер %d пуст" % ("default_params_list", id))

            try:
                for e in expressions:
                    qry = f"""select * from calculation where id={e};"""
                    with self.connection.cursor() as cursor:
                        try:
                            cursor.execute(qry)
                            e_info = cursor.fetchall()[0]
                        except Exception:
                            raise ModelProblems("Данные для расчетного выражения %s из модели номер %d не найдены" % (e, id))
                        else:
                            try:
                                dict_all = {'id': e_info[0], 'Order': e_info[1], 'Expression': e_info[2],
                                        'DefinedVariableId': e_info[3], 'NeededVariables': e_info[4]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (e_info, id))
                            else:
                                expressions_text.append(dict_all)
            except TypeError:
                ModelProblems("Словарь %s из модели номер %d пуст" % ("expressions_text", id))

            try:
                description_list.append({'id': id, 'title': title, 'description': description,
                                         'input_flows': input_flows, 'output_flows': output_flows,
                                         'default_params': default_params_list, 'all_params': all_params_list,
                                         'expressions': expressions_text})
            except Exception:
                ModelProblems("Совсем плохо")
        if description_list:
            return description_list
        else:
            raise ParametrNotFoundException('Environments not found!')

    def create_model(self, model_description, model_title, in_flows, out_flows, default_params, extra_params, calculations,
                     model_id=None):
        print(model_description)
        print(model_title)
        print(in_flows)
        print(out_flows)
        print(default_params)
        print(extra_params)
        print(calculations)
        # создание записи о новой модели
        qry = f"""select create_model('{model_title}', '{model_description}');"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            id_model = cursor.fetchall()[0][0]

        # создание группы ДОПОЛНИТЕЛЬНЫХ параметров
        qry = f"""select create_group('extra_params', {id_model});"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            id_group_extr = cursor.fetchall()[0][0]

        id_extra_params_list = []
        # запись ДОПОЛНИТЕЛЬНЫХ параметров в созданную группу
        for cur_param in extra_params:
            print(extra_params)
            qry = f"""select add_extra_def_param(
                {id_model}, {id_group_extr}, 'extra', '{cur_param['Title']}', '{cur_param['Symbol']}', '{cur_param['Units']}');"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                id_extra_params_list.append(cursor.fetchall()[0][0])

        # создание группы параметров ПО УМОЛЧАНИЮ
        qry = f"""select create_group('default_params', {id_model});"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            id_group_def = cursor.fetchall()[0][0]

        id_default_params_list = []
        # запись параметров ПО УМОЛЧАНИЮ в созданную группу
        for cur_param in default_params:
            print(default_params)
            qry = f"""select add_extra_def_param(
                {id_model}, {id_group_def}, 'default', '{cur_param['Title']}', '{cur_param['Symbol']}', '{cur_param['Units']}');"""
            print(qry)
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                id_default_params_list.append(cursor.fetchall()[0][0])

        flows_model = []
        id_flows_model_input = []
        # внесение в список потоков входных
        for cur_flow in in_flows:
            qry = f"""select add_input_flow(
                {id_model}, '{cur_flow['FlowVariableIndex']}', {cur_flow['FlowEnviroment']});"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                id_flow = cursor.fetchall()[0][0]
                id_flows_model_input.append(id_flow)
        flows_model = flows_model + id_flows_model_input

        id_flows_model_output = []
        # внесение в список потоков выходных
        for cur_flow in out_flows:
            qry = f"""select add_output_flow({id_model}, '{cur_flow['FlowVariableIndex']}', {cur_flow['FlowEnviroment']});"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                id_flow = cursor.fetchall()[0][0]
                id_flows_model_output.append(id_flow)
        flows_model = flows_model + id_flows_model_output

        id_flow_params_list = []
        # запись в модель переменных от всех потоков
        for flow in flows_model:
            qry = f"""select add_params_from_flow({id_model}, {flow});"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                id_flow_params = cursor.fetchall()[0][0]
                id_flow_params_list = id_flow_params_list + id_flow_params

        id_calcs_list = []
        for calculation in calculations:
            order_calc = calculation['Order']
            express_calc = calculation['Expression']
            defined_param = calculation['DefinedVariable']
            required_params_list = calculation['NeededVariables']
            qry = f"""select add_calculation ({id_model}, {order_calc}, '{express_calc}');"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                id_calc = cursor.fetchall()[0][0]
                id_calcs_list.append(id_calc)
            qry2 = f"""select defined_param_fk, required_params_fk from calculation c where id={id_calc};"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry2)
                params = cursor.fetchall()[0]
                required_params_group = params[1]
                defined_params_group = params[0]


            qry3 = f"""select insert_calc_param({id_model}, '{defined_param}', {id_calc}, {defined_params_group});"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry3)
                cursor.fetchall()[0][0]
            for req in required_params_list:
                qry4 = f"""select insert_calc_param({id_model}, '{req}', {id_calc}, {required_params_group});"""
                with self.connection.cursor() as cursor:
                    cursor.execute(qry4)
                    cursor.fetchall()[0][0]


        all_params_list = id_extra_params_list + id_default_params_list + id_flow_params_list
        qry = f"""update model_of_block set input_flows=array{id_flows_model_input},
        output_flows=array{id_flows_model_output}, default_params =array{id_default_params_list},
        all_params =array{all_params_list},  expressions =array{id_calcs_list}
        where id = {id_model};"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)

        if all_params_list:
            print('Добавлена модель номер ', id_model)
            return id_model
        else:
            raise ParametrNotFoundException('Environments not found!')


if __name__ == '__main__':
    db = DbInteraction(
        host='localhost',
        port=5432,
        user="postgres",
        password="root",
        db_name="PNI3_v7"
    )
    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="PNI3_v7"
    )

    print(db2.get_models_info())
    #print(db2.create_model())
    # db.create_table_users()
    # db.add_param_info(2222, 'test', 'test', 'test', 'base')
    # db.add_user_info('test', 'test', 'base')
    # db.get_parametr_info(2222)
