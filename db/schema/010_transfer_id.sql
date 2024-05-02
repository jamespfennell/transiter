
ALTER TABLE transfer ADD id CHARACTER VARYING NOT NULL DEFAULT '';

UPDATE transfer SET id = CONCAT(
    REPLACE(from_stop.id, '_', '__'),
    '_to_',
    REPLACE(to_stop.id, '_', '__')
)
FROM stop from_stop, stop to_stop
WHERE from_stop.pk = transfer.from_stop_pk
AND to_stop.pk = transfer.to_stop_pk;


CREATE UNIQUE INDEX transfer_system_pk_id_key ON transfer (system_pk, id);
ALTER TABLE transfer ALTER COLUMN id DROP DEFAULT;

DELETE FROM transfer WHERE system_pk IS NULL;
ALTER TABLE transfer ALTER COLUMN system_pk SET NOT NULL;
