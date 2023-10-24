def create_new_model(tit, description, con):
    """Создает записи о новой модели. Принимает название, описание и
    соединение с БД возвращает идентификатор добавленной модели"""
    qry = f"""INSERT    INTO    public.model_of_block    (title, description, status)    
    VALUES('{tit}', '{description}', 'Developing'::types_status)   RETURNING    id   ;"""
    # qry2 = f"""select create_model('{tit}', '{description}');"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        res_id = cursor.fetchall()[0][0]
    return res_id


def delete_model(id, con):
    """Удаляет из БД запись о некорректной модели"""
    qry = f"""delete from model_of_block where id=({id});"""
    with con.cursor() as cursor:
        cursor.execute(qry)
    return "OK"


def cursor_add_extra_def_param(model, gop_id,  p_type, tit, sym, un, type_incl, con):
    par_m_id_list = []
    with con.cursor() as cursor:
        ins_parametr_qry = f"""INSERT INTO public.parametr (title, symbol, units, param_type, model_fk) 
        VALUES('{tit}', '{sym}', '{un}', '{p_type}', {model})	RETURNING * ;"""
        cursor.execute(ins_parametr_qry)
        result = cursor.fetchall()
        par_id = result[0][0]

        ins_param_of_group_qry = f"""INSERT INTO public.param_of_group (param_fk, group_fk) 
        VALUES({par_id}, {gop_id})	RETURNING * ; """
        cursor.execute(ins_param_of_group_qry)
        result = cursor.fetchall()
        pog_id = result[0][0]

        ins_param_of_model_qry = f"""insert into public.param_of_model (model_fk, param_fk, param_name, param_type) 
        VALUES({model}, {par_id}, '{sym}', '{p_type}') ON CONFLICT (model_fk, param_name)  	DO NOTHING ; """
        cursor.execute(ins_param_of_model_qry)

        sel_pom_qry = f"""SELECT * FROM public.param_of_model WHERE model_fk={model} and param_name='{sym}'; """
        cursor.execute(sel_pom_qry)
        result = cursor.fetchall()
        par_m_id = result[0][0]

        par_m_id_list.append(par_m_id)

        ins_all_inclusions_qry = f"""insert into public.all_inclusions (param_group_fk, param_of_model_fk, type_inclusion)
        VALUES({pog_id}, {par_m_id}, '{type_incl}')	RETURNING *; """
        cursor.execute(ins_all_inclusions_qry)
        result = cursor.fetchall()
        par_all_in = result[0][0]

    return par_m_id_list

