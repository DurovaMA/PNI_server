----Отображение переменных доступных потоку
--drop FUNCTION public.return_avail_env(env integer);
CREATE OR REPLACE FUNCTION public.return_avail_env(env integer)
 RETURNS TABLE(par_id integer, par_title character varying, par_symbol character varying, 
 par_units character varying)
 LANGUAGE sql
AS $function$
select par.id, par.title, par.symbol , par.units 
from parametr par 
inner join parametr_group pg on pg.param_fk =par.id 
inner join group_par gop on gop.id =pg.group_fk 
inner join group_environment ge on ge.group_fk =gop.id 
inner join environment e on e.id =ge.enviroment_fk 
where gop.group_type ='avail_for_env' 
and e.id = $1;
$function$
;
COMMENT ON FUNCTION public.return_avail_env(int4) IS 
'Возвращает таблицу доступных параметров для среды по ее номеру';

----создание новой модели
CREATE OR REPLACE FUNCTION public.create_model
(tit character varying, descr character varying)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
declare
v_id bigint;
	begin
INSERT INTO public.model_of_block 
	(title, description, status ) 
	VALUES(tit,descr, 'Developing'::types_status) 
	RETURNING id into v_id;
return v_id;
	END;
$function$;
COMMENT ON FUNCTION public.create_model(varchar, varchar) IS 
'Создает пустую модель с названием и описанием. 
Возвращает номер модели в таблице create_model';
--select create_model('Насос', 'повышает давление');

----создание группы параметра 
CREATE OR REPLACE FUNCTION public.create_group
(type_group types_group , model_id int)
RETURNS integer
LANGUAGE plpgsql
AS $function$
declare
	gop_id bigint;
BEGIN
insert into group_par (group_type, model_fk) 
	values (type_group, model_id) 
	RETURNING id into gop_id; 
return gop_id;
END;
$function$;
COMMENT ON FUNCTION public.create_group(types_group,  int) IS 
'Создает новую группу параметра. Принимает номер модели и тип группы.
Возвращает номер группы';
--drop function public.create_group(types_group,  int);


----добавление дополнительного параметра или параметра по умолчанию
CREATE OR REPLACE FUNCTION public.add_extra_def_param
(model int, gop_id int,  p_type types_params, tit character varying, sym character varying, 
un character varying)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
declare
par_id bigint;
pg_id bigint;
par_m_id bigint;
par_all_in bigint;
	begin 
INSERT INTO public.parametr (title, symbol, units, param_type) 
	VALUES(tit, sym, un, p_type)
	RETURNING id into par_id;
INSERT INTO public.parametr_group (param_fk, group_fk) 
	VALUES(par_id, gop_id)
	RETURNING id into pg_id;
insert into public.param_of_model (model_fk, param_name) 
	VALUES(model, sym) ON CONFLICT (model_fk, param_name) 
	DO NOTHING;
par_m_id = (SELECT id FROM public.param_of_model WHERE model_fk=model and param_name=sym);
insert into public.all_inclusions (param_group_fk, param_of_model_fk) 
	VALUES(pg_id, par_m_id)
	RETURNING id into par_all_in;
return par_m_id;
	END;
$function$;
COMMENT ON FUNCTION public.add_extra_def_param
(int4, int4, types_params, varchar, varchar, varchar) 
IS 'Добавляет дополнительный параметр или параметр по умолчанию. 
Принимает номер модели, номер группы параметров, тип параметра и 
описание параметра. Возвращает номер добавленного параметра в таблице all_inclusions';


----добавление входного потока
CREATE OR REPLACE FUNCTION public.add_input_flow
(model int, ind character varying, env int)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
declare
flow_id bigint;
	begin 
INSERT INTO public.flow  (param_index, flow_type , enviroment_fk , model_fk) 
	VALUES(ind, 'input', env, model)
	RETURNING id into flow_id;
return flow_id;
	END;
$function$
;
COMMENT ON FUNCTION public.add_input_flow
(model int, ind character varying, env int)
IS 'Создает входной поток. Принимает номер модели, 
индекс для переменных и номер среды. 
Возвращает номер добавленного потока в таблице flow';


