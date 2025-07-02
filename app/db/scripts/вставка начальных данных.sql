INSERT INTO public.parametr (id, title,symbol,units,param_type) VALUES
	 (1, 'Давление','p','Па','base'),
	 (2, 'Температура','T','К','base'),
	 (3, 'Энтальпия','h','Дж/кг','base'),
	-- ('Давление на выходе','pOut','МПа','default'),
	-- ('Нагрев насоса','Ti1','Deg','custom'),
	 (4, 'Тепловая мощность','Q','Вт','base'),
	 (5, 'Энтропия','s','Дж/кг*К','base'),
	 (6, 'Расход','G','кг/c','base'),
	 (7, 'Значение 1','X','Ед','base');
SELECT setval('parametr_id_seq', max(id)) FROM parametr;

INSERT INTO public.environment (id, type_of_environment) VALUES
	 (1, 'вода'), --1
	 (2, 'влажный пар'), --2
	 (3, 'служебная'); --3
SELECT setval('environment_id_seq', max(id)) FROM environment;

INSERT INTO public.group_par (id, group_type) VALUES
	 (1, 'avail_for_env'), --1
	 (2, 'avail_for_env'), --2
	 (3, 'avail_for_env'); --3
SELECT setval('group_par_id_seq', max(id)) FROM group_par;

INSERT INTO public.environment_of_group (group_fk,environment_fk) VALUES
	 (1,1),--avail_for_env 1,вода
	 (2,2),--avail_for_env 2,влажный пар
	 (3,3);--avail_for_env 3,служебная

INSERT INTO public.param_of_group (param_fk,group_fk) VALUES
	 (1,1), --Давление, avail_for_env 1
	 (2,1), --Температура, avail_for_env 1
	 (3,1), --Энтальпия, avail_for_env 1
	 (5,1), --Полная мощность, avail_for_env 1
	 (6,1), --Некое обозначение, avail_for_env 1
	 (1,2), --Давление, avail_for_env 2
	 (3,2), --Энтальпия, avail_for_env 2
	 (4,2), --Тепловая мощность, avail_for_env 2
	 (7,3); --Значение 1, avail_for_env 3

INSERT INTO public.directory
	(id, dir_name, parent_level_fk)
	values
	(1,	'Сквозные однопоточные элементы', null),
	(2, 'Конденсаторы и котлы', 1),
	(3,	'Генераторы потоков', null),
	(4,	'Служебное', null);

SELECT setval('model_of_block_id_seq', max(id)) FROM model_of_block;
SELECT setval('version_id_seq', max(id)) FROM version;
SELECT setval('directory_model_id_seq', max(id)) FROM directory_model;
SELECT setval('version_id_seq', max(id)) FROM version;


INSERT INTO public."user"
(id, username, login, passw)
VALUES(nextval('user_id_seq'::regclass), 'первый пользователь', 'login', 'passw');


'''INSERT INTO public.directory_model
(id, model_fk, directory_fk)
values
(1, 1, 1),
(2, 2, 1),
(3, 4, 2),
(4, 3, 2),
(5, 5, 3);'''

