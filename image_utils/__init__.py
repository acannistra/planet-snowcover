from os import environ as env
try:
    env["PL_API_KEY"]
except ImportError:
    raise("PL_API_KEY not defined in environment.")
else:
    print("image_utils: found API key")