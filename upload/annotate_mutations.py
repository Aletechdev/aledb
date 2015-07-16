from seq.alchemy_orm import *
import trnlib.omeORM as ome
session = Session()
ome_session = ome.Session()

base_ecocyc_link = """<a href="http://ecocyc.org/ECOLI/NEW-IMAGE?type=GENE&object=%s">%s</a>"""

for mutation in session.query(Mutation).filter_by(gene=None):
    position = mutation.position
    gene = ome_session.query(ome.Gene).filter(ome.Gene.leftpos <= position, ome.Gene.rightpos >= position).first()
    if gene is not None:
        mutation.gene = base_ecocyc_link % (gene.bnum, gene.name)
        session.add(mutation)
    else:
        # intergenic
        left_gene = ome_session.query(ome.Gene).filter(ome.Gene.rightpos < position).order_by(ome.Gene.rightpos.desc()).limit(1).first()
        right_gene = ome_session.query(ome.Gene).filter(ome.Gene.leftpos > position).order_by(ome.Gene.leftpos.asc()).limit(1).first()
        if left_gene is None:  # wrap around circular genome
            left_gene = ome_session.query(ome.Gene).order_by(ome.Gene.rightpos.desc()).limit(1).first()
        left_gene_str = base_ecocyc_link % (left_gene.bnum, left_gene.name)
        right_gene_str = base_ecocyc_link % (right_gene.bnum, right_gene.name)
        mutation.gene = """<span class="intergenic">%s/%s</i>""" % (left_gene_str, right_gene_str)
        session.add(mutation)

session.commit()
