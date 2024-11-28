import pymongo

def get_database_client(mongo_uri):
    """Creates and returns a MongoDB client."""
    return pymongo.MongoClient(mongo_uri)


def get_service_config(db, service_name):
    """Fetches service configuration from the database."""
    srv_collection = db.get_collection("service")
    srv_config = srv_collection.find_one({"name": service_name}, {"_id": 0})
    if not srv_config:
        raise ValueError(f"Service configuration for '{service_name}' not found.")
    return srv_config


def get_system_config(db, system_name):
    """Fetches system configuration from the database."""
    sys_collection = db.get_collection("system")
    system_config = sys_collection.find_one({"name": system_name}, {"_id": 0})
    if not system_config:
        raise ValueError(f"System configuration for '{system_name}' not found.")
    return system_config