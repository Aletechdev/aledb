import os.path
import csv
import ast

__author__ = 'Patrick Phaneuf'


class Duplications:
    _CSV_GENE_LIST_INDEX = 7
    _CSV_START_POSITION_INDEX = 0
    _CSV_WIDTH_INDEX = 2
    _CSV_DEPTH_INDEX = 4
    _PROTEIN_CHANGE_ANNOTATION = "Duplication"
    _MUTATION_TYPE = "DUP"

    START_POSITION_KEY = "start_position"
    GENES_KEY = "genes"
    SEQUENCE_CHANGE_KEY = "sequence_change"
    PROTEIN_CHANGE_KEY = "protein_change"
    MUTATION_TYPE_KEY = "mutation_type"

    def __init__(self, breseq_output_dir_path):
        ale_flask_isolate_annotation = os.path.basename(os.path.dirname(os.path.dirname(breseq_output_dir_path)))
        breseq_output_path = os.path.dirname(os.path.dirname(os.path.dirname(breseq_output_dir_path)))
        self._dup_csv_file_path = breseq_output_path \
                   + "/dups/" \
                   + ale_flask_isolate_annotation \
                   + "/" \
                   + ale_flask_isolate_annotation \
                   + "_genes.csv"
        self._populate_dup_list()

    def _populate_dup_list(self):
        self.dup_list = []
        try:
            with open(self._dup_csv_file_path, 'rt') as csv_file:
                dup_list = list(csv.reader(csv_file, delimiter=','))
                if len(dup_list) > 1:  # There will always be a header in the file.
                    dup_list.pop(0)  # Removes header.
                    for dup in dup_list:
                        dup_dict = {}
                        dup_dict[self.START_POSITION_KEY] = dup[self._CSV_START_POSITION_INDEX]
                        dup_dict[self.GENES_KEY] = self._get_gene_list_str(dup[self._CSV_GENE_LIST_INDEX])
                        dup_dict[self.SEQUENCE_CHANGE_KEY] = (format(int(dup[self._CSV_WIDTH_INDEX]), ",d") + " bp x" + dup[self._CSV_DEPTH_INDEX])
                        dup_dict[self.PROTEIN_CHANGE_KEY] = self._PROTEIN_CHANGE_ANNOTATION
                        dup_dict[self.MUTATION_TYPE_KEY] = self._MUTATION_TYPE
                        self.dup_list.append(dup_dict)

        except IOError:
            print(IOError.strerror)
            return

    def _get_gene_list_str(self, gene_list_csv_str):
        gene_list = ast.literal_eval(gene_list_csv_str)
        gene_list_str = ', '.join(gene_list)
        return gene_list_str