def add_extra_def_params(group_type, param_type, model, param_list, con):
    """Создает группу параметров и записывает их в эту группу.
    Принимает тип группы, тип параметров, номер модели, список параметров и соединение с БД.
    Возвращает список из: идентификатор добавленной группы и массив идентификаторов параметров"""
    if param_list ==[]:
        return 0, []
    id_and_list = []
    qry = f"""insert into group_par(group_type, model_fk)
        values('{group_type}', {model})    RETURNING    id"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        gop_id = cursor.fetchall()[0][0]
    # получили id созданной группы параметров в таблице group_par
    id_and_list.append(gop_id)

    for cur_param in param_list:
        try:
            title = cur_param['Title']
            symbol = cur_param['Symbol']
            units = cur_param['Units']
            type_inclusion = group_type
        except Exception:
            print("Ошибка в ключах особых параметров")
            return gop_id, -1
        par_m_id_list = cursor_add_extra_def_param(model, gop_id, param_type, title, symbol, units, type_inclusion, con)

    return gop_id, par_m_id_list


def add_flow(model, flow_type, flows, con):
    """Записывает потоки. Принимает номер модели, массив потоков и соединение с БД. Возвращает массив идентификаторов потоков"""
    id_flows_model = []
    for cur_flow in flows:
        try:
            param_index = cur_flow['FlowVariableIndex']
            environment_fk = cur_flow['FlowEnvironment']
        except Exception:
            print("Ошибка в ключах потоков")
            return -1

        if flow_type == 'input':
            qry = f"""INSERT INTO public.flow  (param_index, flow_type , environment_fk , model_fk)
            VALUES('{param_index}', 'input', {environment_fk}, {model})	RETURNING id; """
        elif flow_type == 'output':
            # пока допустим что для любого выходного потока требуется чтобы были определены 2 переменные
            count_def = 2
            qry = f"""INSERT INTO public.flow  	(param_index, flow_type , environment_fk , count_params_out,  model_fk) 
            VALUES('{param_index}', 'output', {environment_fk}, {count_def}, {model})	RETURNING id;"""

        with con.cursor() as cursor:
            try:
                cursor.execute(qry)
                id_flow = cursor.fetchall()[0][0]
                id_flows_model.append(id_flow)
            except Exception:
                print("не удалось выполнить запрос по добавлению потоков")
                return -1

    return id_flows_model


def add_params_from_flow(mod_id, flow_id, con):
    """Добавляет в модель те параметры, которые доступны из-за потока. Принимает номер модели, номер потока и соединение
     с БД. Возвращает массив идентификаторов вставленных параметров """
    problem_text = ""
    qry1 = f"""select  * from param_of_flow where model={mod_id} and flow={flow_id};"""
    with con.cursor() as cursor:
        cursor.execute(qry1)
        param_to_insert = cursor.fetchall()
        if param_to_insert == None:
            problem_text += ("\nВ потоке %s для модели %d не найдены параметры" % (flow_id, mod_id))
        else:
            pog_list = []
            pom_inserted_list = []
            for param in param_to_insert:
                model = param[0]
                flow_type = param[1]
                p_id = param[2]
                pog_id = param[3]
                param_name = param[5]
                p_dict = {"model": model, "param_name": param_name, "p_id": p_id, "pog_id": pog_id}
                qry2 = f"""insert into param_of_model ( model_fk, param_fk, param_name, param_type) values ({model}, {p_id},'{param_name}', 'flow') RETURNING  *;"""
                with con.cursor() as cursor:
                    cursor.execute(qry2)
                    pom_inserted = cursor.fetchall()
                if pom_inserted == None:
                    problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
                else:
                    pom_id = pom_inserted[0][0]
                    p_dict['pom_id'] = pom_id
                pog_list.append(p_dict)

            for ins in pog_list:
                param_group_fk = ins["pog_id"]
                param_of_model_fk = ins["pom_id"]
                type_of_inclusion = flow_type + " flow " + str(flow_id)
                qry3 = f"""insert into all_inclusions ( param_group_fk, param_of_model_fk, type_inclusion)  values ({param_group_fk},'{param_of_model_fk}', '{type_of_inclusion}') RETURNING  *;"""
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
        return -1


def cursor_insert_calc_param(model, p_name, group_id , type_incl, con):
    with con.cursor() as cursor:
        qry3 = f"""select pog.param_fk, pom.id 	from all_inclusions a_i
        join param_of_group pog on a_i.param_group_fk=pog.id
        join param_of_model pom on pom.id =a_i.param_of_model_fk
        where pom.model_fk={model} and param_name='{p_name}';"""
        cursor.execute(qry3)
        future_ai = cursor.fetchall()
        parametr_id = future_ai[0][0]
        pom_id = future_ai[0][1]

        qry4 = f"""INSERT INTO public.param_of_group (param_fk, group_fk) 
        VALUES({parametr_id}, {group_id}) RETURNING id;"""
        cursor.execute(qry4)
        parametr_group_id = cursor.fetchall()[0][0]

        qry5 = f"""insert into public.all_inclusions (param_group_fk, param_of_model_fk, type_inclusion)
        values ({parametr_group_id}, {pom_id}, '{type_incl}');"""
        cursor.execute(qry5)
    return parametr_group_id

def cursor_add_calculation(model_id, order_c, expres, con):
    with con.cursor() as cursor:
        qry1 = f"""insert into group_par(group_type, model_fk)
        values('required_for_calc', {model_id}) RETURNING id;"""
        cursor.execute(qry1)
        group_required = cursor.fetchall()[0][0]

        qry2 = f"""insert into group_par(group_type, model_fk)
        values('defined_from_calc', {model_id}) RETURNING id;"""
        cursor.execute(qry2)
        group_defined = cursor.fetchall()[0][0]

        qry3 = f"""insert into calculation (order_calc, expression_calc, required_params_fk, defined_param_fk, model_fk)
        values ({order_c}, '{expres}',{group_required} ,{group_defined} ,{model_id} ) returning id;"""
        cursor.execute(qry3)
        id_calc = cursor.fetchall()[0][0]
    return id_calc, group_required, group_defined

def add_calc(mod_id, calc_list, con):
    """Заполняет таблицу расчетных выражений. Принимает номер модели, массив записей о выражениях и соединение
         с БД. Возвращает массив идентификаторов вставленных выражений """
    id_list = []
    for calculation in calc_list:
        try:
            order_calc = calculation['Order']
            express_calc = calculation['Expression']
            defined_param = calculation['DefinedVariable']
            required_params_list = calculation['NeededVariables']
        except Exception:
            print("Ошибка в ключах calculation")
            return -1

        try:
            id_calc, group_required, group_defined = cursor_add_calculation(mod_id, order_calc, express_calc, con)
        except Exception:
            print("Ошибка в добавлении выражения calculation ", express_calc,  " модели ", "mod_id")
            return -1

        id_list.append(id_calc)
        id_required_params_group = group_required
        id_defined_params_group = group_defined

        try:
            type_inclusion = "defined for " + str(id_calc)
            cursor_insert_calc_param(mod_id, defined_param, id_defined_params_group, type_inclusion, con)

            for req in required_params_list:
                type_inclusion = "required for " + str(id_calc)
                cursor_insert_calc_param(mod_id, req, id_required_params_group, type_inclusion, con)
        except Exception:
            print("Ошибка в добавлении параметров для выражения  ", express_calc)
            return -1

    return id_list


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
                    variable_prototype = {'ParametrId': executed[4], 'Title': executed[5],
                                          'Symbol': executed[6], 'Units': executed[7]}
                    vars_desc.append({'FlowVariableId': flow_variable_id, 'FlowId': flow_id,
                                      'FlowVariableName': flow_variable_name,
                                      'VariablePrototype': variable_prototype})
                if type == "input":
                    dict_all = {'AvailableVariables': vars_desc, 'FlowVariablesIndex': flow_variable_index,
                                'FlowId': flow_id}
                elif type == "output":
                    dict_all = {'RequiredVariables': vars_desc, 'FlowVariablesIndex': flow_variable_index,
                                'FlowId': flow_id, 'CountOfMustBeDefinedVars': count_req}
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
                    dict_all = {'ParametrId': param_id, 'VariableName': varname,
                                'Title': title, 'Units': units}
                    params_list.append(dict_all)
    return params_list, problem_param_text, flag


def show_expressions(mode_id, expressions, con):
    expressions_list = []
    problem_expres_text = ""
    flag = False  # поднимается если ошибка критическая для модели
    if expressions is None or (len(expressions) == 0):
        problem_expres_text += ("\nСловарь %s из модели номер %d пуст" % ("expressions", mode_id))
        # flag = True
        return expressions_list, problem_expres_text, -1
    for e in expressions:
        qry = f"""select * from calculation where id={e};"""
        with con.cursor() as cursor:
            cursor.execute(qry)
            result_sql = cursor.fetchall()
        if (result_sql is None) or (len(result_sql) == 0):
            problem_expres_text += ("\nДанные для расчетного выражения %s из модели номер %d не найдены" % (
                e, mode_id))
            return expressions_list, problem_expres_text, -1
        #    flag = True
        e_info = result_sql[0]
        try:
            calc_id = e_info[0]
            calc_order = e_info[1]
            calc_text = e_info[2]
            group_defined = e_info[3]
            group_required = e_info[4]
        except:
            return -1

        dict_all = {'ExpressionId': calc_id, 'Order': calc_order, 'Expression': calc_text,
                    'DefinedVariableId': group_defined, 'NeededVariables': group_required}
        expressions_list.append(dict_all)
    return expressions_list, problem_expres_text, flag


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
            var_info = {'name':needed_var, 'type': type, 'pom_id': param_of_model, 'p_id': par_id}
            needed_list.append(var_info)
            dict['NeededVariables'] = needed_list

    for ex in calc_list:
        print (ex)
    return calc_list

def create_scheme(name, con):
    qry = f"""insert into scheme (scheme_name) values ('{name}') returning id;"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        result_sql = cursor.fetchall()
    scheme_id = result_sql[0][0]
    return scheme_id

