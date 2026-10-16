from falkordb import FalkorDB

from app.config import (
    FALKORDB_HOST,
    FALKORDB_PORT,
    FALKORDB_USERNAME,
    FALKORDB_PASSWORD,
    FALKORDB_TLS,
    FALKORDB_GRAPH,
)


class GraphDatabase:
    def __init__(self):
        self.client = FalkorDB(
            host=FALKORDB_HOST,
            port=FALKORDB_PORT,
            username=FALKORDB_USERNAME,
            password=FALKORDB_PASSWORD,
            ssl=FALKORDB_TLS,
            socket_connect_timeout=5,
            socket_timeout=10,
        )

        self.graph = self.client.select_graph(
            FALKORDB_GRAPH
        )

    def query(self, cypher: str, params: dict | None = None):
        return self.graph.query(
            cypher,
            params or {},
        )

    def health_check(self) -> bool:
        self.graph.query("RETURN 1 AS healthy")
        return True