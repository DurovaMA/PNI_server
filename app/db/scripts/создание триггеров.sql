drop TRIGGER if exists clean_parametres ON model_of_block;
drop FUNCTION if exists clean_parametres();

CREATE OR REPLACE FUNCTION clean_parametres() RETURNS trigger AS $emp_stamp$
    BEGIN
        delete from parametr where
        	id in (select p_id from param_to_delete where
	param_to_delete.model =old.id);

        RETURN OLD;
    END;
$emp_stamp$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER clean_parametres BEFORE delete ON model_of_block
    FOR EACH ROW EXECUTE PROCEDURE clean_parametres();