DROP VIEW IF EXISTS id_mapping;
CREATE OR REPLACE VIEW id_mapping AS
SELECT
  seq_resequencingexperiment.id AS reseq_id,
  ale_isolate.id AS isolate_id,
  ale_flask.id AS flask_id,
  ale_aleid.id AS ale_no,
  ale_aleexperiment.ale_id AS experiment_id
FROM seq_resequencingexperiment
JOIN ale_isolate
ON seq_resequencingexperiment.isolate_id = ale_isolate.id
JOIN ale_flask
ON ale_flask.id = ale_isolate.flask_id
JOIN ale_aleid
ON ale_aleid.id = ale_flask.ale_id_id
JOIN ale_aleexperiment
ON ale_aleexperiment.ale_id = ale_aleid.ale_experiment_id
ORDER BY reseq_id;
