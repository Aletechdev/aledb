import os
import sys

from sqlalchemy import create_engine, Table, MetaData, Column, ForeignKey, Integer
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

# add aleinfo directory to the path
ale_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ale_dir, "aleinfo"))
import settings

DATABASES = settings.DATABASES

db_settings = DATABASES["default"]

hostname = db_settings["HOST"]
if "PORT" in db_settings:
    if len(db_settings["PORT"]) > 0:
        hostname += ":" + db_settings["PORT"]
if db_settings["ENGINE"].endswith("sqlite3"):
    db = "sqlite"
    name = os.path.join(ale_dir, db_settings["NAME"])
    connection_str = "%s:///%s" % (db, name)
elif db_settings["ENGINE"].endswith("postgresql_psycopg2"):
    connection_str = "postgresql://%s:%s@%s/%s" % \
                     (db_settings["USER"], db_settings["PASSWORD"],
                      hostname, db_settings["NAME"])
elif db_settings["ENGINE"].endswith("mysql"):
    connection_str = "mysql://%s:%s@%s/%s?charset=utf8" % \
                     (db_settings["USER"], db_settings["PASSWORD"],
                      hostname, db_settings["NAME"])

engine = create_engine(connection_str)
Base = declarative_base()
metadata = MetaData(bind=engine)
Session = sessionmaker(bind=engine)


class ResequencingExperiment(Base):
    __table__ = Table("seq_resequencingexperiment", metadata, autoload=True)
    isolate = relationship("Isolate",
                           primaryjoin="ResequencingExperiment.isolate_id == Isolate.id",
                           foreign_keys=[__table__.c.isolate_id])


class ObservedMutation(Base):
    __table__ = Table("seq_observedmutation", metadata, autoload=True)
    mutation = relationship("Mutation")
    experiment = relationship("ResequencingExperiment")


class Mutation(Base):
    __table__ = Table("seq_mutation", metadata, autoload=True)
    experiments = relationship(ResequencingExperiment,
                              secondary=ObservedMutation.__table__,
                              backref=backref("mutations", viewonly=True),
                              viewonly=True)


# models for ALE objects

class Instrument(Base):
    __table__ = Table("ale_instrument", metadata, autoload=True)


class AleExperiment(Base):
    __table__ = Table("ale_aleexperiment", metadata, autoload=True)
    instrument = relationship(Instrument, backref="ale_experiments")


class Media(Base):
    __table__ = Table("ale_media", metadata, autoload=True)


class AleId(Base):
    __table__ = Table("ale_aleid", metadata, autoload=True)
    ale_experiment = relationship(AleExperiment, backref="ale_ids")
    starting_strain = relationship("Isolate",
                                   # for some reason this fails in sqlite so more specification is needed
                                   primaryjoin="AleId.starting_strain_id == Isolate.id",
                                   foreign_keys=[__table__.c.starting_strain_id])


class FreezerBox(Base):
    __table__ = Table("ale_freezerbox", metadata, autoload=True)


class Flask(Base):
    __table__ = Table("ale_flask", metadata, autoload=True)
    ale_id = relationship("AleId", backref="flasks")
    media = relationship("Media", backref="flasks")


class Isolate(Base):
    __table__ = Table("ale_isolate", metadata, autoload=True)
    flask = relationship("Flask", backref="isolates")
    freezer_box = relationship("FreezerBox")
    # child_isolates = relationship("Isolate")


def query_or_create(session, class_type, **kwargs):
    """query an object using filter_by on the kwargs. If no such object
    is found in the database, a new one will be created which satisfies
    these constraints, and added to the session"""
    result = session.query(class_type).filter_by(**kwargs).first()
    if result is None:
        result = class_type()
        for key, value in kwargs.iteritems():
            setattr(result, key, value)
        session.add(result)
    return result


if __name__ == "__main__":
    session = Session()
    from IPython import embed;

    embed()
