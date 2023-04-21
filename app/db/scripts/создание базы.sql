DROP TABLE public.model_of_block CASCADE;
DROP TABLE public.parametr CASCADE;
DROP TABLE public.group_par CASCADE;
DROP TABLE public.parametr_group CASCADE;
DROP TABLE public.environment CASCADE;
DROP TABLE public.flow CASCADE;
DROP TABLE public.group_environment CASCADE;
DROP TABLE public.param_of_model CASCADE;
DROP TABLE public.calculation CASCADE;
DROP TABLE public.all_inclusions  CASCADE;

DROP TYPE public."types_group";
DROP TYPE public."types_flow";
DROP TYPE public."types_params";
DROP TYPE public."types_status";

CREATE TYPE public."types_group" AS ENUM (
	'avail_for_env',
	'required_for_output',
	'default_params',
	'extra_params',
	'required_for_calc',
	'defined_from_calc'
	);

CREATE TYPE public."types_flow" AS ENUM (
	'input',
	'output');

CREATE TYPE public."types_params" AS ENUM (
	'base',
	'default',
	'extra');

CREATE TYPE public."types_status" AS ENUM (
	'Developing',
	'Completed');

CREATE TABLE public.model_of_block (
    id serial NOT NULL,
    title character varying not NULL,
    description character varying NULL,
    status public."types_status" NULL DEFAULT 'Developing'::types_status,
    input_flows _int4 NULL,
    output_flows _int4 NULL,
    default_params _int4 NULL,
    all_params _int4 NULL,
    expressions _int4 NULL,
    CONSTRAINT model_of_block_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.model_of_block IS 'Модель блока';

CREATE TABLE public.parametr (
	id serial NOT NULL,
	title varchar NULL,
	symbol varchar NOT NULL,
	units varchar NULL,
	param_type public."types_params" NOT NULL,
	CONSTRAINT parametr_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.parametr IS 'Параметр';

CREATE TABLE public.group_par (
	id serial4 NOT NULL,
	group_type public.types_group NOT NULL,
	model_fk int4 NULL,
	CONSTRAINT group_p PRIMARY KEY (id),
	CONSTRAINT group_par_fk FOREIGN KEY (model_fk) REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.group_par IS 'Группа параметров';

CREATE TABLE public.parametr_group (
	id serial NOT NULL,
	param_fk int4 NOT NULL,
	group_fk int4 NOT NULL,
	CONSTRAINT parametr_group_pk PRIMARY KEY (id),
	CONSTRAINT parametr_group_fk FOREIGN KEY (param_fk) 
		REFERENCES public.parametr(id) ON DELETE CASCADE ON UPDATE cascade,
	CONSTRAINT parametr_group_fk_1 FOREIGN KEY (group_fk) 
	REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.parametr_group IS 'Связь параметра и группы';

CREATE TABLE public.environment (
    id serial NOT NULL,
    type_of_environment character varying NOT NULL,
    CONSTRAINT environment_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.environment IS 'Среда';

CREATE TABLE public.group_environment (
    id serial NOT NULL,
    group_fk integer NOT NULL,
    enviroment_fk integer NOT NULL,    
    CONSTRAINT group_environment_pk PRIMARY KEY (id),
    CONSTRAINT group_environment_fk FOREIGN KEY (group_fk) 
    	REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT group_environment_fk_1 FOREIGN KEY (enviroment_fk) 
    	REFERENCES public.environment(id) ON DELETE CASCADE ON UPDATE cascade	
);
COMMENT ON TABLE public.group_environment IS 'Связь среды и группы параметров';

CREATE TABLE public.flow (
    id serial NOT NULL,
    param_index character varying NOT NULL,
    flow_type public.types_flow NOT NULL,
    enviroment_fk integer NOT NULL,
    count_params_out integer,
    model_fk int4 NULL,
    CONSTRAINT flow_pk PRIMARY KEY (id),
    CONSTRAINT flow_fk FOREIGN KEY (enviroment_fk) 
    	REFERENCES public.environment(id) ON DELETE CASCADE ON UPDATE cascade,	
    CONSTRAINT flow_fk_1 FOREIGN KEY (model_fk) 
    	REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.flow IS 'Поток';

CREATE TABLE public.param_of_model (
    id serial NOT NULL,
    model_fk integer NOT NULL,  
    param_name character varying NOT NULL,
    value real NULL,  
    CONSTRAINT param_of_model_pk PRIMARY KEY (id),
    CONSTRAINT param_of_model_un UNIQUE (model_fk, param_name),
    CONSTRAINT param_of_model_fk FOREIGN KEY (model_fk) 
    	REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE cascade
);
COMMENT ON TABLE public.param_of_model IS 'Уникальная переменная модели блока';

CREATE TABLE public.all_inclusions (
    id serial NOT NULL,
    param_group_fk integer NOT NULL,
    param_of_model_fk integer NOT NULL,
    CONSTRAINT all_inclusions_pk PRIMARY KEY (id),
    CONSTRAINT all_inclusions_fk FOREIGN KEY (param_group_fk) 
    	REFERENCES public.parametr_group(id) ON DELETE CASCADE ON UPDATE cascade,    	
    CONSTRAINT all_inclusions_fk_1 FOREIGN KEY (param_of_model_fk) 
    	REFERENCES public.param_of_model(id) ON DELETE CASCADE ON UPDATE cascade
);
COMMENT ON TABLE public.all_inclusions IS 'Все вхождения переменной в модель';


CREATE TABLE public.calculation (
    id serial NOT NULL,
    order_calc integer NOT NULL,
    expression_calc character varying NOT NULL,    
    defined_param_fk integer  NULL,    
    required_params_fk integer  NULL,
    model_fk int4 NULL,    	
    CONSTRAINT calculation_pk PRIMARY KEY (id),
    CONSTRAINT calculation_fk FOREIGN KEY (defined_param_fk) 
    	REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT calculation_fk_1 FOREIGN KEY (required_params_fk) 
    	REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT calculation_fk_2 FOREIGN KEY (model_fk) 
    	REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE cascade    
    );  
COMMENT ON TABLE public.calculation IS 'Расчетное выражение';

