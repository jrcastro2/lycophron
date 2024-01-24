# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Lycophron is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Lycophron project classes (business logic layer)."""

import os
from urllib.parse import urlparse

from .client import create_session
from .config import required_configs
from .errors import (
    DatabaseAlreadyExists,
    ErrorHandler,
    InvalidRecordData,
    InvalidDirectoryError,
)
from .loaders import LoaderFactory
from .schemas.record import RecordRow


class Project:
    def __init__(self, project_folder=os.getcwd()):
        self.project_folder = project_folder
        self.errors = []

    def load_file(self, filename):
        data = self.process_file(filename)
        for record in data:
            self.add_record(record)
        if len(self.errors):
            ErrorHandler.handle_error(self.errors)

    def process_file(self, filename):
        if not self.is_project_initialized():
            raise Exception("Project is not initialised.")
        factory = LoaderFactory()
        loader = factory.create_loader(filename)
        row_schema = RecordRow()
        records = []
        for data in loader.load(filename):
            try:
                record = row_schema.load(data)
            except Exception as e:
                self.errors.append(e)
            else:
                records.append(record)
        return records

    def add_record(self, record):
        # TODO fix too many "from .db import db"
        # TODO record data integrity is missing validation
        from .db import db

        try:
            db.add_record(record)
        except Exception as e:
            self.errors.append(e)

    def initialize(self):
        """Initialize the project"""
        from .db import db

        try:
            db.init_db()
        except DatabaseAlreadyExists as e:
            ErrorHandler.handle_error(e)

    def recreate_project(self):
        from .db import db

        db.recreate_db()

    def _is_valid_url(self, config):
        parsed_url = urlparse(config["ZENODO_URL"])
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError(f"Invalid URL provided: {config['ZENODO_URL']}.")

    def _is_valid_token(self, config):
        session = create_session(config["TOKEN"])
        url = config["ZENODO_URL"] + "/api/me"
        response = session.get(url)
        if response.status_code != 200:
            raise ValueError(
                f"Invalid token or URL provided. Token: {config['TOKEN']}, URL: {config['ZENODO_URL']}"
            )

    def validate_project(self, config):
        # Configs exist
        for required_value in required_configs:
            if not config[required_value]:
                raise ValueError(f"Missing required config: {required_value}")
        # Configs are valid (sqlite uri is already validated, as the db needs to be initialized in order to reach this)
        self._is_valid_url(config)
        self._is_valid_token(config)
        # Folder for files does exist
        folder_name = "files"
        if not os.path.exists(folder_name) or not os.path.isdir(folder_name):
            raise InvalidDirectoryError(f"Missing required folder: {folder_name}")

    def is_project_initialized(self):
        from .db import db

        return db.database_exists()

    def publish_records(self, url, token, num_records=None):
        from .tasks.tasks import publish_records

        publish_records.apply_async(
            args=[url, token, num_records],
        )
