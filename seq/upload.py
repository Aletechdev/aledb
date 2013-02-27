from alchemy_orm import *

from BeautifulSoup import BeautifulSoup
from os.path import join



def add_breseq_results(session, isolate_id, person, breseq_folder):
    with open(join(breseq_folder, "summary.html")) as infile:
        summary_html = BeautifulSoup(infile)

    with open(join(breseq_folder, "index.html")) as infile:
        html_file = BeautifulSoup(infile)

    mutation_table = html_file.find("th", attrs={"class": "mutation_header_row"}).parent.parent
    mutation_rows = mutation_table.findChildren("tr", attrs={"class": "normal_table_row"})
    row_read_info = summary_html.find("tr", attrs={"class": "highlight_table_row"}).findChildren("td")

    seq_experiment = ResequencingExperiment()
    seq_experiment.isolate_id = isolate_id
    seq_experiment.person = person
    seq_experiment.reads = int(row_read_info[2].b.text.replace(",", ""))
    seq_experiment.average_read_length = row_read_info[5].text.split("&nbsp;")[0]
    session.add(seq_experiment)

    for row in mutation_rows:
        attrs = row.findChildren("td")
        mutation = query_or_create(session, Mutation,
            position=int(attrs[1].text.replace(",", "")),
            sequence_change=attrs[2].text)
        observed_mutation = ObservedMutation()
        observed_mutation.experiment = seq_experiment
        observed_mutation.mutation = mutation
        session.add(observed_mutation)

if __name__ == "__main__":
    session = Session()
    add_breseq_results(session, 132, "Gaby", "/home/aebrahim/ale_sequencing/9_y/")
    from IPython import embed; embed()
