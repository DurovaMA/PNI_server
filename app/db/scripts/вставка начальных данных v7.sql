INSERT INTO public.parametr (title,symbol,units,param_type) VALUES
	 ('Давление','p','Pa','base'),
	 ('Температура','T','K','base'),
	 ('Энтальпия','h','J','base'),
	-- ('Давление на выходе','pOut','МПа','default'),
	-- ('Нагрев насоса','Ti1','Deg','custom'),
	 ('Тепловая мощность','Q','Вт','base');
	
INSERT INTO public.environment (type_of_environment) VALUES
	 ('стандартная'), --1
	 ('влажный пар'); --2
	 
INSERT INTO public.group_par (group_type) VALUES
	 ('avail_for_env'), --1
	 ('avail_for_env'); --2
	

INSERT INTO public.group_environment (group_fk,enviroment_fk) VALUES
	 (1,1),--avail_for_env 1,стандартная
	 (2,2);--avail_for_env 2,влажный пар
	
INSERT INTO public.parametr_group (param_fk,group_fk) VALUES
	 (1,1), --Давление, avail_for_env 1
	 (2,1), --Температура, avail_for_env 1 
	 (3,1), --Энтальпия, avail_for_env 1
	 (1,2), --Давление, avail_for_env 2
	 (3,2), --Энтальпия, avail_for_env 2
	 (4,2); --Тепловая мощность, avail_for_env 2

