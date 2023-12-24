from app.db.interaction import func_sql, func_sql_show, func_sql_insert
from app.db.exceptions import ModelProblems
import psycopg2
import random


class DbConnection:
    def __init__(self, host, user, password, database):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.connection.autocommit = True


    def insert_users(self):

        list = ['Горбачев Богдан', 'Иванов Максим', 'Марков Дмитрий', 'Кузин Дмитрий', 'Жуков Денис', 'Павлов Ярослав',
                'Федорова Виктория', 'Андреева Ульяна', 'Савельева Екатерина', 'Матвеева Амина', 'Сидоров Демид',
                'Семенова Ольга', 'Романова Арина', 'Николаева Валерия', 'Морозова Виктория', 'Карпова Есения',
                'Кудрявцев Фёдор', 'Васильева Марьяна', 'Калинина Евгения', 'Давыдова Мария', 'Степанов Павел',
                'Мухина Арина', 'Комарова Надежда', 'Дмитриев Илья', 'Коновалова Полина', 'Афанасьев Дамир',
                'Аксенова Анастасия', 'Архипов Владимир', 'Шубин Егор', 'Рожкова Ксения', 'Ларионов Сергей',
                'Чижов Егор', 'Дементьев Дмитрий', 'Воробьева Алия', 'Олейникова Ксения', 'Матвеев Василий',
                'Тарасов Марк', 'Булгакова Анастасия', 'Кочетова Софья', 'Романова Ульяна', 'Козловская Арина',
                'Сазонов Дмитрий', 'Токарев Тимофей', 'Исаков Михаил', 'Кравцова Василиса', 'Климова Ариана',
                'Савин Михаил', 'Александрова Олеся', 'Кравцова Ксения', 'Куликов Василий', 'Минаева Мария',
                'Борисов Артём', 'Емельянова Алиса', 'Громова Мария', 'Тихонов Ярослав', 'Матвеев Борис',
                'Гришин Арсений', 'Васильев Иван', 'Горлов Александр', 'Осипова Анастасия', 'Колесников Максим',
                'Одинцова Ника', 'Елисеева Милана', 'Копылов Матвей', 'Новиков Вадим', 'Марков Марк', 'Антонова София',
                'Круглова Вероника', 'Козловский Даниил', 'Пугачев Евгений', 'Прокофьев Антон', 'Степанова Кристина',
                'Воробьева Есения', 'Самойлова Дарья', 'Макаров Демид', 'Власов Даниил', 'Филиппов Максим',
                'Матвеев Лев', 'Митрофанов Роман', 'Широков Тимофей', 'Овчинников Алексей', 'Мешкова Олеся',
                'Носова Ева', 'Софронова Виктория', 'Иванова Эмилия', 'Баранов Егор', 'Рыбакова Валерия', 'Белов Максим',
                'Рыбакова Таисия', 'Крылов Илья', 'Бочаров Фёдор', 'Васильева Анастасия', 'Герасимов Савелий',
                'Крылов Роман', 'Алексеева Сафия', 'Владимирова Таисия', 'Захаров Николай', 'Новиков Максим',
                'Морозов Александр', 'Коротков Даниил']
        for pers in list:
            pers = pers.split(' ')
            name = pers[1]
            second_name = pers[0]
            age = random.randint(15, 100)
            qry = f"""INSERT INTO public."user" ("name", second_name, age) values
                ( '{name}', '{second_name}', {age});"""
            with self.connection.cursor() as cursor:
                cursor.execute(qry)
                #result = cursor.fetchall()
        return 'OK'

    def insert_relations(self):
        # qry = f"""Select id from public."user" ;"""
        # with self.connection.cursor() as cursor:
        #     cursor.execute(qry)
        #     inserted = cursor.fetchall()
        # users_id = []
        # for ins in inserted:
        #     users_id.append(ins[0])
        #
        # #вставка друзей
        # for i in range(0, 40):
        #     first = random.choice(users_id)
        #     second = random.choice(users_id)
        #     while first == second:
        #         second = random.choice(users_id)
        #     qry = f"""INSERT INTO public.relation ("user 1", "user 2", type_relation) values
        #             ( {first}, {second}, 'friend'),
        #             ( {second}, {first}, 'friend');"""
        #     with self.connection.cursor() as cursor:
        #         cursor.execute(qry)
        qry = f"""INSERT INTO public.relation ("user 1", "user 2", type_relation) values 
                             ( 2, 39, 'friend'),
                             ( 39, 2, 'friend'),
                             ( 7, 2, 'friend'),
                             ( 2, 7, 'friend'),
                             ( 7, 10, 'friend'),
                             ( 10, 7, 'friend')
                                ;"""
        with self.connection.cursor() as cursor:
                 cursor.execute(qry)
        return 'users_id'

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
        qry_all_directories = f"""select * from directory d ;"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry_all_directories)
            all_directories = cursor.fetchall()

        description_list = []
        description_dict = {}
        problem_list = []

        if len(all_directories) == 0:
            problem_list.append("Каталогов в базе нет")
        for m in all_directories:
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

    def add_scheme(self, name):
        scheme_id = func_sql_insert.create_scheme(name, self.connection)
        return scheme_id

    def create_scheme(self, title, instances, flows):

        id_scheme = func_sql_insert.create_scheme(title, self.connection)

        for i in instances:
            ins = instances[i]
            model_id = ins["ModelId"]
            x = ins["x"]
            y = ins["y"]
            place_id = self.create_topography(x, y)
            instance_id = self.create_instance(model_id, id_scheme, place_id)
            ins["InstanceId"] = instance_id

        for f in flows:
            num = str(f["FromInstance"])
            cur_inst = instances[num]
            f["FromInstance"] = cur_inst["InstanceId"]
            # Перезаписали айди которое пришло с интерфейса на то которое создали
            num = str(f["ToInstance"])
            cur_inst = instances[num]
            f["ToInstance"] = cur_inst["InstanceId"]
            scheme_flows_id = self.insert_scheme_flow(f["FromInstance"], f["ToInstance"], id_scheme,
                                                      f["FromFlow"], f["ToFlow"])
        return id_scheme

    def create_topography(self, x, y):
        topog_id = func_sql_insert.create_topography(x, y, self.connection)
        return topog_id

    def create_instance(self, model, scheme, topography):
        instance_id = func_sql_insert.create_instance(model, scheme, topography, self.connection)
        return instance_id

    def insert_param_of_instnc(self, instance, pom, param_name):
        poi_id = func_sql_insert.insert_param_of_instnc(instance, pom, param_name, self.connection)
        return poi_id

    def insert_scheme_flow(self, from_instance, to_instance, scheme, from_flow, to_flow):
        poi_id = func_sql_insert.insert_scheme_flow(from_instance, to_instance, scheme, from_flow, to_flow, self.connection)
        return poi_id


if __name__ == '__main__':
    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="pni_v9"
    )

    name = input("Введите имя: ")
    id_scheme = db2.add_scheme(name)

    print(f"схема номер  {id_scheme} добавлена!")

    all_models = db2.get_models_info()[1]

    # print(all_models["Title"])
    print(f"выберите номер модели для создания ее экземпляра:  ")
    for mod in all_models:
        desc = all_models[mod]
        print(desc["ModelId"], desc["Title"])
    model_id = int(input("Модель: "))
    place_id = db2.create_topography(1, 1)
    instance_id = db2.create_instance(model_id, id_scheme, place_id)

    print(f"выберите номер второй модели для создания ее экземпляра:  ")
    for mod in all_models:
        desc = all_models[mod]
        print(desc["ModelId"], desc["Title"])
    model_id2 = int(input("Модель 2: "))
    place_id2 = db2.create_topography(1, 1)
    instance_id2 = db2.create_instance(model_id2, id_scheme, place_id2)

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

    scheme_flows_id = db2.insert_scheme_flow(instance_id, instance_id2, id_scheme, from_flow, to_flow)

    # all_calcs = db2.get_info_instance(model_id)
    #
    # for calc in all_calcs:
    #     neededvars = calc["NeededVariables"]
    #     for var in neededvars:
    #         pom = var['pom_id']
    #         param_name = var['name']
    #         poi = db2.insert_param_of_instnc(instance_id, pom, param_name)
