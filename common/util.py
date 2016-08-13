from common.constants import REQUEST_ALL
from common.constants import ALE_EXPERIMENT_SELECTOR_QUERY
from common.constants import ALE_NUMBER_SELECTOR_QUERY


def get_ale_experiment_selector(ale_experiment_id_str):
    # print(ale_experiment_id_str)
    if ale_experiment_id_str is None or ale_experiment_id_str == REQUEST_ALL:
        ale_experiment_selector = ""
    else:
        ale_experiment_selector = ALE_EXPERIMENT_SELECTOR_QUERY % int(ale_experiment_id_str)
    return ale_experiment_selector


def get_ale_number_selector(ale_id_str):
    if ale_id_str is None or ale_id_str == REQUEST_ALL:
        ale_no_selector = ""
    else:
        ale_no_selector = ALE_NUMBER_SELECTOR_QUERY % int(ale_id_str)
    return ale_no_selector
