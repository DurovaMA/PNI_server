




def show_flows(mod_id, type, flows, con):
    """Отображает список потоков для JSON. Принимает номер модели, тип потока ("input" или "output") массив записей о
    выражениях и соединение с БД. Возвращает массив идентификаторов вставленных выражений """
    problem_flow_text = ""
    id_flows_list = []
    flag = False  # поднимается если ошибка критическая для модели
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
                    env_id = executed[10]
                    variable_prototype = {'ParameterId': executed[4], 'Title': executed[5],
                                          'Symbol': executed[6], 'Units': executed[7]}
                    vars_desc.append({'FlowVariableId': flow_variable_id, 'FlowId': flow_id,
                                      'FlowVariableName': flow_variable_name,
                                      'VariablePrototype': variable_prototype})
                if type == "input":
                    dict_all = {'AvailableVariables': vars_desc, 'FlowVariablesIndex': flow_variable_index,
                                'FlowId': flow_id, 'EnvironmentId': env_id}
                elif type == "output":
                    dict_all = {'RequiredVariables': vars_desc, 'FlowVariablesIndex': flow_variable_index,
                                'FlowId': flow_id, 'EnvironmentId': env_id, 'CountOfMustBeDefinedVars': count_req}
                id_flows_list.append(dict_all)
    return id_flows_list, problem_flow_text, flag


def show_extra_default_params(mod_id, type, params, con):
    params_list = []
    problem_param_text = ""
    flag = False  # поднимается если ошибка критическая для модели
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
                    param_id = ''
                    varname = ''
                    title = ''
                    units = ''
                    try:
                        param_id = param_info[0]
                        varname = param_info[1]
                        title = param_info[2]
                        units = param_info[3]
                    except Exception:
                        print("В параметре нет заголовка и единиц")
                    dict_all = {'ParameterId': param_id, 'VariableName': varname,
                                'Title': title, 'Units': units}
                    params_list.append(dict_all)
    return params_list, problem_param_text, flag


