# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Lycophron is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Lycophron data models."""

import enum
from sqlalchemy import Column, Integer, String, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils.models import Timestamp

Model = declarative_base()


class RecordStatus(str, enum.Enum):
    NEW = "NEW"
    DEPOSIT_FAIL = "DEPOSIT_FAIL"
    DEPOSIT_SUCCESS = "DEPOSIT_SUCCESS"
    PUBLISH_FAIL = "RECORD_FAIL"
    PUBLISH_SUCCESS = "PUBLISH_SUCCESS"
    FILE_FAIL = "FILE_FAIL"
    FILE_SUCCESS = "FILE_SUCCESS"


class Record(Model, Timestamp):
    """Local representation of a record."""

    __tablename__ = "record"
    id = Column(Integer, primary_key=True)
    communities = Column(JSON)
    doi = Column(String)
    deposit_id = Column(String)
    # Represents the last known metadata's state on Zenodo
    remote_metadata = Column(JSON)
    response = Column(JSON)  # TODO response, errors
    # Already validated by marshmallow
    original = Column(JSON)
    files = Column(JSON)
    status = Column(Enum(RecordStatus), default=RecordStatus.NEW)
    links = Column(JSON, default={})

    def __repr__(self) -> str:
        return f"Record {self.doi}"

    def to_dict(self):
        return {
            "id": self.id,
            "doi": self.doi,
            "deposit_id": self.deposit_id,
            "status": self.status,
            "communities": self.communities,
            "original": self.original,
            "files": self.files,
            "links": self.links,
        }
