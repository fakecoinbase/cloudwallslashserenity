import os
import psycopg2


def connect_serenity_db(hostname: str = 'localhost', username: str = 'postgres',
                        password: str = os.getenv('POSTGRES_PASSWORD', None)):
    return psycopg2.connect(host=hostname, dbname="serenity", user=username, password=password)
