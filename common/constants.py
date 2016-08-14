__author__ = "Patrick Phaneuf"

RESEQ_QUERY = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;"""
REQUEST_ALL = "all"
ALE_EXPERIMENT_SELECTOR_QUERY = "AND experiment_id = %d"
ALE_NUMBER_SELECTOR_QUERY = "AND ale_no = %d"
REQUEST_MUTATION_ID = "mutation_id"
REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"
REQUEST_ALE_ID = "ale_no"