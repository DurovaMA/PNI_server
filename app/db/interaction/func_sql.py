def create_new_model(tit, description, con):
    """Создает записи о новой модели. Принимает название, описание и
    соединение с БД возвращает идентификатор добавленной модели"""
    qry = f"""select create_model('{tit}', '{description}');"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        res_id = cursor.fetchall()[0][0]
    return res_id


def add_extra_def_params(group_type, param_type, model, param_list, con):
    """Создает группу параметров и записывает их в эту группу.
    Принимает тип группы, тип параметров, номер модели, список параметров и соединение с БД.
    Возвращает список из: идентификатор добавленной группы и массив идентификаторов параметров"""
    id_and_list = []
    qry = f"""select create_group('{group_type}', {model});"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        id_group = cursor.fetchall()[0][0]
    id_and_list.append(id_group)

    id_params_list = []
    for cur_param in param_list:
        qry = f"""select add_extra_def_param(
            {model}, {id_group}, '{param_type}', '{cur_param['Title']}', '{cur_param['Symbol']}', '{cur_param['Units']}');"""
        with con.cursor() as cursor:
            cursor.execute(qry)
            id_params_list.append(cursor.fetchall()[0][0])
    id_and_list.append(id_params_list)
    return id_group, id_params_list


def add_flow(model, flow_type, flows, con):
    """Записывает потоки. Принимает номер модели, массив потоков и соединение с БД. Возвращает массив идентификаторов потоков"""
    id_flows_model = []
    for cur_flow in flows:
        if flow_type == 'input':
            qry = f"""select add_input_flow(
        {model}, '{cur_flow['FlowVariableIndex']}', {cur_flow['FlowEnviroment']});"""
        elif flow_type == 'output':
            qry = f"""select add_output_flow({model}, '{cur_flow['FlowVariableIndex']}', {cur_flow['FlowEnviroment']});"""
        with con.cursor() as cursor:
            try:
                cursor.execute(qry)
            except Exception:
                print("не удалось выполнить запрос")
            id_flow = cursor.fetchall()[0][0]
            id_flows_model.append(id_flow)
    return id_flows_model


def add_params_from_flow(mod_id, flow_id, con):
    """Добавляет в модель те параметры, которые доступны из-за потока. Принимает номер модели, номер потока и соединение
     с БД. Возвращает массив идентификаторов вставленных параметров """
    problem_text = ""
    qry1 = f"""select  model, param_name, pg_id from param_of_flow where model={mod_id} and flow={flow_id};"""
    with con.cursor() as cursor:
        cursor.execute(qry1)
        param_to_insert = cursor.fetchall()
        if param_to_insert == None:
            problem_text += ("\nВ потоке %s для модели %d не найдены параметры" % (flow_id, mod_id))
        else:
            pg_list = []
            pom_inserted_list = []
            for param in param_to_insert:
                model = param[0]
                param_name = param[1]
                pg_id = param[2]
                p_dict = {"model": model, "param_name": param_name, "pg_id": pg_id}
                qry2 = f"""insert into param_of_model ( model_fk, param_name) values ({model},'{param_name}') RETURNING  *;"""
                with con.cursor() as cursor:
                    cursor.execute(qry2)
                    pom_inserted = cursor.fetchall()
                if pom_inserted == None:
                    problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
                else:
                    pom_id = pom_inserted[0][0]
                    p_dict['pom_id'] = pom_id
                pg_list.append(p_dict)

            for ins in pg_list:
                param_group_fk = ins["pg_id"]
                param_of_model_fk = ins["pom_id"]
                qry3 = f"""insert into all_inclusions ( param_group_fk, param_of_model_fk)  values ({param_group_fk},'{param_of_model_fk}') RETURNING  *;"""
                with con.cursor() as cursor:
                    cursor.execute(qry3)
                    ai_inserted = cursor.fetchall()[0][2]
                if ai_inserted == None:
                    problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
                else:
                    pom_inserted_list.append(ai_inserted)
    if pom_inserted_list:
        return pom_inserted_list
    else:
        print('problem')


