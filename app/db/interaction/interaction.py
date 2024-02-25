from app.db.interaction import func_sql, func_sql_show, func_sql_insert
from app.db.exceptions import ModelProblems
import psycopg2
import random


class DbConnection:
    def __init__(self, db_host, user, password, database, db_port):
        self.connection = psycopg2.connect(
            host=db_host,
            user=user,
            password=password,
            database=database,
            port=db_port
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
                p_of_e.append(p[0])
            env_list.append({'FlowEnvironmentId': e[0], 'FlowEnvironmentType': e[1], 'BaseParameters': p_of_e})

        request_dict["BaseParameters"] = param_list
        request_dict["FlowEnvironments"] = env_list

        if request_dict:
            return request_dict
        # else:
        #    raise ParametrNotFoundException('Environments not found!')


    def get_model_catalog_info(self):
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
    def get_models_info(self):
        qry = f"""select * from model_of_block;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            models = cursor.fetchall()
        description_list = []
        description_dict = {}
        problem_list = []

        if len(models) == 0:
            problem_list.append("Моделей в базе нет")
        for m in models:
            problem_text = ""
            print(m)
            model_id = m[0]
            title = m[1]
            description = m[2]
            input_flows = m[4]
            output_flows = m[5]
            default_params = m[6]
            extra_params = m[7]
            expressions = m[8]

            critical_flag = False

            input_flows_list, problem_flow, flag_flow = func_sql_show.show_flows \
                (model_id, "input", input_flows, self.connection)
            problem_text += problem_flow
            critical_flag += flag_flow
            output_flows_list, problem_flow, flag_flow = func_sql_show.show_flows \
                (model_id, "output", output_flows, self.connection)
            problem_text += problem_flow
            critical_flag += flag_flow

            if extra_params != []:
                extra_params_list, problem_params, flag_params = func_sql_show.show_extra_default_params \
                    (model_id, "extra", extra_params, self.connection)
            else:
                extra_params_list = []
                problem_params = ("в модели %s нет дополнительных параметров" % (model_id))
                flag_params = 0
            problem_text += problem_params
            critical_flag += flag_params

            if default_params != []:
                default_params_list, problem_params, flag_params = func_sql_show.show_extra_default_params \
                    (model_id, "default", default_params, self.connection)
            else:
                default_params_list = []
                problem_params = ("в модели %s нет параметров по умолчанию" % (model_id))
                flag_params = 0

            problem_text += problem_params
            critical_flag += flag_params


            expressions_list = func_sql_show.show_expressions \
                (model_id, expressions, self.connection)
            #problem_text += problem_expressions
            # critical_flag += flag_expression

            if (critical_flag > 0) or ((len(input_flows_list) < 1) and (len(output_flows_list) < 1)):
                problem_text += ("\nМодель номер %d не будет отображена\n" % model_id)
            else:
                model_desc = {'ModelId': model_id, 'Title': title, 'Description': description,
                              'InputFlows': input_flows_list, 'OutputFlows': output_flows_list,
                              'DefaultParameters': default_params_list, 'CustomParameters': extra_params_list,
                              'Expressions': expressions_list}
                description_list.append(model_desc)
                description_dict[model_id] = model_desc
            problem_list.append(problem_text)

        print('\n'.join(map(str, problem_list)))
        return description_list, description_dict

    def get_info_model(self):
        '''Функция для создания аналога в графовой БД. Возвращает инфо об одной модели'''
        qry = f"""select * from model_of_block limit 1;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)
            models = cursor.fetchall()
        description_list = []
        description_dict = {}
        problem_list = []

        if len(models) == 0:
            problem_list.append("Моделей в базе нет")
        for m in models:
            problem_text = ""
            print(m)
            model_id = m[0]
            title = m[1]
            description = m[2]
            input_flows = m[4]
            output_flows = m[5]
            default_params = m[6]
            extra_params = m[7]
            expressions = m[8]

            critical_flag = False

            input_flows_list, problem_flow, flag_flow = func_sql_show.show_flows \
                (model_id, "input", input_flows, self.connection)
            problem_text += problem_flow
            critical_flag += flag_flow
            output_flows_list, problem_flow, flag_flow = func_sql_show.show_flows \
                (model_id, "output", output_flows, self.connection)
            problem_text += problem_flow
            critical_flag += flag_flow

            if extra_params != []:
                extra_params_list, problem_params, flag_params = func_sql_show.show_extra_default_params \
                    (model_id, "extra", extra_params, self.connection)
            else:
                extra_params_list = []
                problem_params = ("в модели %s нет дополнительных параметров" % (model_id))
                flag_params = 0
            problem_text += problem_params
            critical_flag += flag_params

            if default_params != []:
                default_params_list, problem_params, flag_params = func_sql_show.show_extra_default_params \
                    (model_id, "default", default_params, self.connection)
            else:
                default_params_list = []
                problem_params = ("в модели %s нет параметров по умолчанию" % (model_id))
                flag_params = 0

            problem_text += problem_params
            critical_flag += flag_params


            expressions_list = func_sql_show.show_expressions \
                (model_id, expressions, self.connection)
            #problem_text += problem_expressions
            # critical_flag += flag_expression

            if (critical_flag > 0) or ((len(input_flows_list) < 1) and (len(output_flows_list) < 1)):
                problem_text += ("\nМодель номер %d не будет отображена\n" % model_id)
            else:
                model_desc = {'ModelId': model_id, 'Title': title, 'Description': description,
                              'InputFlows': input_flows_list, 'OutputFlows': output_flows_list,
                              'DefaultParameters': default_params_list, 'CustomParameters': extra_params_list,
                              'Expressions': expressions_list}
                description_list.append(model_desc)
                description_dict[model_id] = model_desc
            problem_list.append(problem_text)

        print('\n'.join(map(str, problem_list)))
        return description_list, description_dict

    def get_info_instance(self, model_id):
        instance_info = func_sql_show.info_instance(model_id, self.connection)
        return instance_info

    def create_model(self, model_description, model_title, in_flows, out_flows, default_params, extra_params,
                     calculations):
        # массив переменных модели, фигурирующих в ней от потоков
        id_flow_params_list = []

        all_params = default_params + extra_params
        list_params = []
        for param in all_params:
            symbol = param['Symbol']
            list_params.append(symbol)
        visited = set()
        dup = [x for x in list_params if x in visited or (visited.add(x) or False)]
        if dup != []:
            print("Дублируются параметры: ", dup)  # [1, 5, 1]
            return -1

        # dup = func_sql.check_dup(model_title, model_description, self.connection)

        # создание записи в таблице model_of_block
        id_model = func_sql_insert.create_new_model(model_title, model_description, self.connection)

        # создание группы дополнительных параметров в таблице group_par и записей о ней в таблицах parametr,
        # parametr_group, param_of_model и all_inclusions.
        # Возвращает идентификатор группы из таблицы group_par и массив идентификаторов в таблице param_of_model
        id_group_extr, id_extra_params_list = func_sql_insert.add_extra_def_params('extra_params', 'extra', id_model,
                                                                            extra_params, self.connection)
        # Аналогично для параметров по умолчанию
        id_group_def, id_default_params_list = func_sql_insert.add_extra_def_params('default_params', 'default', id_model,
                                                                             default_params, self.connection)
        if id_default_params_list == -1 or id_extra_params_list == -1:
            func_sql_insert.delete_model(id_model, self.connection)
            return -1
        if id_group_extr == 0 or id_extra_params_list == 0:
            print("нет extra параметров")

        # Создает записи о входных и выходных потоках, возвращает массивы идентификаторов из таблицы flow
        id_flows_model_input = func_sql_insert.add_flow(id_model, 'input', in_flows, self.connection)
        id_flows_model_output = func_sql_insert.add_flow(id_model, 'output', out_flows, self.connection)

        if id_flows_model_input == -1 or id_flows_model_output == -1:
            func_sql_insert.delete_model(id_model, self.connection)
            return -1

        # Объединяет массивы входных и выходных потоков
        flows_model = id_flows_model_input + id_flows_model_output

        for flow in flows_model:
            id_flow_params = func_sql_insert.add_params_from_flow(id_model, flow, self.connection)
            if id_flow_params == -1:
                func_sql_insert.delete_model(id_model, self.connection)
                return -1
            id_flow_params_list = id_flow_params_list + id_flow_params

        # массив рассчетных выражений модели
        id_calcs_list = func_sql_insert.add_calc(id_model, calculations, self.connection)

        if id_calcs_list == -1:
            func_sql_insert.delete_model(id_model, self.connection)
            return -1

        if id_calcs_list != -1 and id_extra_params_list != -1 and id_default_params_list != -1 and id_flow_params_list != -1:
            print('Добавлена модель номер ', id_model)
            len_in_flows = len(id_flows_model_input)
            len_out_flows = len(id_flows_model_output)
            len_def_params = len(id_default_params_list)
            len_ext_params = len(id_extra_params_list)
            len_calcs = len(id_calcs_list)
            qry = f"""update model_of_block set input_flows=ARRAY{id_flows_model_input}::integer[{len_in_flows}],
                    output_flows=ARRAY{id_flows_model_output}::integer[{len_out_flows}], 
                    default_params =ARRAY{id_default_params_list}::integer[{len_def_params}],
                    extra_params =ARRAY{id_extra_params_list}::integer[{len_ext_params}], 
                     expressions =ARRAY{id_calcs_list}::integer[{len_calcs}]
                    where id = {id_model};"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
            return id_model
        else:
            return -1
            raise ModelProblems('Не удалось добавить модель!')

    def add_schema(self, name):
        schema_id = func_sql_insert.create_schema(name, self.connection)
        return schema_id

    def create_schema(self, title, instances, interconnections):

        id_schema = func_sql_insert.create_schema(title, self.connection)

        instances_dict = {}
        for ins in instances:
            #ins = instances[i]
            client_instance_id = ins["BlockInstanceId"]
            model_id = ins["BlockModel"]["ModelId"]
            top = ins["OffsetTop"]
            left = ins["OffsetLeft"]
            place_id = self.create_topography(top, left)
            instance_id = self.create_instance(model_id, id_schema, place_id)
            instances_dict[client_instance_id] = instance_id
            for def_v in ins["DefaultVariables"]:
                pom_id = def_v["VariableId"]
                param_name = def_v["VariableName"]
                value = def_v["Value"]
                poi_id = self.insert_param_of_instnc(instance_id, pom_id, param_name, value)

        for intercon in interconnections:
            client_block_output_id = intercon["OutputFlowConnector"]["BlockInstanceID"]
            block_output_id = instances_dict[client_block_output_id]
            flow_output_id = intercon["OutputFlowConnector"]["FlowID"]
            client_block_input_id = intercon["InputFlowConnector"]["BlockInstanceID"]
            block_input_id = instances_dict[client_block_input_id]
            flow_input_id = intercon["InputFlowConnector"]["FlowID"]
            schema_flows_id = self.insert_schema_flow(block_output_id, block_input_id, id_schema,
                                                      flow_output_id, flow_input_id)

        return id_schema
    def show_all_schemas(self):
        qry_all_schemas = f"""select id, schema_name from schema;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_all_schemas)
            all_schemas = cursor.fetchall()
        schemas_list = []
        for sch in all_schemas:
            schemas_dict = {}
            schemas_dict["SchemaId"] = sch[0]
            schemas_dict["SchemaName"] = sch[1]
            schemas_list.append(schemas_dict)
        return schemas_list

    def show_schema(self, schema_id):
        qry_schema = f"""select * from schema where id = {schema_id};"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_schema)
            schema_name = cursor.fetchall()[0][1]

        qry_instances = f"""select * from instnc where schema_fk = {schema_id};"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_instances)
            all_instances = cursor.fetchall()

        instances_list = []
        for ins in all_instances:
            instance_id = ins[0]
            model_id = ins[1]
            position_id = ins[2]
            qry_position = f"""select * from position where id = {position_id};"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry_position)
                position = cursor.fetchall()[0]
            position_top = position[1]
            position_left = position[2]
            qry_def_vars = f"""select * from param_of_instnc where instance_fk = {instance_id};"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry_def_vars)
                def_vars = cursor.fetchall()
            vars_list = []
            for var in def_vars:
                var_dict = {"VariableId": var[2], "Value": var[4]}
                vars_list.append(var_dict)
            instance_dict = {"OffsetLeft": position_left, "OffsetTop": position_top, "BlockModel": {"ModelId": model_id},
                             "BlockInstanceId": instance_id, "DefaultVariables": vars_list}
            instances_list.append(instance_dict)


        qry_interconnections = f"""select * from schema_flows where schema_fk = {schema_id};"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_interconnections)
            all_interconnections = cursor.fetchall()

        interconnections_list = []
        for intercon in all_interconnections:
            block_output_id, block_input_id, flow_output_id, flow_input_id = intercon[1], intercon[2], intercon[4], intercon[5]
            interconnections_dict = {"InputFlowConnector": {"BlockInstanceID": block_output_id, "FlowID": flow_output_id },
                                     "OutputFlowConnector": {"BlockInstanceID": block_input_id, "FlowID": flow_input_id}}
            interconnections_list.append(interconnections_dict)
        schema_dict = {"SchemaId": schema_id, "SchemaName": schema_name, "BlockInstanсes": instances_list, "BlockInterconnections": interconnections_list}
        return schema_dict
    def create_topography(self, x, y):
        topog_id = func_sql_insert.create_topography(x, y, self.connection)
        return topog_id

    def create_instance(self, model, schema, topography):
        instance_id = func_sql_insert.create_instance(model, schema, topography, self.connection)
        return instance_id

    def insert_param_of_instnc(self, instance, pom, param_name, value):
        poi_id = func_sql_insert.insert_param_of_instnc(instance, pom, param_name, value, self.connection)
        return poi_id

    def insert_schema_flow(self, from_instance, to_instance, schema, from_flow, to_flow):
        poi_id = func_sql_insert.insert_schema_flow(from_instance, to_instance, schema, from_flow, to_flow, self.connection)
        return poi_id


if __name__ == '__main__':
    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="pni_v9"
    )

    name = input("Введите имя: ")
    id_schema = db2.add_schema(name)

    print(f"схема номер  {id_schema} добавлена!")

    all_models = db2.get_models_info()[1]

    # print(all_models["Title"])
    print(f"выберите номер модели для создания ее экземпляра:  ")
    for mod in all_models:
        desc = all_models[mod]
        print(desc["ModelId"], desc["Title"])
    model_id = int(input("Модель: "))
    place_id = db2.create_topography(1, 1)
    instance_id = db2.create_instance(model_id, id_schema, place_id)

    print(f"выберите номер второй модели для создания ее экземпляра:  ")
    for mod in all_models:
        desc = all_models[mod]
        print(desc["ModelId"], desc["Title"])
    model_id2 = int(input("Модель 2: "))
    place_id2 = db2.create_topography(1, 1)
    instance_id2 = db2.create_instance(model_id2, id_schema, place_id2)

    print(f"выберите номер потока, который выходит из первого экземпляра:  ")
    desc1 = all_models[model_id]
    for flow in desc1["InputFlows"]:
        print(flow["FlowId"])
    from_flow = input("Выходящий поток: ")

    print(f"выберите номер потока, который входит во второй экземпляр:  ")
    desc2 = all_models[model_id2]
    for flow in desc2["OutputFlows"]:
        print(flow["FlowId"])
    to_flow = input("Входящий поток: ")

    schema_flows_id = db2.insert_schema_flow(instance_id, instance_id2, id_schema, from_flow, to_flow)

    # all_calcs = db2.get_info_instance(model_id)
    #
    # for calc in all_calcs:
    #     neededvars = calc["NeededVariables"]
    #     for var in neededvars:
    #         pom = var['pom_id']
    #         param_name = var['name']
    #         poi = db2.insert_param_of_instnc(instance_id, pom, param_name)
