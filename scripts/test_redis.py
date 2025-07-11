import os
import sys
import tempfile

try:
    import redis
except ImportError:
    print("Error: The 'redis' package is not installed.")
    print("Please install it by running: pip install redis")
    sys.exit(1)

from mlox.session import MloxSession
from mlox.services.redis.docker import RedisDockerService

# --- Load MLOX Session and find Redis service ---
password = os.environ.get("MLOX_CONFIG_PASSWORD", None)
if not password:
    print("Error: MLOX_CONFIG_PASSWORD environment variable is not set.")
    exit(1)

session = MloxSession("mlox", password)
infra = session.infra

redis_service = None
for bundle in infra.bundles:
    for service in bundle.services:
        if isinstance(service, RedisDockerService):
            redis_service = service
            break
    if redis_service:
        break

if not redis_service:
    print("Could not find a Redis service in the infrastructure.")
    exit(1)

bundle = infra.get_bundle_by_service(redis_service)
if not bundle:
    print(f"Could not find bundle for service {redis_service.name}")
    exit(1)

# --- CONNECTION PARAMETERS (loaded from MLOX) ---
REDIS_HOST = bundle.server.ip
REDIS_PORT = redis_service.port
REDIS_PASSWORD = redis_service.pw
REDIS_CERTIFICATE = redis_service.certificate


def main():
    """
    Attempts to connect to the Redis database using the specified
    credentials and SSL.
    """
    temp_cert_path = None
    client = None
    try:
        # Write the certificate from memory to a temporary file
        if REDIS_CERTIFICATE:
            tmp_dir = "./.tmp"
            os.makedirs(tmp_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".pem", dir=tmp_dir
            ) as f:
                f.write(REDIS_CERTIFICATE)
                temp_cert_path = f.name
            print(
                f"Temporary certificate for verification written to: {temp_cert_path}"
            )
        else:
            print("Error: No certificate found for Redis service.")
            sys.exit(1)

        print(
            f"Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT} with SSL..."
        )

        # Create Redis client with SSL configuration
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            ssl=True,
            ssl_cert_reqs=None,
            # ssl_ca_certs=temp_cert_path,
            decode_responses=True,  # Get strings back from Redis
        )

        # Ping the server to test the connection
        client.ping()
        print("✅ Success! Connection to Redis is established and is using SSL.")

    except redis.exceptions.ConnectionError as e:
        print(f"❌ Error: Could not connect to Redis.")
        print(f"   Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        if client:
            client.close()
            print("Connection closed.")
        if temp_cert_path and os.path.exists(temp_cert_path):
            os.remove(temp_cert_path)
            print(f"Removed temporary certificate: {temp_cert_path}")


if __name__ == "__main__":
    main()
