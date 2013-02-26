import os
import sys

from sqlalchemy import create_engine, Table, MetaData, Column, ForeignKey, Integer
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

# add aleinfo directory to the path
ale_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ale_dir, "aleinfo"))

from settings import DATABASES

db_settings = DATABASES["default"]

if db_settings["ENGINE"].endswith("sqlite3"):  # TODO handle mysql
    db = "sqlite"
    name = os.path.join(ale_dir, db_settings["NAME"])
    connection_str = "%s:///%s" % (db, name)
elif db_settings["ENGINE"].endswith("postgresql_psycopg2"):
    connection_str = "postgresql://%s:%s@%s/%s" % \
        (db_settings["USER"], db_settings["PASSWORD"], db_settings["HOST"], db_settings["NAME"])
engine = create_engine(connection_str)
Base = declarative_base()
metadata = MetaData(bind=engine)
Session = sessionmaker(bind=engine)

class ObservedMutation(Base):
    __table__ = Table("seq_observedmutation", metadata, autoload=True)
    mutation = relationship("Mutation")
    experiment = relationship("ResequencingExperiment")

class ResequencingExperiment(Base):
    __table__ = Table("seq_resequencingexperiment", metadata, autoload=True)

class Mutation(Base):
    __table__ = Table("seq_mutation", metadata, autoload=True)
    experients = relationship(ResequencingExperiment,
        secondary=ObservedMutation.__table__,
        backref=backref("mutations", viewonly=True),
        viewonly=True)


if __name__ == "__main__":
    session = Session()
    from IPython import embed; embed()

