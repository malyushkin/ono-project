import argparse
import sys
import psycopg2.extras

from typing import Any, Dict, List, Set, Optional
from uuid import uuid4
from sshtunnel import SSHTunnelForwarder
# from sqlalchemy import create_engine
# from sqlalchemy.engine.url import URL

from ner.natasha.client import NatashaClient, MODEL_NAME
from pipeline.ono.queries import (
    INSERT_ARTICLE_QUERY,
    INSERT_ENTITY_QUERY,
    INSERT_ARTICLE_X_ENTITY_QUERY,
    SELECT_ALL_QUERY,
    SELECT_SPEC_ENTITY_QUERY,
)
from pipeline.config import (
    SOURCE_SLUG_MAPPER,
    ONO_SOURCE_STR,
)
from pipeline.utils import source_slug_mapper_maker

parser = argparse.ArgumentParser()
parser.add_argument("--pg_host", default="localhost")
parser.add_argument("--pg_port", default="5432")
parser.add_argument("-f", "--file", required=False, help="JSON file name")
parser.add_argument("-s", "--source", required=False, default=ONO_SOURCE_STR)

args = parser.parse_args()
args_vars = vars(args)

# Rima SSH
SSH_HOST = "bastion.de.rima.media"
SSH_PRIVATE_KEY = "~/.ssh/id_rsa"
SSH_USERNAME = "rmalushkin"
SSH_BIND_ADDRESS = "rima-de.cluster-cuacljzqucw0.us-west-2.rds.amazonaws.com"

# Rima Postgre
POSTGRE_DATABASE = "rima_ext"
POSTGRE_USER = "rmalushkin"
POSTGRE_PASSWORD = "efjD#(nKLa"

POSTGRE_CONFIG = {
    "dbname": "rima_ext",
    "user": POSTGRE_USER,
    "password": POSTGRE_PASSWORD,
    "host": args_vars["pg_host"],
    "port": args_vars["pg_port"]
}

SOURCE_SET = set(args_vars["source"].split(" "))
SOURCE_SLUG_MAPPER_DATA = source_slug_mapper_maker(SOURCE_SLUG_MAPPER)

LOCAL_PORT = 5432
connection, cursor = None, None
print(SOURCE_SET)

psycopg2.extras.register_uuid()


def execute_query(query, vars=None) -> Optional[List]:
    """

    :param query:
    :return:
    """

    # print(cursor)

    cursor.execute(query, vars)

    if cursor.pgresult_ptr is not None:
        rows = cursor.fetchall()
        return rows

    return None


def get_raw_data(source_name) -> List:
    """
    Get postgres raw data by source name

    :param source_name:
    :return:
    """

    _query = SELECT_ALL_QUERY.format(
        schema="ono",
        table="archive_ono_master_articles",
        s=source_name
    )
    raw_data = execute_query(_query)

    return raw_data


def extract_ner(text) -> Set:
    """

    :param text:
    :return:
    """
    ner_obj = NatashaClient(f"А {text}")
    return ner_obj.ner()


def process_article_ner(article_id, ner_data, is_title=False):
    """

    :param article_id:
    :param ner_data:
    :param is_title:
    :return:
    """
    for ner_item in ner_data:
        ner_name = ner_item[1].replace("'", "''")

        _params = {
            "schema": "ono",
            "table": "entity",
            "m": MODEL_NAME,
            "t": ner_item[0],
            "n": ner_name,
        }

        ner_db = execute_query(SELECT_SPEC_ENTITY_QUERY.format(**_params))

        if len(ner_db) > 1:
            raise ValueError

        elif len(ner_db) == 1:
            entity_id = ner_db[0][1]

        else:
            entity_id = uuid4()
            entity = (
                entity_id,
                MODEL_NAME,  # model
                ner_item[0],  # tag
                ner_name,  # name
            )
            execute_query(INSERT_ENTITY_QUERY, entity)

        article_x_entity = (
            article_id,
            entity_id,
            is_title,
        )
        execute_query(INSERT_ARTICLE_X_ENTITY_QUERY, article_x_entity)


def process_article(source_item):
    """

    :param source_item:
    :return:
    """

    # Insert article
    article_id = uuid4()
    article = (
        article_id,
        item[1],  # title
        item[2],  # plain_text
        item[0],  # date
        item[3],  # link
        SOURCE_SLUG_MAPPER_DATA[item[4]],  # source
    )

    execute_query(INSERT_ARTICLE_QUERY, article)
    connection.commit()
    # cursor.execute(INSERT_ARTICLE_QUERY, article)

    # Extract & insert title NER
    article_ner_data = extract_ner(source_item[1])
    process_article_ner(article_id, article_ner_data, is_title=True)
    connection.commit()

    # Extract & insert plain text NER
    article_ner_data = extract_ner(source_item[2])
    process_article_ner(article_id, article_ner_data, is_title=False)
    connection.commit()

if __name__ == "__main__":

    while len(SOURCE_SET):

        source = SOURCE_SET.pop()
        print(source)  ## TODO: remove

        with SSHTunnelForwarder(
                (SSH_HOST, 22),
                ssh_private_key=SSH_PRIVATE_KEY,
                ssh_username=SSH_USERNAME,
                remote_bind_address=(SSH_BIND_ADDRESS, 5432),
        ) as ssh:
            ssh.start()

            # data = get_raw_data(source)[:1]  # for tests
            LOCAL_PORT = ssh.local_bind_port

            # print(LOCAL_PORT)

            params = POSTGRE_CONFIG.copy()
            params["port"] = LOCAL_PORT
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()

            # print(connection)
            # print(cursor)

            data = get_raw_data(source)

            for item in data:
                try:
                    process_article(item)

                except Exception as e:
                    print(e)
                    print(item[0], item[1])

            print(f"For source `{source}` {len(data)} items has been added")

            ssh.stop()

            # sys.exit()
