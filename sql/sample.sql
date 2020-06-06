DROP TABLE IF EXISTS public.sample_table;
CREATE TABLE public.sample_table (
	col1 varchar(256),
	col2 varchar(256)
);

DROP TABLE IF EXISTS public.users;
CREATE TABLE public.users (
	user_id int4 NOT NULL,
	first_name varchar(256),
	last_name varchar(256),
	CONSTRAINT users_pkey PRIMARY KEY (user_id)
);