----Добавление выходного потока
CREATE OR REPLACE FUNCTION public.add_output_flow
(model int, ind character varying, env int)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
declare
flow_id bigint;
count_def int;
	begin 
count_def = 2;
INSERT INTO public.flow  
	(param_index, flow_type , enviroment_fk , 
	count_params_out,  model_fk) 
	VALUES(ind, 'output', env, count_def, model)
	RETURNING id into flow_id;
return flow_id;
	END;
$function$
;
COMMENT ON FUNCTION public.add_output_flow
(model int, ind character varying, env int)
IS 'Создает выходной поток. Принимает номер модели, 
индекс для переменных и номер среды. 
Возвращает номер добавленного потока в таблице flow';


----Представление для вывода всех переменных, доступных потоку, с названием
create view param_of_flow as 
select mob.id as model, flow.id as flow,
p.id as p_id, 
pg.id as pg_id,
p.symbol || flow.param_index  as param_name,
ge.group_fk as "группа" ,gop.group_type as "тип группы"
from model_of_block mob  
join flow on mob.id =flow.model_fk 
join environment e on e.id=flow.enviroment_fk 
join group_environment ge on ge.enviroment_fk =e.id
join group_par gop on gop.id =ge.group_fk
join parametr_group pg on pg.group_fk =gop.id 
join parametr p on p.id =pg.param_fk ;


----функция для вставки параметров модели, зависящих от потока
CREATE OR REPLACE FUNCTION public.add_params_from_flow
(mod_id integer, flow_id integer)
 RETURNS integer[]
 LANGUAGE plpgsql
AS $function$
declare id_list _int4;
	begin
CREATE  temp TABLE temp_inserted 
	(id serial4, model_fk int,
	param_name varchar, val float4, pg_id int);
CREATE temp TABLE temp_pom_inserted 
	(id serial4, model_fk int,
	param_name varchar, val float4);
insert into temp_inserted ( model_fk, param_name, pg_id) 
	select  model, param_name, pg_id
	from param_of_flow 
	where model=mod_id and flow=flow_id;

WITH pom_inserted AS (
	insert into param_of_model ( model_fk, param_name) 
	select  temp_inserted.model_fk, temp_inserted.param_name
	from temp_inserted
        	RETURNING  *
	)
	INSERT INTO temp_pom_inserted SELECT * FROM pom_inserted;

insert into all_inclusions  ( param_group_fk, param_of_model_fk) 
	select t_i.pg_id , t_p_i.id  
	from temp_inserted t_i join temp_pom_inserted t_p_i
	on t_i.param_name= t_p_i.param_name order by t_p_i.id;

id_list = (select array(SELECT id FROM temp_pom_inserted));
drop table temp_inserted;
drop  TABLE temp_pom_inserted;
return id_list;
	END;
$function$
;
COMMENT ON FUNCTION public.add_params_from_flow(int4, int4) 
IS 'Вставляет в таблицу параметров модели все переменные, 
которые есть в этой модели от среды. Принимает номер модели и номер потока. 
Возвращает список вставленных переменных';
--select add_params_from_flow (56, 144);


CREATE OR REPLACE FUNCTION public.insert_calc_param
(model int, p_name character varying, calc int, group_id int)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
declare
parametr_id bigint;
a_i_id bigint;
parametr_group_id int;
pom_id int;
	begin 
DROP TABLE IF EXISTS future_ai;
create temp table future_ai (par_id int, ai_id int) ON COMMIT drop ;
insert into future_ai select pg.param_fk, pom.id    
	from all_inclusions a_i 
	join parametr_group pg on a_i.param_group_fk=pg.id 
	join param_of_model pom on pom.id =a_i.param_of_model_fk 
	where pom.model_fk =model and param_name=p_name; 
parametr_id = (select par_id from  future_ai limit 1);
--a_i_id = 	(select ai_id from  future_ai);
pom_id = (select id from  param_of_model 
	where model_fk=model and param_name=p_name);
INSERT INTO public.parametr_group (param_fk, group_fk) 
	VALUES(parametr_id, group_id)
	RETURNING id into parametr_group_id;
insert into public.all_inclusions (param_group_fk, param_of_model_fk)
	values (parametr_group_id, pom_id);
--update public.all_inclusions set param_group_fk=parametr_group_id where id=a_i_id;
return parametr_group_id;
	END;