def add_calc(mod_id, calc_list, con):
    """Заполняет таблицу расчетных выражений. Принимает номер модели, массив записей о выражениях и соединение
         с БД. Возвращает массив идентификаторов вставленных выражений """
    id_list = []
    for calculation in calc_list:
        order_calc = calculation['Order']
        express_calc = calculation['Expression']
        defined_param = calculation['DefinedVariable']
        required_params_list = calculation['NeededVariables']
        qry = f"""select add_calculation ({mod_id}, {order_calc}, '{express_calc}');"""
        with con.cursor() as cursor:
            cursor.execute(qry)
            id_calc = cursor.fetchall()[0][0]
        id_list.append(id_calc)
        qry2 = f"""select defined_param_fk, required_params_fk from calculation c where id={id_calc};"""
        with con.cursor() as cursor:
            cursor.execute(qry2)
            params = cursor.fetchall()[0]
        required_params_group = params[1]
        defined_params_group = params[0]

        qry3 = f"""select insert_calc_param({mod_id}, '{defined_param}', {id_calc}, {defined_params_group});"""
        with con.cursor() as cursor:
            cursor.execute(qry3)
        for req in required_params_list:
            qry4 = f"""select insert_calc_param({mod_id}, '{req}', {id_calc}, {required_params_group});"""
            with con.cursor() as cursor:
                cursor.execute(qry4)
    return id_list


def show_flows(mod_id, type, flows, con):
    """Отображает список потоков для JSON. Принимает номер модели, тип потока ("input" или "output") массив записей о
    выражениях и соединение с БД. Возвращает массив идентификаторов вставленных выражений """
    problem_flow_text = ""
    id_flows_list = []
    flag = False # поднимается если ошибка критическая для модели
    if (flows is None) or (len(flows) == 0):
        problem_flow_text += ("\nСловарь потоков типа %s из модели номер %d пуст" % (type, mod_id))
    else:
        for f_id in flows:
            qry = f"""select * from flow where id={f_id};"""
            with con.cursor() as cursor:
                cursor.execute(qry)
                flow_inf = cursor.fetchall()
            if len(flow_inf) == 0:
                problem_flow_text += (
                        "\nДанные для потока %s из модели номер %d не найдены" % (f_id, mod_id))
                flag = True
            else:
                flow_info = flow_inf[0]
                flow_id = flow_info[0]
                flow_variable_index = flow_info[1]
                qry = f"""select * from param_of_flow_in_model where model={mod_id} and FlowId ={f_id};"""
                with con.cursor() as cursor:
                    cursor.execute(qry)
                    executed_all = cursor.fetchall()
                if type == "output":
                    count_req = executed_all[0][9]
                vars_desc = []
                for executed in executed_all:
                    flow_variable_id = executed[1]
                    flow_id = executed[2]
                    flow_variable_name = executed[3]
                    variable_prototype = {'ParametrId': executed[4], 'Title': executed[5],
                                          'Symbol': executed[6], 'Units': executed[7]}
                    vars_desc.append({'FlowVariableId': flow_variable_id, 'FlowId': flow_id,
                                      'FlowVariableName': flow_variable_name,
                                      'VariablePrototype': variable_prototype})
                if type == "input":
                    dict_all = {'AvailableVariables': vars_desc, 'FlowVariablesIndex': flow_variable_index,
                                'Flow_id': flow_id}
                elif type == "output":
                    dict_all = {'RequiredVariables': vars_desc, 'FlowVariablesIndex': flow_variable_index,
                                'FlowId': flow_id, 'CountOfMustBeDefinedVars': count_req}
                id_flows_list.append(dict_all)
    return id_flows_list, problem_flow_text, flag

