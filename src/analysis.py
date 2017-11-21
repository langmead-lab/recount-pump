#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

from sqlalchemy import Column, ForeignKey, Integer, String, Sequence, DateTime, Table
from base import Base


class Analysis(Base):
    __tablename__ = 'analysis'

    id = Column(Integer, Sequence('analysis_id_seq'), primary_key=True)
    container_url = Column(String(4096))


def set_up_bioconda(envname='recount-pump', ):
    """
    This runs on a cluster node and installs all the requisite analysis tools
    in a virtualenv using bioconda.
    """
    pass


def check_bioconda(envname='recount-pump', ):
    """
    This checks whether the requisite tools are (still) installed in a
    virtualenv of the given name.
    """
