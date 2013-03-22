from alchemy_orm import *

from BeautifulSoup import BeautifulSoup
from os.path import join


def add_breseq_results(session, isolate_id, person, breseq_folder, wt=False):
    """add breseq results to the database

    Parses the html output from a breseq run and adds those objects into
    the sqlalchemy session.
    
    session.commit() is not run in the function, and should be run afterwards
    
    Setting the wt flag allows any mutations that appear in the starting strain
    relative to the reference to be annotated as reference errors.
    """
    # html file displaying summary statistics
    
    with open(join(breseq_folder, "summary.html")) as infile:
        summary_html = BeautifulSoup(infile)

    # html file displaying the list fo mutations
    with open(join(breseq_folder, "index.html")) as infile:
        html_file = BeautifulSoup(infile)

    # parse the mutation html file to find the correct table
    mutation_table = html_file.find("th", attrs={"class": "mutation_header_row"}).parent.parent
    mutation_rows = mutation_table.findChildren("tr", attrs={"class": "normal_table_row"})
    row_read_info = summary_html.find("tr", attrs={"class": "highlight_table_row"}).findChildren("td")

    # create a resequencing experiment and populate the parameters from
    # summary.html
    seq_experiment = ResequencingExperiment()
    seq_experiment.location = breseq_folder[breseq_folder.find("sequencing/") + 11:]
    seq_experiment.isolate_id = isolate_id
    seq_experiment.person = person
    seq_experiment.reads = int(row_read_info[2].b.text.replace(",", ""))
    seq_experiment.average_read_length = row_read_info[5].text.split("&nbsp;")[0]
    seq_experiment.percentage_mapped = float(row_read_info[7].text.replace("%", ""))
    # average coverage is 3rd table, 2nd row (could also be more rows), 5th column
    seq_experiment.mean_coverage = summary_html.findChildren("table")[2].findChildren("tr")[1].findChildren("td")[4].text
    session.add(seq_experiment)

    # add in the appropriate mutations from the mutations html file
    for row in mutation_rows:
        attrs = row.findChildren("td")
        mutation = query_or_create(session, Mutation,
            position=int(attrs[1].text.replace(",", "")),
            sequence_change=attrs[2].text)
        if wt:
            mutation.reference_error = True
        if mutation.protein_change is None:
            change = attrs[3].renderContents()
            mutation.protein_change = change
        observed_mutation = ObservedMutation()
        observed_mutation.experiment = seq_experiment
        observed_mutation.mutation = mutation
        observed_mutation.evidence = attrs[0].renderContents()
        session.add(observed_mutation)

