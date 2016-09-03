INTERGENIC_SPLIT_CHAR = '/'
INTRAGENIC_RIGHT_CHAR = '['
INTRAGENIC_LEFT_CHAR = ']'

# TODO: unit testable
# TODO: add populating of gene list from a range here. Likely will have to add argument for ref file path.
def get_gene_list(mutation_gene_str):
    if INTERGENIC_SPLIT_CHAR in mutation_gene_str:
        gene_list = mutation_gene_str.split(INTERGENIC_SPLIT_CHAR)
    else:
        gene_list = [mutation_gene_str]

    _clean_gene_list(gene_list)

    return gene_list


def _clean_gene_list(gene_list):
    for gene_idx in range(len(gene_list)):
        if INTRAGENIC_LEFT_CHAR in gene_list[gene_idx]:
            gene_list[gene_idx] = gene_list[gene_idx].replace(INTRAGENIC_LEFT_CHAR, '')
        if INTRAGENIC_RIGHT_CHAR in gene_list[gene_idx]:
            gene_list[gene_idx] = gene_list[gene_idx].replace(INTRAGENIC_RIGHT_CHAR, '')