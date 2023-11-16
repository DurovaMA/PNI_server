INSERT INTO public.parametr (id, title,symbol,units,param_type) VALUES
	 (1, 'Давление','p','Pa','base'),
	 (2, 'Температура','T','K','base'),
	 (3, 'Энтальпия','h','J','base'),
	-- ('Давление на выходе','pOut','МПа','default'),
	-- ('Нагрев насоса','Ti1','Deg','custom'),
	 (4, 'Тепловая мощность','Q','Вт','base'),
	 (5, 'Полная мощность','s','ВА','base'),
	 (6, 'Некое обозначение','G','Вт','base');
SELECT setval('parametr_id_seq', max(id)) FROM parametr;

INSERT INTO public.environment (id, type_of_environment) VALUES
	 (1, 'вода'), --1
	 (2, 'влажный пар');
SELECT setval('environment_id_seq', max(id)) FROM environment;

INSERT INTO public.group_par (id, group_type) VALUES
	 (1, 'avail_for_env'), --1
	 (2, 'avail_for_env'); --2
SELECT setval('group_par_id_seq', max(id)) FROM group_par;

INSERT INTO public.environment_of_group (group_fk,environment_fk) VALUES
	 (1,1),--avail_for_env 1,вода
	 (2,2);--avail_for_env 2,влажный пар

INSERT INTO public.param_of_group (param_fk,group_fk) VALUES
	 (1,1), --Давление, avail_for_env 1
	 (2,1), --Температура, avail_for_env 1
	 (3,1), --Энтальпия, avail_for_env 1
	 (5,1), --Полная мощность, avail_for_env 1
	 (6,1), --Некое обозначение, avail_for_env 1
	 (1,2), --Давление, avail_for_env 2
	 (3,2), --Энтальпия, avail_for_env 2
	 (4,2); --Тепловая мощность, avail_for_env 2
