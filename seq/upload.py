from alchemy_orm import *

from bs4 import BeautifulSoup
from os.path import join
import gdparse

EXPERIMENT_PARENT_DIR = "breseq/"


def add_breseq_results(session, isolate_id, person, breseq_folder, wt=False):

    """add breseq results to the database

    Parses the html output from a breseq run and adds those objects into
    the sqlalchemy session.

    The "breseq_folder" parameter is looking for the contents of the "/output" dir
    from a breseq execution.
    
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
    seq_experiment = query_or_create(session, ResequencingExperiment,
                                     location=breseq_folder[breseq_folder.find(EXPERIMENT_PARENT_DIR)
                                                            + len(EXPERIMENT_PARENT_DIR):],
                                     isolate_id=isolate_id,
                                     person=person)
    # seq_experiment = ResequencingExperiment()
    # seq_experiment.location = breseq_folder[breseq_folder.find("sequencing/") + 11:]
    # seq_experiment.isolate_id = isolate_id
    # seq_experiment.person = person
    # if any mutations were read in, we need to overwrite them
    seq_experiment.mutations = []
    seq_experiment.reads = int(row_read_info[2].b.text.replace(",", ""))
    seq_experiment.average_read_length = row_read_info[5].text.split("&nbsp;")[0]
    try:
        seq_experiment.percentage_mapped = float(row_read_info[7].text.replace("%", ""))
    except:
        None
    # average coverage is 3rd table, 2nd row (could also be more rows), 5th column
    mean_coverage = summary_html.findChildren("table")[2].findChildren("tr")[1].findChildren("td")[4].text
    try:
        mean_coverage = float(mean_coverage)
    except:
        mean_coverage = 0
    seq_experiment.mean_coverage = mean_coverage
    session.add(seq_experiment)

    # parse the output.gd file and retrieve a dictionary of the mutations:
    with open(join(breseq_folder, 'output.gd'), 'rb') as gdfile:
        mutation_data = gdparse.GDParser(gdfile).data['mutation']

    # add in the appropriate mutations from the index.html file
    for row_num, row in enumerate(mutation_rows):
        attrs = row.findChildren("td")
        mutation = query_or_create(session, Mutation,
                                   position=mutation_data[row_num + 1]['position'],
                                   # mutations are in the same order in the html and output.gd files so we can index the ids with row_num
                                   sequence_change=attrs[2].text,
                                   mutation_type=mutation_data[row_num + 1]['type'])
        if wt:
            mutation.reference_error = True
        if mutation.protein_change is None:
            change = attrs[3].renderContents()
            mutation.protein_change = change
        observed_mutation = ObservedMutation()
        observed_mutation.experiment = seq_experiment
        observed_mutation.mutation = mutation
        observed_mutation.breseq_present = True
        observed_mutation.evidence = attrs[0].renderContents()
        session.add(observed_mutation)


def add_pop_results(session, isolate_id, person, breseq_folder, wt=False):
    """add population sequencing results to the database

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
    # mutation_rows = mutation_table.findChildren("tr", attrs={"class": "polymorphism_table_row"})
    mutation_rows = mutation_table.findChildren("tr", attrs={"class": ["normal_table_row", "polymorphism_table_row"]})
    row_read_info = summary_html.find("tr", attrs={"class": "highlight_table_row"}).findChildren("td")

    # create a resequencing experiment and populate the parameters from
    # summary.html
    seq_experiment = query_or_create(session, ResequencingExperiment,
                                     location=breseq_folder[breseq_folder.find(EXPERIMENT_PARENT_DIR)
                                                            + len(EXPERIMENT_PARENT_DIR):],
                                     isolate_id=isolate_id,
                                     person=person)
    # seq_experiment = ResequencingExperiment()
    # seq_experiment.location = breseq_folder[breseq_folder.find("sequencing/") + 11:]
    # seq_experiment.isolate_id = isolate_id
    # seq_experiment.person = person
    # if any mutations were read in, we need to overwrite them
    seq_experiment.mutations = []
    seq_experiment.reads = int(row_read_info[2].b.text.replace(",", ""))
    seq_experiment.average_read_length = row_read_info[5].text.split("&nbsp;")[0]
    try:
        seq_experiment.percentage_mapped = float(row_read_info[7].text.replace("%", ""))
    except:
        None
    # average coverage is 3rd table, 2nd row (could also be more rows), 5th column
    mean_coverage = summary_html.findChildren("table")[2].findChildren("tr")[1].findChildren("td")[4].text
    try:
        mean_coverage = float(mean_coverage)
    except:
        mean_coverage = 0
    seq_experiment.mean_coverage = mean_coverage
    session.add(seq_experiment)

    # parse the output.gd file and retrieve a dictionary of the mutations:
    with open(join(breseq_folder, 'output.gd'), 'rb') as gdfile:
        mutation_data = gdparse.GDParser(gdfile).data['mutation']

    row_num = 0
    # add in the appropriate mutations from the index.html file
    for row_num, row in enumerate(mutation_rows):
        attrs = row.findChildren("td")
        mutation = query_or_create(session, Mutation,
                                   position=mutation_data[row_num + 1]['position'],
                                   # mutations are in the same order in the html and output.gd files so we can index the ids with row_num,
                                   sequence_change=attrs[2].text,
                                   mutation_type=mutation_data[row_num + 1]['type'])
        if wt:
            mutation.reference_error = True
        if mutation.protein_change is None:
            change = attrs[4].renderContents()
            mutation.protein_change = change
        observed_mutation = ObservedMutation()
        observed_mutation.experiment = seq_experiment
        observed_mutation.mutation = mutation
        observed_mutation.breseq_present = True
        observed_mutation.evidence = attrs[0].renderContents()
        observed_mutation.frequency = attrs[3].text
        session.add(observed_mutation)
