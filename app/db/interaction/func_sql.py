
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
        print(param_list)
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
        if flow_type=='input':
            qry = f"""select add_input_flow(
        {model}, '{cur_flow['FlowVariableIndex']}', {cur_flow['FlowEnviroment']});"""
        elif flow_type=='output':
            qry = f"""select add_output_flow({model}, '{cur_flow['FlowVariableIndex']}', {cur_flow['FlowEnviroment']});"""
        with con.cursor() as cursor:
            try:
                cursor.execute(qry)
            except Exception:
                print("не удалось выполнить запрос")
            id_flow = cursor.fetchall()[0][0]
            id_flows_model.append(id_flow)
    return id_flows_model



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

    def add_params_from_flow(self, mod_id, flow_id):
        problem_text = ""
        qry1 = f"""select  model, param_name, pg_id from param_of_flow where model={mod_id} and flow={flow_id};"""
        with self.connection.cursor() as cursor:
            cursor.execute(qry1)
            param_to_insert = cursor.fetchall()
            if param_to_insert == None:
                problem_text += ("\nВ потоке %s для модели %d не найдены параметры" % (flow_id, mod_id))
            else:
                pg_list = {}
                pom_inserted_list = []
                p_num = 0
                for param in param_to_insert:
                    p_num += 1
                    model = param[0]
                    param_name = param[1]
                    pg_id = param[2]
                    list_p_num = []
                    pg_list[p_num] = {"model": model, "param_name": param_name, "pg_id": pg_id}
                    ##теперь в pg_list список словарей - аналог таблицы pom_inserted
                    qry2 = f"""insert into param_of_model ( model_fk, param_name) values ({model},'{param_name}') RETURNING  *;"""
                    with self.connection.cursor() as cursor:
                        cursor.execute(qry2)
                        pom_inserted = cursor.fetchall()
                        if pom_inserted == None:
                            problem_text += ("\nВ модели %s не удалось вставить параметр %d" % (model, param_name))
                        else:

                            for pom in pom_inserted:
                                pom_id = pom[0]
                                model_id = param[1]
                                param_name = param[2]
                                pg_list[p_num]
                                pom_inserted_list.append({"pom_id": pom_id, "model_id": model_id, "param_name": param_name})
                                ##теперь в pom_inserted_list список словарей - аналог таблицы temp_pom_inserted
                print(pg_list,pom_inserted_list)

        if param_to_insert:
            return param_to_insert
        else:
            print('problem')

if __name__ == '__main__':

    db2 = DbConnection(
        host='localhost',
        user="postgres",
        password="root",
        database="PNI3_v7"
    )
    v = db2.add_params_from_flow(44, 111 )
