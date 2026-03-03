from abc import ABC, abstractmethod


class BaseHRMSConnector(ABC):
    def __init__(self, connection, db, settings):
        self.connection = connection
        self.db = db
        self.settings = settings

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def exchange_code_for_token(self, code: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fetch_employees(self, updated_after=None, status=None):
        raise NotImplementedError
