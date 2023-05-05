from app.db.interaction import func_sql
from app.db.exceptions import ModelProblems
import psycopg2


class DbConnection:
    def __init__(self, host, user, password, database):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.connection.autocommit = True

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
            model_id = m[0]
            title = m[1]
            description = m[2]
            input_flows = m[4]
            output_flows = m[5]
            default_params = m[6]
            extra_params = m[7]
            expressions = m[8]

            expressions_text = []
            critical_flag = False

            input_flows_list, problem_flow, flag_flow = func_sql.show_flows \
                (model_id, "input", input_flows, self.connection)
            problem_text += problem_flow
            critical_flag += flag_flow
            output_flows_list, problem_flow, flag_flow = func_sql.show_flows \
                (model_id, "output", output_flows, self.connection)
            problem_text += problem_flow
            critical_flag += flag_flow

            extra_params_list, problem_params, flag_params = func_sql.show_extra_default_params \
                (model_id, "extra", extra_params, self.connection)
            problem_text += problem_params
            critical_flag += flag_params
            default_params_list, problem_params, flag_params = func_sql.show_extra_default_params \
                (model_id, "default", default_params, self.connection)
            problem_text += problem_params
            critical_flag += flag_params

            if expressions is None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("expressions", model_id))
            else:
                for e in expressions:
                    qry = f"""select * from calculation where id={e};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        e_info = cursor.fetchall()[0]
                        if e_info is None:
                            problem_text += ("\nДанные для расчетного выражения %s из модели номер %d не найдены" % (
                                e, model_id))
                        else:
                            try:
                                dict_all = {'ExpressionId': e_info[0], 'Order': e_info[1], 'Expression': e_info[2],
                                            'DefinedVariableId': e_info[3], 'NeededVariables': e_info[4]}
                            except Exception:
                                raise ModelProblems("Ошибка индекса для %s из модели номер %d " % (e_info, model_id))
                            else:
                                expressions_text.append(dict_all)
            # if ((len(input_flows_list) < 1) or (len(output_flows_list) < 1) or (default_params_list is None)
            #         or (extra_params_list is None) or (expressions_text is None)):
            if (critical_flag > 0) or ((len(input_flows_list) < 1) and (len(output_flows_list) < 1)):
                problem_text += ("\nМодель номер %d не будет отображена\n" % model_id)
            else:
                model_desc = {'ModelId': model_id, 'Title': title, 'Description': description,
                              'InputFlows': input_flows_list, 'OutputFlows': output_flows_list,
                              'DefaultParameters': default_params_list, 'CustomParameters': extra_params_list,
                              'Expressions': expressions_text}
                description_list.append(model_desc)

            problem_list.append(problem_text)

        print('\n'.join(map(str, problem_list)))
        return description_list

    def create_model(self, model_description, model_title, in_flows, out_flows, default_params, extra_params,
                     calculations):

        # массив переменных модели, фигурирующих в ней от потоков
        id_flow_params_list = []

        # создание записи в таблице model_of_block
        id_model = func_sql.create_new_model(model_title, model_description, self.connection)

        # создание группы дополнительных параметров в таблице group_par и записей о ней в таблицах parametr,
        # parametr_group, param_of_model и all_inclusions.
        # Возвращает идентификатор группы из таблицы group_par и массив идентификаторов в таблице param_of_model
        id_group_extr, id_extra_params_list = func_sql.add_extra_def_params('extra_params', 'extra', id_model,
                                                                            extra_params, self.connection)
        # Аналогично для параметров по умолчанию
        id_group_def, id_default_params_list = func_sql.add_extra_def_params('default_params', 'default', id_model,
                                                                             default_params, self.connection)

        # Создает записи о входных и выходных потоках, возвращает массивы идентификаторов из таблицы flow
        id_flows_model_input = func_sql.add_flow(id_model, 'input', in_flows, self.connection)
        id_flows_model_output = func_sql.add_flow(id_model, 'output', out_flows, self.connection)

        # Объединяет массивы входных и выходных потоков
        flows_model = id_flows_model_input + id_flows_model_output

        for flow in flows_model:
            id_flow_params = func_sql.add_params_from_flow(id_model, flow, self.connection)
            id_flow_params_list = id_flow_params_list + id_flow_params

        # массив рассчетных выражений модели
        id_calcs_list = func_sql.add_calc(id_model, calculations, self.connection)

        qry = f"""update model_of_block set input_flows=array{id_flows_model_input},
        output_flows=array{id_flows_model_output}, default_params =array{id_default_params_list},
        extra_params =array{id_extra_params_list},  expressions =array{id_calcs_list}
        where id = {id_model};"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry)

        if id_extra_params_list and id_default_params_list and id_flow_params_list:
            print('Добавлена модель номер ', id_model)
            return id_model
        else:
            raise ModelProblems('Не удалось добавить модель!')


if __name__ == '__main__':
    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="PNI3_v7"
    )

    print(db2.get_models_info())
    # print(db2.create_model())
    # db.create_table_users()
    # db.add_param_info(2222, 'test', 'test', 'test', 'base')
    # db.add_user_info('test', 'test', 'base')
    # db.get_parametr_info(2222)