def show_expressions(model_id, expressions, con):
    qry_all_calcs = ["select * from calculation where model_fk=%s;", [model_id]]
    with con.cursor() as cursor:
        cursor.execute(qry_all_calcs[0], qry_all_calcs[1])
        result_all_calcs = cursor.fetchall()

    # qry_defined_vars = ["select * from show_calc_defined where model=%s;", [model_id]]
    # with con.cursor() as cursor:
    #     cursor.execute(qry_defined_vars[0], qry_defined_vars[1])
    #     result_defined_vars = cursor.fetchall()
    #
    # qry_required_vars = ["select * from show_calc_required where model=%s;", [model_id]]
    # with con.cursor() as cursor:
    #     cursor.execute(qry_required_vars[0], qry_required_vars[1])
    #     result_required_vars = cursor.fetchall()

    calc_list = []
    for calc in result_all_calcs:
        try:
            id_calc = calc[0]
            order = calc[1]
            exp_text = calc[2]
            type_calc = calc[6]
        except Exception:
            print(f"""Ошибка в считывании result_all_calcs %s модели %s""" % (id_calc, model_id))
            return -1

        qry_defined_var = ["select id, param_name from show_calc_defined where c_id=%s;", [id_calc]]
        with con.cursor() as cursor:
            cursor.execute(qry_defined_var[0], qry_defined_var[1])
            result_defined_vars = cursor.fetchall()
        try:
            def_var_id = result_defined_vars[0][0]
            def_var_name = result_defined_vars[0][1]
        except Exception:
            print(f"""Ошибка в считывании result_defined_vars %s модели %s""" % (id_calc, model_id))
            return -1

        dict = {'ExpressionId': id_calc, "ExpressionType": type_calc, 'Order': order, 'Expression': exp_text,
                'NeededVariables': [], 'DefinedVariable': [def_var_id]}

        qry_required_vars = ["select c_id, array_agg(id), array_agg(param_name) "
                             "from show_calc_required where c_id=%s group by c_id;", [id_calc]]
        with con.cursor() as cursor:
            cursor.execute(qry_required_vars[0], qry_required_vars[1])
            result_required_vars = cursor.fetchall()
        try:
            req_var_id_list = result_required_vars[0][1]
            req_var_name_list = result_required_vars[0][2]
            dict = {'ExpressionId': id_calc, "ExpressionType": type_calc, 'Order': order, 'Expression': exp_text,
                    'NeededVariables': req_var_id_list, 'DefinedVariable': [def_var_id]}
        except Exception:
            print(f"""В %s модели отсутствуют необходимые переменные для выражения %s""" % (model_id, id_calc))



        calc_list.append(dict)

    # qry = f"""select * from show_calc_defined where model={model_id};"""
    # with con.cursor() as cursor:
    #     cursor.execute(qry)
    #     result_sql = cursor.fetchall()
    # def_dict = {}
    # calc_var_dict = {}
    # defined_calc_dict = {}
    # for calc in result_defined_vars:
    #     try:
    #         id_model = calc[0]
    #         param_of_model = calc[1]
    #         exp_id = calc[2]
    #         order = calc[3]
    #         exp = calc[4]
    #         defined_var = calc[5]
    #         param_type = calc[6]
    #         par_id = calc[7]
    #         type_calc = calc[8]
    #     except Exception:
    #         print("Ошибка в ключах calculation")
    #         return -1
    #     calc_var_dict[exp_id] = [param_of_model, defined_var]
    #     defined_calc_dict[exp_id] = {'model': id_model,'pom_id': param_of_model,'c_id': exp_id,
    #                          'order_calc': order,'expression_calc':exp,'param_name':defined_var,
    #                         'param_type':param_type,'p_id':par_id,'type_calc':type_calc}
    #     #var_info = {'name': needed_var, 'type': type, 'pom_id': param_of_model, 'p_id': par_id}
    #     def_dict[exp_id] = param_of_model
    #
    #
    # # qry = f"""select * from show_calc_required where model={model_id};"""
    # # with con.cursor() as cursor:
    # #     cursor.execute(qry)
    # #     result_sql = cursor.fetchall()
    # calc_list = []
    # cur_calc = -1
    # required_calc_dict = {}
    # for calc in result_required_vars:
    #     try:
    #         param_of_model = calc[1]
    #         exp_id = calc[2]
    #         order = calc[3]
    #         exp = calc[4]
    #         needed_var = calc[5]
    #         type = calc[6]
    #         par_id = calc[7]
    #         type_calc = calc[8]
    #     except Exception:
    #         print("Ошибка в ключах calculation")
    #         return -1
    #     if cur_calc != exp_id:  # если это новое выражение
    #         cur_calc = exp_id
    #         dict = {'ExpressionId': exp_id,  'NeededVariables': []}
    #         needed_list = []
    #         needed_list.append([param_of_model, needed_var])
    #         dict['NeededVariables'] = needed_list
    #         calc_list.append(dict)
    #     else:
    #         needed_list.append([param_of_model, needed_var])
    #         dict['NeededVariables'] = needed_list
    #
    #     required_calc_dict[exp_id] = {'model': id_model, 'pom_id': param_of_model, 'c_id': exp_id,
    #                                   'order_calc': order, 'expression_calc': exp, 'param_name': defined_var,
    #                                   'param_type': param_type, 'p_id': par_id, 'type_calc': type_calc}
    #

    # if cur_calc != exp_id:  # если это новое выражение
    #     cur_calc = exp_id
    #     dev_info = def_dict[exp_id]
    #     dict = {'ExpressionId': exp_id, "ExpressionType": type_calc, 'Order': order, 'Expression': exp,
    #             'NeededVariables': [], 'DefinedVariable': [dev_info]}
    #     needed_var_dict = {}
    #     needed_list = []
    #     #var_info = {'name': needed_var, 'type': type, 'pom_id': param_of_model, 'p_id': par_id}
    #     needed_list.append(param_of_model)
    #     dict['NeededVariables'] = needed_list
    #     calc_list.append(dict)
    # else:
    #     #var_info = {'name': needed_var, 'type': type, 'pom_id': param_of_model, 'p_id': par_id}
    #     needed_list.append(param_of_model)
    #     dict['NeededVariables'] = needed_list

    #print(calc_list)

    # for ex in calc_list:
    #     print(ex)
    return calc_list
    # return expressions_list, problem_expres_text, flag

def show_childs_in_catalog(catalog_id, con):
    qry_directories = f"""select d.id, d.dir_name,  d2.dir_name, d2.id  from directory d 
    left join directory d2 on d.id =d2.parent_level_fk where d.id = {catalog_id};"""
    with con.cursor() as cursor:
        cursor.execute(qry_directories)
        all_directories = cursor.fetchall()
    catalog_dict = {}
    catalog_list = []
    for dir in all_directories:
        try:
            catalog_id = dir[0]
            dir_name = dir[1]
            child_name = dir[2]
            child_id = dir[3]
        except Exception:
            print("Невозможно прочитать каталоги")
            return -1
        catalog_dict = {'CatalogId': catalog_id}
    return

