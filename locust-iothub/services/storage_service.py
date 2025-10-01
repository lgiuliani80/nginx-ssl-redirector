from azure.core import MatchConditions
from azure.data.tables import TableServiceClient, UpdateMode


class StorageService:
    def __init__(self, connection_string: str):
        self.service = TableServiceClient.from_connection_string(connection_string)

    def create_table(self, table_name: str):
        self.service.create_table(table_name)

    def delete_table(self, table_name: str):
        self.service.delete_table(table_name)

    def create_table_entity(self, table_name: str, entity: dict):
        table = self.service.create_table_if_not_exists(table_name)
        table.create_entity(entity=entity)

    def get_table_entity(self, table_name: str, partition_key: str, row_key: str):
        table = self.service.create_table_if_not_exists(table_name)
        return table.get_entity(partition_key=partition_key, row_key=row_key)

    def get_table_entities(self, table_name: str, filter: str = None):
        table = self.service.create_table_if_not_exists(table_name)
        if filter is None:
            return table.list_entities()
        else:
            return table.query_entities(filter=filter)

    def update_table_entity(self, table_name: str, entity: dict):
        table = self.service.create_table_if_not_exists(table_name)
        table.update_entity(
            entity=entity,
            mode=UpdateMode.MERGE,
            match_condition=MatchConditions.IfNotModified
        )

    def delete_all_table_entities(self, table_name: str):
        table = self.service.create_table_if_not_exists(table_name)
        entities = table.list_entities()
        for entity in entities:
            table.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])