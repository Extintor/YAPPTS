import redis

r = redis.Redis(
    host='redis-13882.c135.eu-central-1-1.ec2.cloud.redislabs.com',
    port=13882,
    password='dbWpteeJL36hUyfpv0Z1XoIBxHLtxJ7e')

r.flushdb()