def create_topography( x, y, con):
    qry = f"""insert into topography (x, y) values ({x}, {y}) returning id;"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        result_sql = cursor.fetchall()
    topog_id = result_sql[0][0]
    return topog_id

def create_instance(model, scheme, topography, con):
    qry = f"""insert into instnc (model_fk, topography_fk, scheme_fk, instance_type) 
        values ({model}, {topography}, {scheme}, 'block') returning id;"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        result_sql = cursor.fetchall()
    instance_id = result_sql[0][0]
    return instance_id


def insert_param_of_instnc(instance, pom, param_name, con):
    qry = f"""insert into param_of_instnc (instance_fk, pom_fk, param_name) 
        values ({instance}, {pom}, '{param_name}') returning id;"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        result_sql = cursor.fetchall()
    poi_id = result_sql[0][0]
    return poi_id

def insert_scheme_flow(from_instance, to_instance, scheme, from_flow, to_flow, con):
    qry = f"""insert into scheme_flows (from_instance_fk, to_instance_fk, scheme_fk, from_flow_fk, to_flow_fk) 
        values ({from_instance}, {to_instance}, {scheme}, {from_flow}, {to_flow}) returning id;"""
    with con.cursor() as cursor:
        cursor.execute(qry)
        result_sql = cursor.fetchall()
    sh_id = result_sql[0][0]
    return sh_id

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


if __name__ == '__main__':
    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="PNI3_v7"
    )
    v = db2.add_params_from_flow(56, 144)
