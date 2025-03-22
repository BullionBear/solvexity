import unittest
import redis
import sqlalchemy
from solvexity.analytic.feed import Feed

class TestFeedIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Connect to real Redis
        cls.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
        cls.redis.ping()  # will raise an error if not connected

        # Connect to real PostgreSQL
        db_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/test_db"
        cls.engine = sqlalchemy.create_engine(db_url)
        cls.engine.connect()  # test connection

        # Initialize Feed
        cls.feed = Feed(cache=cls.redis, sql_engine=cls.engine)

    def test_redis_set_get(self):
        self.redis.set("test_key", "hello")
        value = self.redis.get("test_key")
        self.assertEqual(value, "hello")

    def test_sql_connection(self):
        with self.engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
            self.assertEqual(result.scalar(), 1)
