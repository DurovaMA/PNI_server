----Представление для вывода всех переменных, доступных потоку, с названием
create view param_of_flow as
select mob.id as model, flow.flow_type,
p.id as p_id, pog.id as pog_id,flow.id flow,
p.symbol || flow.param_index  as param_name,
eog.group_fk as "группа" ,gp.group_type as "тип группы"
from model_of_block mob
join flow on mob.id =flow.model_fk
join environment e on flow.environment_fk =e.id
join environment_of_group eog on eog.environment_fk =e.id
join group_par gp on eog.group_fk =gp.id
join param_of_group pog on pog.group_fk =gp.id
join parametr p on pog.param_fk =p.id ;
--drop view param_of_flow;

--представление для отображения данных о выражении: определяемая переменная
create view show_calc_defined as
select gp.model_fk model, pom.id , c.id c_id, c.order_calc , c.expression_calc ,  pom.param_name, pom.param_type, p.id p_id, c.type_calc
from group_par gp  join calculation c on gp.id =c.defined_param_fk
join param_of_group pog on pog.group_fk =gp.id
join all_inclusions ai on ai.param_group_fk =pog.id
join param_of_model pom  on ai.param_of_model_fk  =pom.id
join parametr p on pom.param_fk =p.id ;
--drop view show_calc_defined;

--представление для отображения данных о выражении: требуемые переменные
create view show_calc_required as
select gp.model_fk model, pom.id , c.id c_id, c.order_calc , c.expression_calc ,  pom.param_name, pom.param_type, p.id p_id, c.type_calc
from group_par gp  join calculation c on gp.id =c.required_params_fk
join param_of_group pog on pog.group_fk =gp.id
join all_inclusions ai on ai.param_group_fk =pog.id
join param_of_model pom  on ai.param_of_model_fk  =pom.id
join parametr p on pom.param_fk =p.id ;
--drop view show_calc_required;

--представление для отображения данных о потоке:  переменные
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
    flow.count_params_out AS count_of_def,
    e.id as env_id
   FROM param_of_model pom
     JOIN all_inclusions ai ON pom.id = ai.param_of_model_fk
     JOIN param_of_group pog ON pog.id = ai.param_group_fk
     JOIN environment_of_group eog ON eog.group_fk = pog.group_fk
     JOIN environment e ON e.id = eog.environment_fk
     JOIN flow ON flow.environment_fk = e.id
     JOIN parametr p ON p.id = pog.param_fk
  WHERE pom.param_name::text = (p.symbol::text || flow.param_index::text);
  --drop view param_of_flow_in_model;

 --представление: данные о параметрах для вывода в json
create view show_parameters_info as
select  distinct pom.id, pom.param_name, p.title , p.units
from param_of_model pom
join all_inclusions ai on ai.param_of_model_fk =pom.id
join param_of_group pog on ai.param_group_fk=pog.id
join group_par gp on gp.id =pog.group_fk
join parametr p on p.id =pog.param_fk;
--------------------------------------------------------
--drop view show_parameters_info;

--drop FUNCTION public.return_avail_env(env integer);
CREATE OR REPLACE FUNCTION public.return_avail_env(env integer)
 RETURNS TABLE(par_id integer, par_title character varying, par_symbol character varying,
 par_units character varying)
 LANGUAGE sql
AS $function$
select par.id, par.title, par.symbol , par.units
from parametr par
inner join param_of_group pog on pog.param_fk =par.id
inner join group_par gop on gop.id =pog.group_fk
inner join environment_of_group eog on eog.group_fk =gop.id
inner join environment e on e.id =eog.environment_fk
where gop.group_type ='avail_for_env'
and e.id = $1;
$function$
;
COMMENT ON FUNCTION public.return_avail_env(int4) IS
'Возвращает таблицу доступных параметров для среды по ее номеру';

