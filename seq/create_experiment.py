import alchemy_orm
import upload
import validatemutations  # TODO: find out what validatemutations does for mutations.
import datetime
import os

WILD_TYPE_ALE_NUMBER = 0
WILD_TYPE_FLASK_NUMBER = 0
WILD_TYPE_ISOLATE_NUMBER = 0
WILD_TYPE_PERSON_NAME = "BOP27"

BRESEQ_OUTPUT_REPORT_DIR = "output/"
BRESEQ_OUTPUT_REPORT_FILE = "index.html"

# TODO: this should be an input from a user UI.
BRESEQ_ISOLATE_OUTPUT_PATH = "/data/breseq/BOP27_reseq_v3/clonal/output/"

# TODO: this should be an input from a user UI.
# !!! ENSURE THAT THE TRAILING '/' IS ALWAYS INCLUDED!!!
BRESEQ_EXPERIMENT_OUTPUT_PATH = "/data/breseq/ssw/combo/"

# TODO: this should be an input from a user UI.
BRESEQ_EXPERIMENT_PERSON_NAME = "Troy"


def main():

    db_session = alchemy_orm.Session()

    # TODO: shouldn't be returning multiple objects, because you remember return order; bad practice.
    experiment,\
    media,\
    freezer_box\
        = get_project_orm(db_session)

    create_and_commit_ale_entry(db_session,
                                WILD_TYPE_PERSON_NAME,
                                BRESEQ_ISOLATE_OUTPUT_PATH,
                                WILD_TYPE_ALE_NUMBER,
                                WILD_TYPE_FLASK_NUMBER,
                                WILD_TYPE_ISOLATE_NUMBER,
                                experiment,
                                media,
                                freezer_box)

    # Might need to explicitly sort this list in the future.
    breseq_sample_report_list = get_sample_report_list(
        BRESEQ_EXPERIMENT_OUTPUT_PATH)

    for breseq_sample_name in breseq_sample_report_list:

        split = breseq_sample_name.split("-")

        # find the isolate from the folder name
        ale_number = int(split[0])
        flask_number = int(split[1])
        isolate_number = 1  # TODO: find out why is this set to 1 for all endpoints and make it a constant.

        # TODO: handle population samples differently from clonal.
        # May have to implement other "create" scripts do this.
        # The method for handling populations was exemplified in deleted
        # obsolete scripts. Refer to them for the code when necessary.

        output_path = BRESEQ_EXPERIMENT_OUTPUT_PATH\
                      + breseq_sample_name\
                      + "/"\
                      + BRESEQ_OUTPUT_REPORT_DIR

        create_and_commit_ale_entry(db_session,
                                    BRESEQ_EXPERIMENT_PERSON_NAME,
                                    output_path,
                                    ale_number,
                                    flask_number,
                                    isolate_number,
                                    experiment,
                                    media,
                                    freezer_box)

    # validate mutations in each parallel ale
    for ale in experiment.ale_ids:
        validatemutations.check_negative_predictions(ale.ale_experiment_id,
                                                     ale.ale_id)


def create_and_commit_ale_entry(db_session,
                                person,
                                breseq_folder,
                                ale_number,
                                flask_number,
                                isolate_number,
                                experiment,
                                media,
                                freezer_box):

    ale_id = alchemy_orm.query_or_create(db_session,
                                         alchemy_orm.AleId,
                                         ale_experiment=experiment,
                                         ale_id=ale_number)

    flask = alchemy_orm.query_or_create(db_session,
                                        alchemy_orm.Flask,
                                        flask_number=flask_number,
                                        ale_id=ale_id,
                                        media=media)

    isolate = alchemy_orm.query_or_create(db_session,
                                          alchemy_orm.Isolate,
                                          flask=flask,
                                          isolate_number=isolate_number,
                                          is_population=False,
                                          freezer_box=freezer_box,
                                          person=person)

    db_session.commit()

    upload.add_breseq_results(session=db_session,
                              isolate_id=isolate.id,
                              person=person,
                              breseq_folder=breseq_folder,
                              wt=True)

    db_session.commit()


# TODO: make all default values used within this script as constants or in a config file.
# TODO: add more parameters to function for inputs set as literals.
def get_project_orm(db_session):

    # create the instrument, experiment, etc. to the isolates for the strains
    instrument = alchemy_orm.query_or_create(db_session,
                                             alchemy_orm.Instrument,
                                             name="")

    experiment = alchemy_orm.query_or_create(db_session,
                                             alchemy_orm.AleExperiment,
                                             name="SSW BOP27",
                                             instrument=instrument,
                                             person=BRESEQ_EXPERIMENT_PERSON_NAME,
                                             date=datetime.date(1, 1, 1),
                                             simulation=False)

    media = alchemy_orm.query_or_create(db_session,
                                        alchemy_orm.Media,
                                        description="asdf",
                                        temperature=0,
                                        volume=0,
                                        stirring_speed=0)

    freezer_box = alchemy_orm.query_or_create(db_session,
                                              alchemy_orm.FreezerBox,
                                              name="ale box",
                                              number=0)

    # TODO: find a better way to return these, so that don't have to worry about return order.
    return experiment, media, freezer_box


def get_sample_report_list(experiment_breseq_output_path):

    breseq_sample_report_list = []

    for breseq_sample_names in os.listdir(experiment_breseq_output_path):

        sample_path = experiment_breseq_output_path + breseq_sample_names
        sample_breseq_output_report = sample_path\
                                      + '/'\
                                      + BRESEQ_OUTPUT_REPORT_DIR\
                                      + BRESEQ_OUTPUT_REPORT_FILE

        if os.path.isdir(sample_path) and os.path.isfile(sample_breseq_output_report):
            breseq_sample_report_list.append(breseq_sample_names)

    return breseq_sample_report_list


if __name__ == "__main__":
    main()
