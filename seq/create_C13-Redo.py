from alchemy_orm import *
from upload import add_breseq_results
from validatemutations import check_negative_predictions
import datetime
from os import listdir
from os.path import abspath, dirname, isdir, isfile
import pdb

session = Session()

# create the instrument, experiment, etc. to the isolates for the strains
instrument = query_or_create(session, Instrument, name="UCSD1.0")
experiment = query_or_create(session, AleExperiment, name="C13",
    instrument=instrument, person="Adam", simulation=False, date=datetime.date(2013, 1, 1))

media = query_or_create(session, Media, description="C13-Glucose M9 media", temperature=37, volume=15, stirring_speed=1200)
freezer_box = query_or_create(session, FreezerBox, name="ale box", number=1)


sequencing_path = settings.sequencing_path + "glycerol_dynamics/"

runs = [i for i in listdir(sequencing_path) if isdir(sequencing_path + i) and isfile(sequencing_path + i + "/index.html") and i.startswith("C13-Redo")]

def get_key(name):
    s = name.split("-")
    return (int(s[2]), int(s[3]))
#runs.sort(key=get_key)
print runs
#import sys
#sys.exit()

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


print sorted(runs)

for run in sorted(runs):
    split = run.split("-")
    # find the isolate from the folder name
    pdb.set_trace()
    if split[1] != 'pop':
        ale_number = int(split[2])
        flask_number = int(split[3])
	isolate_number = 1
	is_population = False
    else:
	ale_number = int(split[2])
	flask_number = int(split[3])
	isolate_number = 1
	is_population = True
    ale_id = query_or_create(session, AleId, ale_experiment=experiment,
        ale_id=ale_number)
    flask = query_or_create(session, Flask, flask_number=flask_number, ale_id=ale_id, media=media)
    isolate = query_or_create(session, Isolate, flask=flask,
        isolate_number=isolate_number, is_population=is_population,
        freezer_box=freezer_box, person="Adam")
    session.commit()
    add_breseq_results(session, isolate.id, "Adam", sequencing_path + run)
    session.commit()

# validate mutations in each parallel ale
#for ale in experiment.ale_ids:
#    check_negative_predictions(ale.ale_experiment_id, ale.ale_id)
