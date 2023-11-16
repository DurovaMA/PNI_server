DROP TABLE public.model_of_block CASCADE;
DROP TABLE public.parametr CASCADE;
DROP TABLE public.group_par CASCADE;
DROP TABLE public.param_of_group CASCADE;
DROP TABLE public.environment CASCADE;
DROP TABLE public.flow CASCADE;
DROP TABLE public.environment_of_group CASCADE;
DROP TABLE public.param_of_model CASCADE;
DROP TABLE public.calculation CASCADE;
DROP TABLE public.all_inclusions  CASCADE;
DROP TABLE public.instnc  CASCADE;
DROP TABLE public.scheme  CASCADE;
DROP TABLE public.scheme_flows  CASCADE;
DROP TABLE public.topography  CASCADE;

DROP TYPE public."types_group";
DROP TYPE public."types_flow";
DROP TYPE public."types_params";
DROP TYPE public."types_status";
DROP TYPE public."types_instance";
DROP TYPE public."types_expression";

--call inicialize_db();


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
	'flow',
	'base',
	'default',
	'extra');

CREATE TYPE public."types_status" AS ENUM (
	'Developing',
	'Completed');

CREATE TYPE public."types_instance" AS ENUM (
	'block',
	'multiple_block');

CREATE TYPE public."types_expression" AS ENUM (
	'Expression',
	'PropSI');

