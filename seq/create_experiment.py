import alchemy_orm
import upload
import validatemutations
import datetime
import os

BRESEQ_OUTPUT_REPORT_FILE = "index.html"


def main():
    db_session = alchemy_orm.Session()

    # create the instrument, experiment, etc. to the isolates for the strains
    instrument = alchemy_orm.query_or_create(db_session,
                                             alchemy_orm.Instrument,
                                             name="UCSD1")

    experiment = alchemy_orm.query_or_create(db_session,
                                             alchemy_orm.AleExperiment,
                                             name="Glycerol Dynamics",
                                             instrument=instrument,
                                             person="ryan",
                                             date=datetime.date(2013, 1, 1),
                                             simulation=False)

    media = alchemy_orm.query_or_create(db_session,
                                        alchemy_orm.Media,
                                        description="Glycerol M9 media",
                                        temperature=30,
                                        volume=15,
                                        stirring_speed=1100)

    freezer_box = alchemy_orm.query_or_create(db_session,
                                              alchemy_orm.FreezerBox,
                                              name="ale box",
                                              number=1)

    # add wild type
    ale_id = alchemy_orm.query_or_create(db_session,
                                         alchemy_orm.AleId,
                                         ale_experiment=experiment,
                                         ale_id=0)

    flask = alchemy_orm.query_or_create(db_session,
                                        alchemy_orm.Flask,
                                        flask_number=0,
                                        ale_id=ale_id,
                                        media=media)

    isolate = alchemy_orm.query_or_create(db_session,
                                          alchemy_orm.Isolate,
                                          flask=flask,
                                          isolate_number=0,
                                          is_population=False,
                                          freezer_box=freezer_box,
                                          person="BOP27")

    db_session.commit()

    upload.add_breseq_results(db_session,
                              isolate.id,
                              "BOP27",
                              "/data/breseq/BOP27_reseq",
                              wt=True)

    db_session.commit()

    # !!! ENSURE THAT THE TRAILING '/' IS ALWAYS INCLUDED
    experiment_breseq_output_path = "/data/breseq/glycerol_dynamics_clonal/"

    # Might need to explicitly sort this list in the future.
    breseq_sample_report_list = get_sample_report_list(experiment_breseq_output_path)

    for breseq_sample_name in breseq_sample_report_list:

        split = breseq_sample_name.split("-")

        # find the isolate from the folder name
        ale_number = int(split[0])
        flask_number = int(split[1])
        isolate_number = 1

        # TODO: handle population samples differently from clonal. Other "create" scripts do this.
        # The method for handling populations was exemplified in delete obsolete scripts. Refer
        # to them for the code when necessary.

        print breseq_sample_name

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
                                              person="ryan")

        db_session.commit()

        upload.add_breseq_results(db_session,
                              isolate.id,
                              "ryan",
                              experiment_breseq_output_path + breseq_sample_name)

        db_session.commit()

    # validate mutations in each parallel ale
    for ale in experiment.ale_ids:
        validatemutations.check_negative_predictions(ale.ale_experiment_id, ale.ale_id)


def get_sample_report_list(experiment_breseq_output_path):
    breseq_sample_report_list = []

    for breseq_sample_names in os.listdir(experiment_breseq_output_path):

        sample_path = experiment_breseq_output_path + breseq_sample_names
        sample_breseq_output_report = sample_path + '/' + BRESEQ_OUTPUT_REPORT_FILE

        if os.path.isdir(sample_path) and os.path.isfile(sample_breseq_output_report):
            breseq_sample_report_list.append(breseq_sample_names)

    return breseq_sample_report_list


if __name__ == "__main__":
    main()