def show_extra_default_params(mod_id, type, params, con):
    params_list = []
    problem_param_text = ""
    flag = False # поднимается если ошибка критическая для модели
    if (params is None) or (len(params) == 0):
        problem_param_text += ("\nСловарь параметров типа %s из модели номер %d пуст" % (type, mod_id))
    else:
        for p in params:
            qry = f"""select * from show_parameters_info where id={p};"""
            with con.cursor() as cursor:
                cursor.execute(qry)
                result_sql = cursor.fetchall()
                if (result_sql is None) or (len(result_sql) == 0):
                    problem_param_text += ("Данные для параметра %s из модели номер %d не найдены" % (p, mod_id))
                    flag = True
                else:
                    param_info = result_sql[0]
                    dict_all = {'ParametrId': param_info[0], 'VariableName': param_info[1],
                                'Title': param_info[3], 'Units': param_info[4]}
                    params_list.append(dict_all)
    return params_list, problem_param_text, flag

def show_expressions(mode_id, expressions, con):
    expressions_list = []
    problem_expres_text = ""
    flag = False  # поднимается если ошибка критическая для модели
    if expressions is None or (len(expressions) == 0):
        problem_expres_text += ("\nСловарь %s из модели номер %d пуст" % ("expressions", mode_id))
        flag = True
    else:
        for e in expressions:
            qry = f"""select * from calculation where id={e};"""
            with con.cursor() as cursor:
                cursor.execute(qry)
                result_sql = cursor.fetchall()
                if (result_sql is None) or (len(result_sql) == 0):
                    problem_expres_text += ("\nДанные для расчетного выражения %s из модели номер %d не найдены" % (
                        e, mode_id))
                    flag = True
                else:
                    e_info = result_sql[0]
                    dict_all = {'ExpressionId': e_info[0], 'Order': e_info[1], 'Expression': e_info[2],
                                    'DefinedVariableId': e_info[3], 'NeededVariables': e_info[4]}
                    expressions_list.append(dict_all)
    return expressions_list, problem_expres_text, flag

from app.db.client.client import PostgreSQLConnection
from app.db.interaction import func_sql
from app.db.exceptions import ParametrNotFoundException, UserNotFoundException, ModelProblems
from app.db.models.models import Base, User, Parametr, Environment
import psycopg2
import json


class DbConnection:
    def __init__(self, host, user, password, database):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.connection.autocommit = True

    def add_params_from_flow(self, mod_id, flow_id, con):
        problem_text = ""
        qry1 = f"""select  model, param_name, pg_id from param_of_flow where model={mod_id} and flow={flow_id};"""
        with con.cursor() as cursor:
            cursor.execute(qry1)
            param_to_insert = cursor.fetchall()
            if param_to_insert == None:
                problem_text += ("\nВ потоке %s для модели %d не найдены параметры" % (flow_id, mod_id))
            else:
                pg_list = []
                pom_inserted_list = []
                for param in param_to_insert:
                    model = param[0]
                    param_name = param[1]
                    pg_id = param[2]
                    p_dict = {"model": model, "param_name": param_name, "pg_id": pg_id}
                    qry2 = f"""insert into param_of_model ( model_fk, param_name) values ({model},'{param_name}') RETURNING  *;"""
                    with con.cursor() as cursor:
                        cursor.execute(qry2)
                        pom_inserted = cursor.fetchall()
                    if pom_inserted == None:
                        problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
                    else:
                        pom_id = pom_inserted[0][0]
                        p_dict['pom_id'] = pom_id
                    pg_list.append(p_dict)

                for ins in pg_list:
                    param_group_fk = ins["pg_id"]
                    param_of_model_fk = ins["pom_id"]
                    qry3 = f"""insert into all_inclusions ( param_group_fk, param_of_model_fk)  values ({param_group_fk},'{param_of_model_fk}') RETURNING  *;"""
                    with con.cursor() as cursor:
                        cursor.execute(qry3)
                        ai_inserted = cursor.fetchall()[0][2]
                    if ai_inserted == None:
                        problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
                    else:
                        pom_inserted_list.append(ai_inserted)
                # print(pg_list,pom_inserted_list)

        if pom_inserted_list:
            return pom_inserted_list
        else:
            print('problem')


if __name__ == '__main__':
    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="PNI3_v7"
    )
    v = db2.add_params_from_flow(56, 144)
