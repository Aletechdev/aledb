from alchemy_orm import *  # TODO: Don't import everything.
import upload
from validatemutations import check_negative_predictions
import datetime
from os import listdir
from os.path import isdir, isfile

BRESEQ_OUTPUT_REPORT_FILE = "index.html"


def main():

    db_session = Session()

    # create the instrument, experiment, etc. to the isolates for the strains
    instrument = query_or_create(db_session, Instrument, name="UCSD1")
    experiment = query_or_create(db_session,
                                 AleExperiment,
                                 name="Glycerol Dynamics",
                                 instrument=instrument,
                                 person="ryan",
                                 date=datetime.date(2013, 1, 1),
                                 simulation=False)

    media = query_or_create(db_session,
                            Media,
                            description="Glycerol M9 media",
                            temperature=30,
                            volume=15,
                            stirring_speed=1100)

    freezer_box = query_or_create(db_session,
                                  FreezerBox,
                                  name="ale box",
                                  number=1)

    # add wild type
    ale_id = query_or_create(db_session,
                             AleId,
                             ale_experiment=experiment,
                             ale_id=0)

    flask = query_or_create(db_session,
                            Flask,
                            flask_number=0,
                            ale_id=ale_id,
                            media=media)

    isolate = query_or_create(db_session,
                              Isolate,
                              flask=flask,
                              isolate_number=0,
                              is_population=False,
                              freezer_box=freezer_box,
                              person="BOP27")
    db_session.commit()

    # add_breseq_results(db_session, isolate.id, "BOP27", settings.sequencing_path + "BOP27_reseq", wt=True)
    # TODO: /data/breseq defined for settings.sequencing_path.
    upload.add_breseq_results(db_session,
                       isolate.id,
                       "BOP27",
                       "/data/breseq/BOP27_reseq",
                       wt=True)

    db_session.commit()

    # !!! ENSURE THAT THE TRAILING '/' IS ALWAYS INCLUDED
    # sequencing_path = settings.sequencing_path + "C13-Redo/"
    # TODO: /data/breseq defined for settings.sequencing_path.
    experiment_breseq_output_path = "/data/breseq/glycerol_dynamics_clonal/"

    # Might need to explicitely sort this list in the future.
    breseq_sample_report_list = get_sample_report_list(experiment_breseq_output_path)

    for breseq_sample_name in breseq_sample_report_list:

        split = breseq_sample_name.split("-")

        # find the isolate from the folder name
        ale_number = int(split[0])
        flask_number = int(split[1])
        isolate_number = 1
        pop = split[-1] == "clonal"
        print breseq_sample_name
        ale_id = query_or_create(db_session, AleId, ale_experiment=experiment,
                                 ale_id=ale_number)
        flask = query_or_create(db_session, Flask, flask_number=flask_number,
                                ale_id=ale_id, media=media)
        isolate = query_or_create(db_session, Isolate, flask=flask,
                                  isolate_number=isolate_number, is_population=pop,
                                  freezer_box=freezer_box, person="ryan")
        db_session.commit()
        # upload data
        # if not pop:
        #    add_breseq_results(db_session, isolate.id, "Gaby", sequencing_path + i)
        if pop:
            upload.add_pop_results(db_session, isolate.id, "ryan", experiment_breseq_output_path + breseq_sample_name)
        else:
            upload.add_breseq_results(db_session, isolate.id, "ryan", experiment_breseq_output_path + breseq_sample_name)

    db_session.commit()

    # validate mutations in each parallel ale
    for ale in experiment.ale_ids:
        check_negative_predictions(ale.ale_experiment_id, ale.ale_id)


def get_sample_report_list(experiment_breseq_output_path):

    breseq_sample_report_list = []

    for breseq_sample_names in listdir(experiment_breseq_output_path):

        sample_path = experiment_breseq_output_path + breseq_sample_names
        sample_breseq_output_report = sample_path + '/' + BRESEQ_OUTPUT_REPORT_FILE

        if isdir(sample_path) and isfile(sample_breseq_output_report):
            breseq_sample_report_list.append(breseq_sample_names)

    return breseq_sample_report_list


if __name__ == "__main__":
    main()
