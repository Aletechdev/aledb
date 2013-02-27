from alchemy_orm import *
from upload import add_breseq_results
import datetime
from os import listdir
from os.path import abspath, dirname, isdir, isfile

session = Session()

# create the instrument, experiment, etc. to the isolates for the strains
instrument = query_or_create(session, Instrument, name="UCSD1")
experiment = query_or_create(session, AleExperiment, name="glucose evolution",
    instrument=instrument, person="ryan", date=datetime.date.today(), simulation=False)

media = query_or_create(session, Media, description="Glucose M9 media", temperature=37, volume=40, stirring_speed=1123)
freezer_box = query_or_create(session, FreezerBox, name="ale box", number=1)

for i in range(11):
    ale_id = query_or_create(session, AleId, ale_id=i, ale_experiment=experiment)
    for j in range(3):
        flask = query_or_create(session, Flask, ale_id=ale_id, flask_number=j + 1, media=media)
        population_isolate = query_or_create(session, Isolate, flask=flask,
            isolate_number=0, person="Gaby", is_population=True,
            freezer_box=freezer_box)
        clone = query_or_create(session, Isolate, flask=flask, isolate_number=1,
            person="Gaby", is_population=False, freezer_box=freezer_box)
        # each clone is made from the frozen population
        clone.parent_isolate_id = population_isolate.id

session.commit()


# sloppy code to find sequencing experiments based off of folder names
sequencing_path = "/home/aebrahim/ale_sequencing/"

runs = [i for i in listdir(sequencing_path) if isdir(sequencing_path + i) and isfile(sequencing_path + i + "/index.html")]

flask_mapping = {"x": 1, "y": 2, "z": 3}

for i in runs:
    if len(i) > 4:
        continue
    # find the isolate from the folder name
    ale_number = int(i.split("_")[0])
    flask_letter = i.split("_")[1]
    flask_number = flask_mapping[flask_letter]
    ale_id = session.query(AleId).filter_by(ale_experiment=experiment, ale_id=ale_number).first()
    flask = session.query(Flask).filter_by(flask_number=flask_number, ale_id=ale_id).first()
    isolate = session.query(Isolate).filter_by(flask=flask, is_population=False).first()
    # upload data
    add_breseq_results(session, isolate.id, "Gaby", sequencing_path + i)

session.commit()