$function$
;
COMMENT ON FUNCTION public.insert_calc_param
(model int, p_name character varying, calc int, group_id int)
IS 'Создает связь между параметром расчета и группой, 
помечая его как требуемый для расчета или рассчитываемый';
--drop function insert_calc_param( int,  character varying ,  int,  int);

CREATE OR REPLACE FUNCTION public.add_calculation
(model_id integer, order_c integer, expres character varying)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
declare
calc_id integer;
group_required int;
group_defined int;
parametr_group_id int;
	begin 
insert into calculation (order_calc, expression_calc) 
	values (order_c, expres) returning id into calc_id;
group_required = (select create_group('required_for_calc', model_id)); 
group_defined = (select create_group('defined_from_calc', model_id));
update calculation set required_params_fk = group_required, 
	defined_param_fk = group_defined, model_fk =model_id 	
	where id=calc_id;
return calc_id;
	END;
$function$
;
COMMENT ON FUNCTION public.add_calculation
(model_id integer, order_c integer, expres character varying)
IS 'Создает запись о расчетном выражении. Создает для него 
группы требуемых и вычисляемых переменных. Возвращает номер выражения';


--представление для отображения данных о выражении: определяемая переменная
create view show_calc_defined as
select c.id c_id, c.order_calc, c.expression_calc, 
pom.param_name defined_param, pom.value  from 
calculation c 
join group_par gp on c.defined_param_fk=gp.id 
join parametr_group pg  on gp.id =pg.group_fk 
join all_inclusions ai on pg.id =ai.param_group_fk 
join param_of_model pom on pom.id =ai.param_of_model_fk ;
--------------------------------------------------------
--drop view show_calc_defined;
--select * from show_calc_defined; where c_id=11;


--представление для отображения данных о выражении: определяемая переменная
create view show_calc_required as
select c.id c_id, c.order_calc, c.expression_calc, 
pom.param_name required_param, pom.id pom_id, pom.value   from 
calculation c 
join group_par gp on c.required_params_fk=gp.id 
join parametr_group pg  on gp.id =pg.group_fk 
join all_inclusions ai on pg.id =ai.param_group_fk 
join param_of_model pom on pom.id =ai.param_of_model_fk ;
--------------------------------------------------------
--drop view show_calc_required;
--select * from show_calc_required where c_id=11;


--представление: данные о параметрах для вывода в json
create view show_parameters_info as
select  distinct pom.id, pom.param_name, pom.value, p.title , p.units
from param_of_model pom 
join all_inclusions ai on ai.param_of_model_fk =pom.id
join parametr_group pg on ai.param_group_fk=pg.id 
join group_par gp on gp.id =pg.group_fk 
join parametr p on p.id =pg.param_fk;
--------------------------------------------------------
--drop view show_parameters_info;
--select * from show_parameters_info where id=87;

--представление: параметры удаляемой модели, которые тоже надо удалить
create view param_to_delete as
select p.id p_id, gp.model_fk model from group_par gp 
join parametr_group pg on gp.id =pg.group_fk
join parametr p on p.id =pg.param_fk 
where param_type!='base';
--------------------------------------------------------
--drop view param_to_delete;
--------------------------------------------------------
/*drop view show_parameters_info;
delete from parametr where 
id in (select p_id from param_to_delete where 
	param_to_delete.model =33) returning *;*/


CREATE OR REPLACE VIEW public.param_of_flow_in_model
AS SELECT pom.model_fk AS model,
    pom.id AS flowvariableid,
    flow.id AS flowid,
    pom.param_name AS flowvariablename,
    p.id,
    p.title,
    p.symbol,
    p.units,
    p.param_type,
    flow.count_params_out AS count_of_def
   FROM param_of_model pom
     JOIN all_inclusions ai ON pom.id = ai.param_of_model_fk
     JOIN parametr_group pg ON pg.id = ai.param_group_fk
     JOIN group_environment ge ON ge.group_fk = pg.group_fk
     JOIN environment e ON e.id = ge.enviroment_fk
     JOIN flow ON flow.enviroment_fk = e.id
     JOIN parametr p ON p.id = pg.param_fk
  WHERE pom.param_name::text = (p.symbol::text || flow.param_index::text);