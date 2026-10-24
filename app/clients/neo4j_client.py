import logging
import threading
from typing import Optional, Any, Dict, List
from neo4j import GraphDatabase, Driver
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    _instance: Optional["Neo4jClient"] = None
    _lock = threading.Lock()
    _driver: Optional[Driver] = None

    def __new__(cls) -> "Neo4jClient":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> Driver:
        if self._driver is None:
            with self._lock:
                if self._driver is None:
                    settings = get_settings()
                    uri = settings.NEO4J_URI
                    user = settings.NEO4J_USER
                    password = settings.NEO4J_PASSWORD
                    uris_to_try = [uri]
                    if "neo4j:" in uri:
                        uris_to_try.append(uri.replace("neo4j:", "localhost:"))

                    connected = False
                    last_err = None
                    for target_uri in uris_to_try:
                        try:
                            logger.info("Connecting to Neo4j at %s ...", target_uri)
                            self._driver = GraphDatabase.driver(
                                target_uri,
                                auth=(user, password),
                                max_connection_lifetime=30 * 60,
                                max_connection_pool_size=50,
                                connection_acquisition_timeout=2 * 60,
                            )
                            self._driver.verify_connectivity()
                            logger.info("Connected to Neo4j successfully at %s", target_uri)
                            connected = True
                            break
                        except Exception as e:
                            last_err = e
                            logger.warning("Could not connect to Neo4j at %s: %s", target_uri, e)

                    if not connected:
                        self._driver = None
                        raise RuntimeError(f"Neo4j connection error: {last_err}") from last_err
        return self._driver

    def close(self):
        with self._lock:
            if self._driver:
                try:
                    self._driver.close()
                    logger.info("Neo4j driver closed successfully.")
                except Exception as e:
                    logger.warning("Error closing Neo4j driver: %s", e)
                finally:
                    self._driver = None

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            return self.connect()
        return self._driver

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        settings = get_settings()
        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        settings = get_settings()
        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]


neo4j_client = Neo4jClient()


def get_neo4j_client() -> Neo4jClient:
    return neo4j_client
