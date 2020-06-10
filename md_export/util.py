from seq.util import get_ordered_reseq_queryset
from metadata.views import get_reseq_info_list
from common.constants import HTML_METADATA_TABLE_HEADER

def get_md_csv_str(experiment_id):

    data = get_reseq_info_list(get_ordered_reseq_queryset(experiment_id))
    processed = [HTML_METADATA_TABLE_HEADER]
    for x in data:
        processed.append((x[0].ale_flask_isolate_str,) + x[1:])
    return processed


if __name__ == '__main__':
    get_md_csv_str(47)