CREATE TABLE public.model_of_block (
    id serial NOT NULL,
    title character varying not NULL,
    description character varying NULL,
    status public."types_status" NULL DEFAULT 'Developing'::types_status,
    input_flows _int4 NULL,
    output_flows _int4 NULL,
    default_params _int4 NULL,
    extra_params _int4 NULL,
    expressions _int4 NULL,
    CONSTRAINT model_of_block_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.model_of_block IS 'Модель блока';

CREATE TABLE public.parametr (
	id serial4 NOT NULL,
	title varchar NULL,
	symbol varchar NOT NULL,
	units varchar NULL,
	param_type public."types_params" NOT NULL,
	model_fk int4 NULL,
	CONSTRAINT parametr_pk PRIMARY KEY (id),
	CONSTRAINT parametr_fk FOREIGN KEY (model_fk) REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.parametr IS 'Параметр';

CREATE TABLE public.group_par (
	id serial4 NOT NULL,
	group_type public."types_group" NOT NULL,
	model_fk int4 NULL,
	CONSTRAINT group_p PRIMARY KEY (id),
	CONSTRAINT group_par_fk FOREIGN KEY (model_fk) REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.group_par IS 'Группа параметров';


CREATE TABLE public.param_of_group (
	id serial NOT NULL,
	param_fk int4 NOT NULL,
	group_fk int4 NOT NULL,
	CONSTRAINT param_of_group_pk PRIMARY KEY (id),
	CONSTRAINT param_of_group_fk FOREIGN KEY (param_fk)
		REFERENCES public.parametr(id) ON DELETE CASCADE ON UPDATE cascade,
	CONSTRAINT param_of_group_fk_1 FOREIGN KEY (group_fk)
	REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.param_of_group IS 'Связь параметра и группы';

CREATE TABLE public.environment (
    id serial NOT NULL,
    type_of_environment character varying NOT NULL,
    CONSTRAINT environment_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.environment IS 'Среда';

CREATE TABLE public.environment_of_group (
    id serial NOT NULL,
    group_fk integer NOT NULL,
    environment_fk integer NOT NULL,
    CONSTRAINT environment_of_group_pk PRIMARY KEY (id),
    CONSTRAINT environment_of_group_fk FOREIGN KEY (group_fk)
    	REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT environment_of_group_fk_1 FOREIGN KEY (environment_fk)
    	REFERENCES public.environment(id) ON DELETE CASCADE ON UPDATE cascade
);
COMMENT ON TABLE public.environment_of_group IS 'Связь среды и группы параметров';

CREATE TABLE public.flow (
	id serial4 NOT NULL,
	param_index varchar NOT NULL,
	flow_type public."types_flow" NOT NULL,
	environment_fk int4 NOT NULL,
	count_params_out int4 NULL,
	model_fk int4 NULL,
	CONSTRAINT flow_pk PRIMARY KEY (id),
	CONSTRAINT flow_fk FOREIGN KEY (environment_fk) REFERENCES public.environment(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT flow_fk_1 FOREIGN KEY (model_fk) REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.flow IS 'Поток';

CREATE TABLE public.param_of_model (
    id serial NOT NULL,
    model_fk integer NOT NULL,
    param_fk integer NOT NULL,
    param_name character varying NOT NULL,
    param_type public.types_params not NULL,
    CONSTRAINT param_of_model_pk PRIMARY KEY (id),
    CONSTRAINT param_of_model_un UNIQUE (model_fk, param_name),
    CONSTRAINT param_of_model_fk FOREIGN KEY (model_fk)
    	REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT param_of_model_fk_1 FOREIGN KEY (param_fk)
    	REFERENCES public.parametr(id) ON DELETE CASCADE ON UPDATE cascade
);
COMMENT ON TABLE public.param_of_model IS 'Уникальная переменная модели блока';

CREATE TABLE public.all_inclusions (
	id serial4 NOT NULL,
	param_group_fk int4 NOT NULL,
	param_of_model_fk int4 NOT NULL,
	type_inclusion varchar NULL,
	CONSTRAINT all_inclusions_pk PRIMARY KEY (id),
	CONSTRAINT all_inclusions_fk FOREIGN KEY (param_group_fk) REFERENCES public.param_of_group(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT all_inclusions_fk_1 FOREIGN KEY (param_of_model_fk) REFERENCES public.param_of_model(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.all_inclusions IS 'Все вхождения переменной в модель';


CREATE TABLE public.calculation (
	id serial4 NOT NULL,
	order_calc int4 NOT NULL,
	expression_calc varchar NOT NULL,
	defined_param_fk int4 NULL,
	required_params_fk int4 NULL,
	model_fk int4 not NULL,
	type_calc public."types_expression" NOT NULL,
	CONSTRAINT calculation_pk PRIMARY KEY (id),
	CONSTRAINT calculation_fk FOREIGN KEY (defined_param_fk) REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT calculation_fk_1 FOREIGN KEY (required_params_fk) REFERENCES public.group_par(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT calculation_fk_2 FOREIGN KEY (model_fk) REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.calculation IS 'Расчетное выражение';

-- DROP TABLE public.topography;
CREATE TABLE public.topography (
    id serial NOT NULL,
    x real null,
    y real null,
    color real null,
    CONSTRAINT topography_pk PRIMARY KEY (id)
    );
COMMENT ON TABLE public.topography IS 'Топография экземпляра';

-- DROP TABLE public.scheme;
CREATE TABLE public.scheme (
    id serial NOT NULL,
    scheme_name varchar null,
    CONSTRAINT scheme_pk PRIMARY KEY (id)
    );
COMMENT ON TABLE public.scheme IS 'Схема с экземплярами блоков и связями';

-- DROP TABLE public.instnc;
CREATE TABLE public.instnc (
    id serial NOT NULL,
    model_fk int4 NOT NULL,
    topography_fk int4 NOT NULL,
    scheme_fk int4 NOT NULL,
    instance_type public.types_instance NOT null default 'block',
    CONSTRAINT instnc_pk PRIMARY KEY (id),
    CONSTRAINT instnc_fk FOREIGN KEY (model_fk)
    	REFERENCES public.model_of_block(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT instnc_fk_1 FOREIGN KEY (topography_fk)
    	REFERENCES public.topography(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT instnc_fk_2 FOREIGN KEY (scheme_fk)
    	REFERENCES public.scheme(id) ON DELETE CASCADE ON UPDATE cascade
    );
COMMENT ON TABLE public.instnc IS 'Экземпляр блока';

-- DROP TABLE public.param_of_instnc;
CREATE TABLE public.param_of_instnc (
	id serial4 NOT NULL,
	instance_fk int4 NOT NULL,
	pom_fk int4 NOT NULL,
	param_name varchar NOT NULL,
	value float4 NULL,
	CONSTRAINT param_of_instnc_pk PRIMARY KEY (id),
	CONSTRAINT param_of_instnc_fk FOREIGN KEY (instance_fk) REFERENCES public.instnc(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT param_of_instnc_fk_1 FOREIGN KEY (pom_fk) REFERENCES public.param_of_model(id) ON DELETE CASCADE ON UPDATE CASCADE
);
COMMENT ON TABLE public.param_of_instnc IS 'Значения параметров блока или потока';


-- DROP TABLE public.scheme_flows;
CREATE TABLE public.scheme_flows (
    id serial NOT NULL,
    from_instance_fk int4 NOT NULL,
    to_instance_fk int4 NOT NULL,
    scheme_fk int4 NOT NULL,
    from_flow_fk int4 NOT NULL,
    to_flow_fk int4 NOT NULL,
    CONSTRAINT scheme_flows_pk PRIMARY KEY (id),
    CONSTRAINT scheme_flows_fk FOREIGN KEY (from_instance_fk)
    	REFERENCES public.instnc(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT scheme_flows_fk_1 FOREIGN KEY (to_instance_fk)
    	REFERENCES public.instnc(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT scheme_flows_fk_2 FOREIGN KEY (scheme_fk)
    	REFERENCES public.scheme(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT scheme_flows_fk_3 FOREIGN KEY (from_flow_fk)
    	REFERENCES public.flow(id) ON DELETE CASCADE ON UPDATE cascade,
    CONSTRAINT scheme_flows_fk_4 FOREIGN KEY (to_flow_fk)
    	REFERENCES public.flow(id) ON DELETE CASCADE ON UPDATE cascade
    );
COMMENT ON TABLE public.scheme_flows IS 'Поток в схеме. Соединяет два экземпляра блока. Для первого указывается один из его выходных потоков, для второго - входной';

