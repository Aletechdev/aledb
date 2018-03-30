__author__ = "Patrick Phaneuf"

REQUEST_ALL = "all"
REQUEST_MUTATION_ID = "mutation_id"
REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"
REQUEST_ALE_ID = "ale_no"
POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE = 3
POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE = 3

TAGS = {
    "contaminated": '<i class="fa fa-random fa-fw" aria-hidden="true"></i>',
    "hypermutated": '<i class="fa fa-line-chart fa-fw" aria-hidden="true"></i>',
    "fixating":     '<i class="fa fa-signal fa-fw" aria-hidden="true"></i>',
}

COLUMN_TAGS = ["contaminated", "hypermutated"]

ROW_TAGS = ["contaminated", "hypermutated", "fixating"]
