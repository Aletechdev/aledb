from os.path import join

from bs4 import BeautifulSoup
from enum import Enum

from seq.alchemy_orm import *
import gdparse


EXPERIMENT_PARENT_DIR = "breseq/"   # TODO: See if this is necessary.

BRESEQ_LOG_FILE = "log.txt"

Breseq_sample_type = Enum('Breseq_sample_type', 'clonal population')

BRESEQ_ANALYSIS_POPULATION_FLAG = " -p "


def add_breseq_results(session, isolate_id, person, breseq_folder, wt=False):

    """
    Figures out if the sample is clonal or population,
    and calls the appropriate "add" function.
    Read the output/log.txt file for " -p " option, which indicates that
    sample was processed as a population.
    """

    breseq_log_file_path = breseq_folder + BRESEQ_LOG_FILE

    sample_type = is_sample_clonal_or_popuation(breseq_log_file_path)

    if sample_type == Breseq_sample_type.clonal:

        add_breseq_clonal_results(session, isolate_id, person, breseq_folder, wt=False)

    elif sample_type == Breseq_sample_type.population:

        add_breseq_population_results(session, isolate_id, person, breseq_folder, wt=False)

    else:

        # TODO: implement error code returning/handling for this case.
        print('Error processing sample type. Sample not uploaded')


def is_sample_clonal_or_popuation(breseq_log_file_path):

    sample_type = Breseq_sample_type.clonal

    # If Breseq's log.txt file become very large, the following will be a memory hog.
    # For now, it's quite short.
    if BRESEQ_ANALYSIS_POPULATION_FLAG in open(breseq_log_file_path).read():
        return Breseq_sample_type.population

    return sample_type


# TODO: should split up the code getting the states and details into their own methods.
def add_breseq_clonal_results(session, isolate_id, person, breseq_folder, wt=False):

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

    # GETTING STATS ####################################################################################
    # TODO: put this into it's own function

    # parse the mutation html file to find the correct table
    mutation_table = html_file.find("th", attrs={"class": "mutation_header_row"}).parent.parent
    mutation_rows = mutation_table.findChildren("tr", attrs={"class": "normal_table_row"})
    row_read_info = summary_html.find("tr", attrs={"class": "highlight_table_row"}).findChildren("td")

    # create a resequencing experiment and populate the parameters from summary.html
    seq_experiment = query_or_create(session,
                                     ResequencingExperiment,
                                     location=breseq_folder[breseq_folder.find(EXPERIMENT_PARENT_DIR)
                                                            + len(EXPERIMENT_PARENT_DIR):],
                                     isolate_id=isolate_id,
                                     person=person)

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

    # PARSE GD FILES ####################################################################################
    # TODO: put this into it's own function

    # parse the output.gd file and retrieve a dictionary of the mutations:
    with open(join(breseq_folder, 'output.gd'), 'rb') as gdfile:
        gdparser = gdparse.GDParser(gdfile)
        evidence_dict = gdparser.data['evidence']
        mutation_dict = gdparser.data['mutation']

    # GETTING MUTATIONS ####################################################################################
    # TODO: put this into it's own function

    # add in the appropriate mutations from the index.html file
    for row_num, row in enumerate(mutation_rows):

        attrs = row.findChildren("td")
        mutation = query_or_create(session,
                                   Mutation,
                                   position=mutation_dict[row_num + 1]['position'],
                                   # mutations are in the same order in the html and output.gd files so we can index the ids with row_num
                                   sequence_change=attrs[2].text,
                                   mutation_type=mutation_dict[row_num + 1]['type'])
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

    process_unassigned_missing_coverage(session, seq_experiment, evidence_dict)


def is_missing_coverage_type(evidence_dict):

    is_missing_coverage = False

    if evidence_dict[gdparse.GDParser.EVIDENCE_TYPE_KEY]\
            == gdparse.GDParser.MISSING_COVERAGE_EVIDENCE_TYPE:
        is_missing_coverage = True

    return is_missing_coverage


# Should be able to re-use this with populations.
def process_unassigned_missing_coverage(db_session, seq_experiment, evidence_dict):

    for key in evidence_dict:

        if is_missing_coverage_type(evidence_dict[key]):

            # TODO: make literals into constants
            # Followed example given by ObservedMutations.
            # Seems like I have to use a mix of both Django and Alchemy ORM members.
            # Shouldn't have to do this.
            missing_coverage = UnassignedMissingCoverageEvidence()
            missing_coverage.seq_id = evidence_dict[key]['seq_id']
            missing_coverage.start = evidence_dict[key]['start']
            missing_coverage.end = evidence_dict[key]['end']
            missing_coverage.experiment = seq_experiment

            db_session.add(missing_coverage)


def add_breseq_population_results(session, isolate_id, person, breseq_folder, wt=False):
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
    seq_experiment = query_or_create(session,
                                     ResequencingExperiment,
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
        missing_coverage_data = gdparse.GDParser(gdfile).data['evidence']

    row_num = 0
    # add in the appropriate mutations from the index.html file
    for row_num, row in enumerate(mutation_rows):
        attrs = row.findChildren("td")
        mutation = query_or_create(session,
                                   Mutation,
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
