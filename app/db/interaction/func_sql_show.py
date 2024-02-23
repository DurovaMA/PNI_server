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
    def __init__(self, host, user, password, database):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.connection.autocommit = True

    class Directory(dict):
        def __init__(self):
            self.dict = {
                "CatalogId": 0,
                "CatalogName": "",
                "Models": [],
                "Children": []
            }

        def __str__(self):
            return self.dict

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

    # def show_childs_in_catalog(catalog_id, con):
    #     qry_directories = f"""select d.id, d.dir_name,  d2.dir_name, d2.id  from directory d
    #     left join directory d2 on d.id =d2.parent_level_fk where d.id = {catalog_id};"""
    #     with con.cursor() as cursor:
    #         cursor.execute(qry_directories)
    #         all_directories = cursor.fetchall()
    #     catalog_dict = {}
    #     catalog_list = []
    #     for dir in all_directories:
    #         try:
    #             catalog_id = dir[0]
    #             dir_name = dir[1]
    #             child_name = dir[2]
    #             child_id = dir[3]
    #         except Exception:
    #             print("Невозможно прочитать каталоги")
    #             return -1
    #         catalog_dict = {'CatalogId': catalog_id}
    #     return
    def show_childs_in_catalog(self, catalog_id):
        qry_directories = f"""select d.id, d.dir_name,  d2.dir_name, d2.id  from directory d 
        left join directory d2 on d.id =d2.parent_level_fk where d.id = {catalog_id};"""
        with self.connection.cursor() as cursor:
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
            while child_id is not None:
                childs = self.show_childs_in_catalog(catalog_id)
                catalog_dict = {'CatalogId': catalog_id, 'Direct_name': dir_name, 'childs': childs}
                catalog_list.append(catalog_dict)
        return catalog_list

    def show_catalog(self):
        qry_directories = f"""select * from directory d where parent_level_fk is Null  ;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_directories)
            all_directories = cursor.fetchall()
        catalog_dict = {}
        catalog_list = []
        # здесь перебираем все каталоги, у которых нет родительского - то есть все корневые
        for dir in all_directories:
            try:
                catalog_id = dir[0]
                dir_name = dir[1]
            except Exception:
                print("Невозможно прочитать каталоги")
                return -1
            childs = self.show_childs_in_catalog(catalog_id)
            catalog_dict = {'CatalogId': catalog_id, 'Direct_name': dir_name, 'childs': childs}
            catalog_list.append(catalog_dict)
        return catalog_list

    # def show_models_catalog(self):
    #     qry_directories = f"""select * from models_catalog order by (level, id) desc;"""
    #     with self.connection.cursor() as cursor:
    #         cursor.execute(qry_directories)
    #         models = cursor.fetchall()
    #     catalog_dict = {}
    #     catalog_list = []
    #     lev = 0
    #     parent_id = 0
    #     cur_catalog_id = 0
    #     childs = []
    #     cur_catalog_list = []
    #     cur_model_desc = {}
    #     for m in models:
    #         try:
    #             model_id, title, catalog_id, parent_catalog_id, dir_name, level = m[0], m[1], m[2], m[3], m[4], m[5]
    #         except Exception:
    #             print("Невозможно прочитать модели в каталогах")
    #             return -1
    #         if cur_catalog_id != catalog_id: #если данная модель находится в другом каталоге
    #             cur_model_desc = {'ModelId': model_id, 'Title': title}
    #             cur_catalog_list = [cur_model_desc]
    #             cur_catalog_id = catalog_id
    #             cur_catalog_dict = {'CatalogId': cur_catalog_id, 'Direct_name': dir_name}
    #             catalog_list.append(cur_catalog_dict)
    #             cur_catalog_dict['Models'] = cur_catalog_list
    #         else:
    #             cur_model_desc = {'ModelId': model_id, 'Title': title}
    #             cur_catalog_list.append(cur_model_desc)
    #     return catalog_list

    def create_catalog(self):

        qry_directories = f"""select * from view_catalog order by level;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_directories)
            directories = cursor.fetchall()
        cur_childs = []
        cur_parent = 0

        parent_child_dict = {}
        for dir in directories:
            try:
                id_parent, parent_name, child_name, child_id, level = dir[0], dir[1], dir[2], dir[3], dir[4]
            except Exception:
                print("Невозможно прочитать каталоги")
                return -1
            if id_parent != cur_parent:
                cur_parent = id_parent
                cur_childs = [{'child_id': child_id, 'child_name': child_name}]
                # if parent_child_dict['child_id']
                parent_child_dict[cur_parent] = cur_childs
            else:
                parent_child_dict[cur_parent].append({'child_id': child_id, 'child_name': child_name})

        return parent_child_dict

    def check_childs(self, diction, key):
        print(diction)
        print(type(diction))
        try:
            dicts = diction.keys()
            list = []
            for k in dicts:
                list.append(self.check_childs(diction[k], k))
            return list
        except:
            return []

    def show_catalog2(self):

        qry_max_level = f"""select max(level) from view_catalog;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_max_level)
            max_level = cursor.fetchall()[0][0]

        qry_directories = f"""select  id_parent,parent_name,  child_name, id_child, level from view_catalog order by 
                            (level, id_parent) desc;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_directories)
            directories = cursor.fetchall()
        cur_childs = []
        cur_parent = 0
        parent_child_dict = {}
        level = 0
        prev_parent = 0
        prev_parent_child_dict = {}
        cur_dict = []
        prev_childs = {}
        new_parent_child_dict = {}
        for dir in directories:
            try:
                id_parent, parent_name, child_name, child_id, level = dir[0], dir[1], dir[2], dir[3], dir[4]
            except Exception:
                print("Невозможно прочитать каталоги")
                return -1
            child_dict = {'id_parent': id_parent, 'parent_name': parent_name, 'child_name': child_name,
                          'child_id': child_id}

            try:
                new_parent_child_dict[id_parent][child_id] = {}
            except:
                new_parent_child_dict[id_parent] = {child_id: {}}
        # print(new_parent_child_dict)

        for dict in new_parent_child_dict.keys():
            for d in new_parent_child_dict[dict]:
                if d in new_parent_child_dict.keys():
                    new_parent_child_dict[dict][d] = new_parent_child_dict[d]

        parent_child_dict = new_parent_child_dict[None]
        next_dict = parent_child_dict
        list = []
        level = 1

        list_dicts = []
        for dir in next_dict.keys():
            qry_models = f"""select model_id, title from models_catalog where id =  {dir}"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry_models)
                models = cursor.fetchall()
            new_dict = {}
            new_dict['CatalogId'] = dir
            new_dict['Models'] = models
            new_dict['Childs'] = []
            try:
                new_dict['Childs'] = next_dict[dir]
            except:
                new_dict['Childs'] = []
            list_dicts.append(new_dict)
            # print(list_dicts)
        flag = True

        return parent_child_dict

    def show_models_in_catalog2(self, catalog):
        flag = True
        while flag:
            flag = False
            i = 0
            try:
                print(catalog.keys())
                for c in catalog.keys():
                    self.show_models_in_catalog(catalog[c][0])
                    try:
                        catalog = catalog[c][0]
                    except:
                        print('end')
                flag = True
            except:
                pass

    def show_models_in_catalog(self, catalog):
        print(catalog)
        flag = True
        list1 = []
        while flag:
            if (type(catalog) == list) and (catalog != []):
                catalog = catalog[0]
                for c in catalog.keys():
                    m = self.show_models_in_catalog(catalog[c])
                    # print(m)
                    list1.append(m)
            else:
                flag = False
                return catalog
        return list1

    def create_graph(self):
        qry_max_level = f"""select max(level) from view_catalog;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_max_level)
            max_level = cursor.fetchall()[0][0]

        qry_directories = f"""select  id_parent,parent_name,  child_name, id_child, level from view_catalog
                            order by (level, id_parent) desc;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_directories)
            directories = cursor.fetchall()
        dict_level = {}
        graph = {}
        for dir in directories:
            id_parent, parent_name, child_name, child_id, cur_level = dir[0], dir[1], dir[2], dir[3], dir[4]
            try:
                dict_level[cur_level].append(
                    {'id_parent': id_parent, 'parent_name': parent_name, 'child_name': child_name,
                     'child_id': child_id})
            except:
                dict_level[cur_level] = [{'id_parent': id_parent, 'parent_name': parent_name, 'child_name': child_name,
                                          'child_id': child_id}]
        root_nodes = []
        for dict in dict_level[1]:
            node = Directory(dict['child_id'])
            root_nodes.append(node)
        prev_nodes = root_nodes
        for l in range(2, max_level + 1):
            cur_nodes = []
            for dict in dict_level[l]:

                node = Directory(dict['child_id'])
                cur_nodes.append(node)
                for par_node in prev_nodes:
                    if dict['id_parent'] == par_node.id:
                        par_node.append_child(dict['child_id'])
            prev_nodes = cur_nodes

        c = root_nodes[0]
        while c.childs:
            print(c.id)
            c = root_nodes
            # node.parent =
            # dir_list.append(root.append_child(7).append_child(4))
            # dir_list.append(root.append_child(13))
            #
            # for c in root.childs:
            #     while root.childs:
            #         print(c.id)

            # lev = dict_level[l-1]
            # for dict_cur in dict_level[l-1]:
            #     if dict['id_parent'] == dict_cur['child_id']:
            #         try:
            #             graph[child_id].append()

        return dict_level

    def show_catalog(self):

        qry_max_level = f"""select max(level) from view_catalog;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_max_level)
            max_level = cursor.fetchall()[0][0]

        qry_directories = f"""select  id_parent,parent_name,  child_name, id_child, level from view_catalog 
                            order by (level, id_parent) desc;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_directories)
            directories = cursor.fetchall()

        cur_level_parents = {}  # здесь по ключам родителей лежат СПИСКИ детей
        cur_child_list = []
        cur_child = {}
        prev_level_parents = {}  # здесь будем проверять ключи и брать те списки, которые совпадают с текущим child_id
        prev_parent_id = 0
        level = 0
        parents_childs_dict = {}
        for dir in directories:
            try:
                id_parent, parent_name, child_name, child_id, cur_level = dir[0], dir[1], dir[2], dir[3], dir[4]
            except Exception:
                print("Невозможно прочитать каталоги")
                return -1
            cur_child = {'id': child_id, 'name': child_name, 'child': []}
            if prev_parent_id != id_parent:  # если это новый родитель, то список его детей обновляется
                cur_child_list = [cur_child]
            else:
                cur_child_list.append(cur_child)
            cur_level_parents[id_parent] = cur_child_list

            if level != cur_level:
                level = cur_level
                prev_level_parents = cur_level_parents
                try:
                    prev_level_parents[child_id]['childs'] = cur_level_parents
                except:
                    pass
        return cur_level_parents

    def show_models_catalog(self):
        qry_directories = f"""select * from models_catalog order by (level, id) desc;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_directories)
            models = cursor.fetchall()
        catalog_dict = {}
        catalog_list = []
        lev = 0
        parent_id = 0
        cur_catalog_id = 0
        childs = []
        cur_catalog_list = []
        cur_model_desc = {}

        for m in models:
            try:
                model_id, title, catalog_id, parent_catalog_id, dir_name, level = m[0], m[1], m[2], m[3], m[4], m[5]
            except Exception:
                print("Невозможно прочитать модели в каталогах")
                return -1
            if cur_catalog_id != catalog_id:  # если данная модель находится в другом каталоге

                cur_model_desc = {'ModelId': model_id, 'Title': title}
                cur_catalog_list = [cur_model_desc]
                cur_catalog_id = catalog_id
                cur_catalog_dict = {'CatalogId': cur_catalog_id, 'Direct_name': dir_name}
                catalog_list.append(cur_catalog_dict)
                cur_catalog_dict['Models'] = cur_catalog_list
            else:
                cur_model_desc = {'ModelId': model_id, 'Title': title}
                cur_catalog_list.append(cur_model_desc)
        return catalog_list

    def show_f_catalog(self):
        base_models = {
            "ModelId": 0,
            "Title": ""
        }
        base_catalog = {
            "CatalogId": 0,
            "CatalogName": "",
            "Models": [],
            "Children": []
        }
        # qry_oldest = f"""select * from directory d where d.parent_level_fk is null;"""
        # with self.connection.cursor() as cursor:
        #     cursor.execute(qry_oldest)
        #     oldest_levels = cursor.fetchall()
        #
        # all_dirs = []
        # for d in oldest_levels:
        #     cur_dir = base_catalog.copy()
        #     cur_dir["CatalogId"] = d[0]
        #     cur_dir["CatalogName"] = d[1]
        #     all_dirs.append(cur_dir)

        qry_all = f"""select parent.id id_current, parent.dir_name current_name,  child.dir_name child_name, child.id id_child 
	from directory parent
	full join directory child on parent.id =child.parent_level_fk order by id_child desc;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_all)
            all_levels = cursor.fetchall()

        all_dirs = []
        for d in all_levels:
            if d[0] is None:
                cur_dir = base_catalog.copy()
                cur_dir["CatalogId"] = d[3]
                cur_dir["CatalogName"] = d[2]
                all_dirs.append(cur_dir)
            else:
                pass

        return all_dirs

    def show_f_catalog2(self):
        base_models = {
            "ModelId": 0,
            "Title": ""
        }

        base_catalog = {
            "CatalogId": 0,
            "CatalogName": "",
            "Models": [],
            "Children": []
        }

        qry_all = f"""select parent.id id_current, parent.dir_name current_name,  child.dir_name child_name, child.id id_child 
	from directory parent
	full join directory child on parent.id =child.parent_level_fk order by id_child desc;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_all)
            all_levels = cursor.fetchall()

        all_dirs = []
        buf_children = {}
        buf_parents = {}
        buf_all = []
        flag = True
        while flag:
            flag = False
            for d in all_levels:
                id_cur = d[0]
                id_child = d[3]
                if id_cur is None:
                    cur_dir = self.Directory().dict
                    cur_dir["CatalogId"] = d[0]
                    cur_dir["CatalogName"] = d[1]
                    cur_dir["Children"].append(buf_children.pop(id_child))
                    buf_all.append(cur_dir)
                if id_child is None:  # если нет детей у каталога
                    cur_dir = self.Directory().dict
                    cur_dir["CatalogId"] = d[0]
                    cur_dir["CatalogName"] = d[1]
                    buf_children[d[0]] = cur_dir.copy()
                    parent_keys = buf_parents.keys()
                    if id_child in parent_keys:
                        cur_dir["Children"].append(buf_parents.pop(id_child))
                else:
                    cur_dir2 = self.Directory().dict
                    cur_dir2["CatalogId"] = d[0]
                    cur_dir2["CatalogName"] = d[1]
                    child_keys = buf_children.keys()
                    if id_child in child_keys:
                        child = buf_children.pop(id_child)
                        cur_dir2["Children"].append(child)
                    else:
                        ch = self.Directory().dict
                        ch["CatalogId"] = d[3]
                        ch["CatalogName"] = d[2]
                        buf_children[d[3]] = ch.copy()
                        # buf_parents[d[0]] = cur_dir2.copy()  # родитель, которому не нашлось пока дочернего
                    buf_children[d[0]] = cur_dir2.copy()
                    parent_keys = buf_parents.keys()
                    if id_child in parent_keys:
                        cur_dir["Children"].append(buf_parents.pop(id_child))
                    # третий каталог куда-то теряется, потому что у него есть дочерний каталог
            if buf_parents != {}:
                flag = True
            # if None in buf_children.keys():
            #     flag = True
        return buf_children, buf_parents, buf_all

    def deep_keys(self,  buf=None, res=None, res_dict=None):
        if not buf:
            buf = {}
        if not res:
            res = []
        if not res_dict:
            res_dict = {}

        for key1, value1 in buf.items():
            cur_lev = self.Directory().dict
            cur_lev["CatalogId"] = key1
            cur_lev["Children"].append(value1)
            res.append(cur_lev)
            if type(value1) == dict:
                self.deep_keys(value1, res)

        return res

    def deep_keys2(self, list,  buf=None, res=None):
        if not buf:
            buf = {}
        if not res:
            res = []
        for l in list:
            id = l['CatalogId']
            for key1, value1 in buf.items():
                if key1 == id:
                    self.deep_keys2(list, l['CatalogId'])
                elif type(value1) == dict:
                    self.deep_keys2(list=list, buf=value1)

        return res

    def deep_keys3(self,  buf=None, res=None, res_dict=None, i=None):
        if not buf:
            buf = {}
        if not res:
            res = []
        if not res_dict:
            res_dict = []
        if not i:
            i = 0

        for key1, value1 in buf.items():
            cur_lev = self.Directory().dict
            cur_lev["i"] = i
            cur_lev["CatalogId"] = key1
            childs = value1
            #cur_lev["Children"].append(childs)
            res = cur_lev
            if type(childs) == dict:
                i = i + 1
                cur_lev["Children"] = []
                res2 = self.deep_keys3(buf=childs, res_dict=res_dict, res=res, i=i)
                cur_lev["Children"].append(res2)
                i = i-1
            else:
                cur_lev["Children"] = []
            res_dict.append(cur_lev)
        return res_dict
    def show_f_catalog3(self):

        qry_all = f"""select parent.id id_current, parent.dir_name current_name,  child.dir_name child_name, child.id id_child 
	from directory parent
	full join directory child on parent.id =child.parent_level_fk order by id_child desc;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_all)
            all_levels = cursor.fetchall()

        all_dirs = []
        buf_children = {}
        ParentChild = {}
        buf_all = []

        for d in all_levels:
            id_cur = d[0]
            id_child = d[3]
            if id_child is not None:
                parent_keys = ParentChild.keys()
                if id_cur not in parent_keys:
                    ParentChild[id_cur] = {id_child: []}
                else:
                    ParentChild[id_cur][id_child] = []

        flag = True
        buf = ParentChild.copy()
        while flag:
            parent_keys = ParentChild.keys()
            p = ParentChild.items()

            for key, value in buf.items():
                for v in value:
                    if v in parent_keys:
                        ParentChild[key][v] = ParentChild.pop(v)

            parent_keys_len = len(ParentChild.keys())
            if parent_keys_len == 1:
                flag = False

        buf = ParentChild.copy()
        # for key1, value1 in buf.items():
        #     cur_lev = self.Directory().dict
        #     cur_lev["CatalogId"] = key1
        #     #if type(value1) == dict:
        #     cur_lev["Children"].append(value1)
        #     for v1 in value1:
        #         child_lev = self.Directory().dict
        #         child_lev["CatalogId"] = v1
        #         child_lev["Children"].append(value1[v1])
        res = self.deep_keys(buf)
        return res, buf


# class Directory:
#     def __init__(self, data):
#         self.id = data  # Назначаем дату
#         self.parent = None  # Инициализируем следующий узел как «null»
#         self.childs = []
#
#     def append_child(self, val):
#         end = Directory(val)
#         n = self
#         n.childs.append(end)
#         end.parent = n





if __name__ == '__main__':
    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="pni_v12"
    )

    # c, p, a = db2.show_f_catalog2()
    # print(c)
    # print(p)
    # print(a)
    list, buf = db2.show_f_catalog3()
    print(buf)
    #for b in list:
        #print(b)
    res2 = db2.deep_keys3(buf=buf)
    print(res2)

    # for key1, value1 in buf.items():
    #     cur_lev = db2.Directory().dict
    #     cur_lev["CatalogId"] = key1
    #     cur_lev["Children"].append(value1)
    #     res.append(cur_lev)
    #     if type(value1) == dict:
    #         db2.deep_keys(list=res, buf=value1,  res=res)
    # v = []
    # v.append(db2.show_catalog2())
    # print(v[0])
    # tree = {'a': {'b': {'c': {}, 'd': {}}, 'e': {}, 'f': {}, 'g': {}}}
    # print(deep_keys(v[0]))
    # db2.show_models_in_catalog(v)
