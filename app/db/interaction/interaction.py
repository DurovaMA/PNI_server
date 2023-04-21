from app.db.client.client import PostgreSQLConnection
from app.db.interaction import func_sql
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
        problem_list = []

        if len(models) == 0:
            problem_list.append("Моделей в базе нет")
        for m in models:
            problem_text = ""
            print(m)
            id = m[0]
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


            if input_flows == None:
                problem_text += ("\n Словарь %s из модели номер %d пуст" % ("input_flows", id))
            else:
                for i_f in input_flows:
                    qry = f"""select * from flow where id={i_f};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        flow_info = cursor.fetchall()[0]
                        if flow_info == None:
                            problem_text += ("\nДанные для входного потока %s из модели номер %d не найдены" % (i_f, id))
                        else:
                            try:
                                dict_all = {'id': flow_info[0], 'FlowVariableIndex': flow_info[1], 'FlowEnviroment': flow_info[3]}
                            except Exception:
                                problem_text += ("\n Ошибка индекса для %s из модели номер %d " % (flow_info, id))
                            else:
                                input_flows_list.append(dict_all)

            if output_flows == None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("output_flows", id))
            else:
                for o_f in output_flows:
                    qry = f"""select * from flow where id={o_f};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        flow_info = cursor.fetchall()[0]
                        if flow_info == None:
                            problem_text += ("\nДанные для выходного потока %s из модели номер %d не найдены" % (o_f, id))
                        else:
                            try:
                                dict_all = {'id': flow_info[0], 'FlowVariableIndex': flow_info[1], 'FlowEnviroment': flow_info[3]}
                            except Exception:
                                problem_text += ("\nОшибка индекса для %s из модели номер %d " % (flow_info, id))
                            else:
                                output_flows_list.append(dict_all)

            if all_params == None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("all_params", id))
            else:
                for p in all_params:
                    qry = f"""select * from show_parameters_info where id={p};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        param_info = cursor.fetchall()[0]
                        if param_info == None:
                            problem_text += ("Данные для параметра %s из модели номер %d не найдены" % (p, id))
                        else:
                            try:
                                dict_all = {'id': param_info[0], 'name': param_info[1], 'value': param_info[2],
                                        'title': param_info[3], 'units': param_info[4]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (param_info, id))
                            else:
                                all_params_list.append(dict_all)

            if default_params == None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("default_params_list", id))
            else:
                for d_p in default_params:
                    qry = f"""select * from show_parameters_info where id={d_p};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        param_info = cursor.fetchall()[0]
                        if param_info == None:
                            problem_text += ("Данные для параметра %s из модели номер %d не найдены" % (d_p, id))
                        else:
                            try:
                                dict_all = {'id': param_info[0], 'name': param_info[1], 'value': param_info[2],
                                        'title': param_info[3], 'units': param_info[4]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (param_info, id))
                            else:
                                default_params_list.append(dict_all)

            if expressions == None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("expressions", id))
            else:
                for e in expressions:
                    qry = f"""select * from calculation where id={e};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        e_info = cursor.fetchall()[0]
                        if e_info == None:
                            problem_text += ("\nДанные для расчетного выражения %s из модели номер %d не найдены" % (e, id))
                        else:
                            try:
                                dict_all = {'id': e_info[0], 'Order': e_info[1], 'Expression': e_info[2],
                                        'DefinedVariableId': e_info[3], 'NeededVariables': e_info[4]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (e_info, id))
                            else:
                                expressions_text.append(dict_all)
            if ((input_flows ==None) or (output_flows ==None) or (default_params_list ==None)
                or (all_params_list ==None) or (expressions_text ==None)):
                problem_text += ("\nМодель номер %d не будет отображена\n" % id)
            else:
                model_desc = {'Id': id, 'Title': title, 'Description': description,
                                         'InputFlows': input_flows_list, 'OutputFlows': output_flows_list,
                                         'DefaultParameters': default_params_list, 'AllParameters': all_params_list,
                                         'Expressions': expressions_text}
                description_list.append(model_desc)


            problem_list.append(problem_text)

        print('\n'.join(map(str, problem_list)))
        return description_list



    def create_model(self, model_description, model_title, in_flows, out_flows, default_params, extra_params, calculations,
                     model_id=None):
        print(model_description)
        print(model_title)
        print(in_flows)
        print(out_flows)
        print(default_params)
        print(extra_params)
        print(calculations)



        id_model = func_sql.create_new_model(model_title, model_description, self.connection)

        id_group_extr, id_extra_params_list = func_sql.add_extra_def_params('extra_params', 'extra', id_model, extra_params, self.connection)
        id_group_def, id_default_params_list = func_sql.add_extra_def_params('default_params', 'default', id_model, default_params, self.connection)

        id_flows_model_input = func_sql.add_flow(id_model, 'input', in_flows, self.connection)
        id_flows_model_output = func_sql.add_flow(id_model, 'output', out_flows, self.connection)

        flows_model = id_flows_model_input + id_flows_model_output


        id_flow_params_list = []
        # запись в модель переменных от всех потоков


        for flow in flows_model:
            id_flow_params = func_sql.add_params_from_flow(id_model, flow, self.connection)
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
