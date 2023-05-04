from app.db.interaction import func_sql
from app.db.exceptions import ParametrNotFoundException, ModelProblems
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

            input_flows_list = []
            output_flows_list = []
            extra_params_list = []
            expressions_text = []
            default_params_list = []

            if input_flows is None:
                problem_text += ("\n Словарь %s из модели номер %d пуст" % ("input_flows", model_id))
            else:
                for i_f in input_flows:
                    qry = f"""select * from flow where id={i_f};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        flow_info = cursor.fetchall()[0]
                    if flow_info is None:
                        problem_text += (
                                "\nДанные для входного потока %s из модели номер %d не найдены" % (i_f, model_id))
                    else:
                        flow_id = flow_info[0]
                        flow_variable_index = flow_info[1]
                        qry = f"""select * from param_of_flow_in_model where model={model_id} and FlowId ={i_f};"""
                        with self.connection.cursor() as cursor:
                            cursor.execute(qry)
                            executed_all = cursor.fetchall()
                        avail_var = []
                        for executed in executed_all:
                            flow_variable_id = executed[1]
                            flow_id = executed[2]
                            flow_variable_name = executed[3]
                            variable_prototype = {'ParametrId': executed[4], 'Title': executed[5],
                                                  'Symbol': executed[6], 'Units': executed[7]}
                            avail_var.append({'FlowVariableId': flow_variable_id, 'FlowId': flow_id,
                                              'FlowVariableName': flow_variable_name,
                                              'VariablePrototype': variable_prototype})
                        dict_all = {'AvailableVariables': avail_var, 'FlowVariablesIndex': flow_variable_index,
                                    'Flow_id': flow_id}
                        input_flows_list.append(dict_all)

            if output_flows is None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("output_flows", model_id))
            else:
                for o_f in output_flows:
                    qry = f"""select * from flow where id={o_f};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        flow_info = cursor.fetchall()[0]
                    if flow_info is None:
                        problem_text += (
                                "\nДанные для входного потока %s из модели номер %d не найдены" % (o_f, model_id))
                    else:
                        # try:
                        flow_id = flow_info[0]
                        flow_variable_index = flow_info[1]
                        qry = f"""select * from param_of_flow_in_model where model={model_id} and FlowId ={o_f};"""
                        with self.connection.cursor() as cursor:
                            cursor.execute(qry)
                            executed_all = cursor.fetchall()
                        required_var = []
                        count_req = executed_all[0][9]
                        for executed in executed_all:
                            flow_variable_id = executed[1]
                            flow_id = executed[2]
                            flow_variable_name = executed[3]
                            variable_prototype = {'ParametrId': executed[4], 'Title': executed[5],
                                                  'Symbol': executed[6], 'Units': executed[7]}
                            required_var.append({'FlowVariableId': flow_variable_id, 'FlowId': flow_id,
                                                 'FlowVariableName': flow_variable_name,
                                                 'VariablePrototype': variable_prototype})
                        dict_all = {'RequiredVariables': required_var, 'FlowVariablesIndex': flow_variable_index,
                                    'FlowId': flow_id, 'CountOfMustBeDefinedVars': count_req}
                    output_flows_list.append(dict_all)

            if extra_params is None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("all_params", model_id))
            else:
                for p in extra_params:
                    qry = f"""select * from show_parameters_info where id={p};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        param_info = cursor.fetchall()[0]
                        if param_info is None:
                            problem_text += ("Данные для параметра %s из модели номер %d не найдены" % (p, model_id))
                        else:
                            try:
                                dict_all = {'ParametrId': param_info[0], 'VariableName': param_info[1],
                                            'Title': param_info[3], 'Units': param_info[4]}
                            except Exception:
                                raise ModelProblems(
                                    "Ошибка индекса для %s из модели номер %d " % (param_info, model_id))
                            else:
                                extra_params_list.append(dict_all)

            if default_params is None:
                problem_text += ("\nСловарь %s из модели номер %d пуст" % ("default_params_list", model_id))
            else:
                for d_p in default_params:
                    qry = f"""select * from show_parameters_info where id={d_p};"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry)
                        param_info = cursor.fetchall()[0]
                        if param_info is None:
                            problem_text += ("Данные для параметра %s из модели номер %d не найдены" % (d_p, model_id))
                        else:
                            try:
                                dict_all = {'ParametrId': param_info[0], 'VariableName': param_info[1],
                                            'Title': param_info[3], 'Units': param_info[4]}
                            except Exception:
                                raise ModelProblems(
                                    "Ошибка индекса для %s из модели номер %d " % (param_info, model_id))
                            else:
                                default_params_list.append(dict_all)

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
            if ((input_flows is None) or (output_flows is None) or (default_params_list is None)
                    or (extra_params_list is None) or (expressions_text is None)):
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
                     calculations,
                     model_id=None):

        # массив переменных модели, фигурирующих в ней от потоков
        id_flow_params_list = []
        # массив рассчетных выражений модели
        id_calcs_list = []

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

        id_calcs_list = func_sql.add_calc(id_model, calculations, self.connection)
        # for calculation in calculations:
        #     order_calc = calculation['Order']
        #     express_calc = calculation['Expression']
        #     defined_param = calculation['DefinedVariable']
        #     required_params_list = calculation['NeededVariables']
        #     qry = f"""select add_calculation ({id_model}, {order_calc}, '{express_calc}');"""
        #     with self.connection.cursor() as cursor:
        #         cursor.execute(qry)
        #         id_calc = cursor.fetchall()[0][0]
        #     id_calcs_list.append(id_calc)
        #     qry2 = f"""select defined_param_fk, required_params_fk from calculation c where id={id_calc};"""
        #     with self.connection.cursor() as cursor:
        #         cursor.execute(qry2)
        #         params = cursor.fetchall()[0]
        #     required_params_group = params[1]
        #     defined_params_group = params[0]
        #
        #     qry3 = f"""select insert_calc_param({id_model}, '{defined_param}', {id_calc}, {defined_params_group});"""
        #     with self.connection.cursor() as cursor:
        #         cursor.execute(qry3)
        #     for req in required_params_list:
        #         qry4 = f"""select insert_calc_param({id_model}, '{req}', {id_calc}, {required_params_group});"""
        #         with self.connection.cursor() as cursor:
        #             cursor.execute(qry4)

        # all_params_list = id_extra_params_list + id_default_params_list + id_flow_params_list
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
