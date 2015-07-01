from alchemy_orm import *
from upload import add_breseq_results
from validatemutations import check_negative_predictions
import datetime
from os import listdir
from os.path import abspath, dirname, isdir, isfile

session = Session()

# create the instrument, experiment, etc. to the isolates for the strains
instrument = query_or_create(session, Instrument, name="Adam")
experiment = query_or_create(session, AleExperiment, name="Isozyme discovery KO",
    instrument=instrument, person="Adam", simulation=False, date=datetime.date.today())

media = query_or_create(session, Media, description="Glucose M9 media", temperature=37, volume=40, stirring_speed=1123)
freezer_box = query_or_create(session, FreezerBox, name="ale box", number=1)


sequencing_path = settings.sequencing_path + "isozyme/"

# add wild type
ale_id = query_or_create(session, AleId, ale_experiment=experiment, ale_id=0)
flask = query_or_create(session, Flask, flask_number=0,
    ale_id=ale_id, media=media)
isolate = query_or_create(session, Isolate, flask=flask,
        isolate_number=0, is_population=False,
        freezer_box=freezer_box, person="Adam", description="BOP27")
session.commit()
add_breseq_results(session, isolate.id, "Adam", settings.sequencing_path + "BOP27_reseq/", wt=True)
session.commit()

runs = [i for i in listdir(sequencing_path) if isdir(sequencing_path + i) and isfile(sequencing_path + i + "/index.html")]
print sorted(runs)

for i, run in enumerate(sorted(runs)):
    flask = query_or_create(session, Flask, flask_number=i + 1, ale_id=ale_id, media=media)
    isolate = query_or_create(session, Isolate, flask=flask,
        isolate_number=1, is_population=False, description=run,
        freezer_box=freezer_box, person="Adam")
    session.commit()
    add_breseq_results(session, isolate.id, "Adam", sequencing_path + run)
    session.commit()
