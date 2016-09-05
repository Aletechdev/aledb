CODING_SEQUENCE_FLAG = "cds "
GENE_NAME_FLAG = '/gene'


# TODO: Ignore "gene" block
def get_ordered_gene_list(ref_file_path):
    ordered_gene_list = []
    is_coding_sequence_block = False

    with open(ref_file_path) as ref_file:

        for line in ref_file:
            line = line.strip()

            if line.lower().startswith(CODING_SEQUENCE_FLAG):
                is_coding_sequence_block = True
            elif is_coding_sequence_block and line.lower().startswith(GENE_NAME_FLAG):
                gene_name = _find_between(line, '"', '"')
                ordered_gene_list.append(gene_name)
                is_coding_sequence_block = False

    return ordered_gene_list


def _find_between(s, first, last):

    """
    :param s: inputted string
    :param first: start sequence string
    :param last: end sequence string
    :return: finds string in s between start and end string
    """
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""