def info_instance(mod_id, con):
    qry = f"""select * from show_calc_defined where model={mod_id};"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        result_sql = cursor.fetchall()
    def_dict = {}
    calc_var_dict = {}
    for calc in result_sql:
        try:
            param_of_model = calc[1]
            exp_id = calc[2]
            needed_var = calc[5]
            type = calc[6]
            par_id = calc[7]
        except Exception:
            print("Ошибка в ключах calculation")
            return -1
        calc_var_dict[exp_id] = [param_of_model, needed_var]
        var_info = {'name': needed_var, 'type': type, 'pom_id': param_of_model, 'p_id': par_id}
        def_dict[exp_id] = var_info

    qry = f"""select * from show_calc_required where model={mod_id};"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        result_sql = cursor.fetchall()
    calc_list = []
    cur_calc = -1
    for calc in result_sql:
        try:
            param_of_model = calc[1]
            exp_id = calc[2]
            order = calc[3]
            exp = calc[4]
            needed_var = calc[5]
            type = calc[6]
            par_id = calc[7]
        except Exception:
            print("Ошибка в ключах calculation")
            return -1
        if cur_calc != exp_id:  # если это новое выражение
            cur_calc = exp_id
            dev_info = def_dict[exp_id]
            dict = {'ExpressionId': exp_id, 'Order': order, 'Expression': exp,
                    'NeededVariables': [], 'DefinedVariable': [dev_info]}
            needed_var_dict = {}
            needed_list = []
            var_info = {'name': needed_var, 'type': type, 'pom_id': param_of_model, 'p_id': par_id}
            needed_list.append(var_info)
            dict['NeededVariables'] = needed_list
            calc_list.append(dict)
        else:
            var_info = {'name': needed_var, 'type': type, 'pom_id': param_of_model, 'p_id': par_id}
            needed_list.append(var_info)
            dict['NeededVariables'] = needed_list

    for ex in calc_list:
        print(ex)
    return calc_list




from app.db.client.client import PostgreSQLConnection
from app.db.interaction import func_sql
from app.db.exceptions import ParametrNotFoundException, UserNotFoundException, ModelProblems
from app.db.models.models import Base, User, Parametr, Environment
import psycopg2
import json

# class DbConnection:
#     def __init__(self, host, user, password, database):
#         self.connection = psycopg2.connect(
#             host=host,
#             user=user,
#             password=password,
#             database=database
#         )
#         self.connection.autocommit = True
#
#     def add_params_from_flow(self, mod_id, flow_id, con):
#         problem_text = ""
#         qry1 = f"""select  model, param_name, pg_id from param_of_flow where model={mod_id} and flow={flow_id};"""
#         with con.cursor() as cursor:
#             cursor.execute(qry1)
#             param_to_insert = cursor.fetchall()
#             if param_to_insert == None:
#                 problem_text += ("\nВ потоке %s для модели %d не найдены параметры" % (flow_id, mod_id))
#             else:
#                 pg_list = []
#                 pom_inserted_list = []
#                 for param in param_to_insert:
#                     model = param[0]
#                     param_name = param[1]
#                     p_id = param[2]
#                     pg_id = param[3]
#                     p_dict = {"model": model, "param_name": param_name, "p_id": p_id, "pg_id": pg_id}
#                     qry2 = f"""insert into param_of_model ( model_fk, param_fk, param_name, param_type) values ({model}, {p_id}, '{param_name}', 'flow') RETURNING  *;"""
#                     with con.cursor() as cursor:
#                         cursor.execute(qry2)
#                         pom_inserted = cursor.fetchall()
#                     if pom_inserted == None:
#                         problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
#                     else:
#                         pom_id = pom_inserted[0][0]
#                         p_dict['pom_id'] = pom_id
#                     pg_list.append(p_dict)
#
#                 for ins in pg_list:
#                     param_group_fk = ins["pg_id"]
#                     param_of_model_fk = ins["pom_id"]
#                     qry3 = f"""insert into all_inclusions ( param_group_fk, param_of_model_fk)  values ({param_group_fk},'{param_of_model_fk}') RETURNING  *;"""
#                     with con.cursor() as cursor:
#                         cursor.execute(qry3)
#                         ai_inserted = cursor.fetchall()[0][2]
#                     if ai_inserted == None:
#                         problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
#                     else:
#                         pom_inserted_list.append(ai_inserted)
#                 # print(pg_list,pom_inserted_list)
#
#         if pom_inserted_list:
#             return pom_inserted_list
#         else:
#             print('problem')


# if __name__ == '__main__':
#     db2 = DbConnection(
#         host='localhost',
#         user="postgres",
#         password="root",
#         database="PNI3_v7"
#     )
#     v = db2.add_params_from_flow(56, 144)
