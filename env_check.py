import subprocess, sys

# Check Redis server
try:
    import redis
    r = redis.Redis(host='localhost', port=6379)
    r.ping()
    redis_status = "running"
except Exception as e:
    redis_status = f"not running: {e}"

# Install fakeredis
try:
    import fakeredis
    fakeredis_status = f"installed {fakeredis.__version__}"
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fakeredis", "-q"])
    import fakeredis
    fakeredis_status = f"installed {fakeredis.__version__}"

with open("env_check_result.txt", "w") as f:
    f.write(f"redis_server: {redis_status}\n")
    f.write(f"fakeredis: {fakeredis_status}\n")
    f.write(f"redis_py: {redis.__version__}\n")
    f.write("done\n")
