import json

from app.db.interaction import func_sql
from app.db.exceptions import ModelProblems
import psycopg2
import random


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
                'NeededVariables': [], 'DefinedVariable': def_var_id}

        qry_required_vars = ["select c_id, array_agg(id), array_agg(param_name) "
                             "from show_calc_required where c_id=%s group by c_id;", [id_calc]]
        with con.cursor() as cursor:
            cursor.execute(qry_required_vars[0], qry_required_vars[1])
            result_required_vars = cursor.fetchall()
        try:
            req_var_id_list = result_required_vars[0][1]
            req_var_name_list = result_required_vars[0][2]
            dict = {'ExpressionId': id_calc, "ExpressionType": type_calc, 'Order': order, 'Expression': exp_text,
                    'NeededVariables': req_var_id_list, 'DefinedVariable': def_var_id}
        except Exception:
            print(f"""В %s модели отсутствуют необходимые переменные для выражения %s""" % (model_id, id_calc))

        calc_list.append(dict)

    return calc_list
    # return expressions_list, problem_expres_text, flag


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


class DbConnection:
    def __init__(self, host, user, password, database, port=5432):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
        )
        self.connection.autocommit = True

    class Directory(dict):
        def __init__(self):
            dict.__init__(self, CatalogId=0, CatalogName="", Models=[], Children=[])
            self.dict = {}

        def set_id_and_name(self, cat_id, name):
            self["CatalogId"] = cat_id
            self["CatalogName"] = name

    class CatalogModel(dict):
        def __init__(self, model_id, model_name):
            dict.__init__(self, ModelId=model_id, Title=model_name)


    def model_info(self, model_id):
        qry = f"""select * from model_of_block where id={model_id};"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            model = cursor.fetchall()
        description_list = []
        problem_text = ""

        model_id = model[0]
        title = model[1]
        description = model[2]
        input_flows = model[4]
        output_flows = model[5]
        default_params = model[6]
        extra_params = model[7]
        expressions = model[8]

        critical_flag = False

        input_flows_list, problem_flow, flag_flow = func_sql.show_flows \
            (model_id, "input", input_flows, self.connection)
        problem_text += problem_flow
        critical_flag += flag_flow
        output_flows_list, problem_flow, flag_flow = func_sql.show_flows \
            (model_id, "output", output_flows, self.connection)
        problem_text += problem_flow
        critical_flag += flag_flow

        if extra_params != []:
            extra_params_list, problem_params, flag_params = func_sql.show_extra_default_params \
                (model_id, "extra", extra_params, self.connection)
        else:
            extra_params_list = []
            problem_params = ("в модели %s нет дополнительных параметров" % (model_id))
            flag_params = 0
        problem_text += problem_params
        critical_flag += flag_params

        if default_params != []:
            default_params_list, problem_params, flag_params = func_sql.show_extra_default_params \
                (model_id, "default", default_params, self.connection)
        else:
            default_params_list = []
            problem_params = ("в модели %s нет параметров по умолчанию" % (model_id))
            flag_params = 0

        problem_text += problem_params
        critical_flag += flag_params

        expressions_list = func_sql.show_expressions \
            (model_id, expressions, self.connection)
        # problem_text += problem_expressions
        # critical_flag += flag_expression

        if (critical_flag > 0) or ((len(input_flows_list) < 1) and (len(output_flows_list) < 1)):
            problem_text += ("\nМодель номер %d не будет отображена\n" % model_id)
        else:
            model_desc = {'ModelId': model_id, 'Title': title, 'Description': description,
                          'InputFlows': input_flows_list, 'OutputFlows': output_flows_list,
                          'DefaultParameters': default_params_list, 'CustomParameters': extra_params_list,
                          'Expressions': expressions_list}
            description_list.append(model_desc)
            return description_list


    def get_catalogs(self):
        qry_all = f"""select * from directory order by id desc;"""
        qry_models = f"""select directory_fk, model_fk, title  from directory_model inner join model_of_block on directory_model.model_fk = model_of_block.id;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_all)
            dirs = cursor.fetchall()
            cursor.execute(qry_models)
            all_models = cursor.fetchall()
        # print(dirs)
        print(all_models)

        dirs_tree_root = self.Directory()
        dirs_tree_root.set_id_and_name(0, "__root__")
        level_stack = [dirs_tree_root]
        # print(dirs_tree_root)
        # print(level_stack)

        while len(level_stack) > 0:
            current_catalog_id = (level_stack[len(level_stack) - 1])["CatalogId"]
            current_catalog_id = None if current_catalog_id == 0 else current_catalog_id
            # print(current_catalog_id)
            founded_children = [x for x in dirs if x[2] == current_catalog_id]
            # print(founded_children)
            if len(founded_children) == 0:
                print("levelUp")
                dirs = [x for x in dirs if x[0] != current_catalog_id]
                # Вот тут надо написать код по напихиванию в Models моделей
                founded_models = [model for model in all_models if model[0] == current_catalog_id]
                models = list(map(lambda x: self.CatalogModel(x[1], x[2]), founded_models))
                print(models)
                removed = level_stack.pop()
                removed["Models"].extend(models)
            else:
                print("Processed ", founded_children[0][0])
                new_children = self.Directory()
                new_children.set_id_and_name(founded_children[0][0], founded_children[0][1])
                level_stack[len(level_stack) - 1]["Children"].append(new_children)
                level_stack.append(new_children)

        return dirs_tree_root



if __name__ == '__main__':
    # db2 = DbConnection(
    #     host='localhost',
    #     user="postgres",
    #     password="root",
    #     database="pni_v12"
    # )

    db2 = DbConnection(
        host='91.103.252.95',
        user="postgres",
        password="ThermalUpPGPass",
        database="postgres",
        port=3100
    )


    print(json.dumps(db2.get_catalogs()))
