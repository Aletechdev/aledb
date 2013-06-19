from alchemy_orm import *
from upload import add_breseq_results
from validatemutations import check_negative_predictions
import datetime
from os import listdir
from os.path import abspath, dirname, isdir, isfile

session = Session()

# create the instrument, experiment, etc. to the isolates for the strains
instrument = query_or_create(session, Instrument, name="UCSD1")
experiment = query_or_create(session, AleExperiment, name="42C evolution",
    instrument=instrument, person="ryan", date=datetime.date.today(), simulation=False)

media = query_or_create(session, Media, description="Glucose M9 media", temperature=42, volume=40, stirring_speed=1123)
freezer_box = query_or_create(session, FreezerBox, name="ale box", number=1)

sequencing_path = settings.sequencing_path + "glucose_temperature_evolution/"

runs = [i for i in listdir(sequencing_path) if isdir(sequencing_path + i) and isfile(sequencing_path + i + "/index.html") and i.startswith("Sample")]

# add wild type
ale_id = query_or_create(session, AleId, ale_experiment=experiment, ale_id=0)
flask = query_or_create(session, Flask, flask_number=0,
    ale_id=ale_id, media=media)
isolate = query_or_create(session, Isolate, flask=flask,
        isolate_number=0, is_population=False,
        freezer_box=freezer_box, person="BOP27")
session.commit()
add_breseq_results(session, isolate.id, "BOP27", sequencing_path + "BOP27", wt=True)
session.commit()

for i in runs:
    substr = i.strip("Sample").split("_")[0]
    if substr.endswith("W"):
        continue
    print i
    split = i.split("_")
    # find the isolate from the folder name
    ale_number = int(substr)
    flask_number = 1
    isolate_number = 1
    pop = False
    ale_id = query_or_create(session, AleId, ale_experiment=experiment,
        ale_id=ale_number)
    flask = query_or_create(session, Flask, flask_number=flask_number,
        ale_id=ale_id, media=media)
    isolate = query_or_create(session, Isolate, flask=flask,
        isolate_number=isolate_number, is_population=pop,
        freezer_box=freezer_box, person="Richard")
    session.commit()
    # upload data
    if not pop:
        add_breseq_results(session, isolate.id, "Richard", sequencing_path + i)

session.commit()

# validate mutations in each parallel ale
for ale in experiment.ale_ids:
    check_negative_predictions(ale.ale_experiment_id, ale.ale_id)
