import argparse
import sys

import pandas as pd
import psycopg2.extras

from typing import List, Set, Optional
from uuid import uuid4
from sshtunnel import SSHTunnelForwarder

from ner.natasha.client import NatashaClient, MODEL_NAME
from pipeline.rima.queries import (
    INSERT_ARTICLE_QUERY,
    INSERT_ARTICLE_X_ENTITY_QUERY,
    SELECT_RIMA_RAW_QUERY,
    SELECT_ENTITIES_DICT_QUERY,
)
from pipeline.config import (
    SOURCE_SLUG_MAPPER,
    RIMA_SOURCE_STR,
)
from pipeline.utils import source_slug_mapper_maker

parser = argparse.ArgumentParser()
parser.add_argument("--pg_host", default="localhost")
parser.add_argument("--pg_port", default="5432")
parser.add_argument("-f", "--file", required=False, help="JSON file name")
parser.add_argument("-s", "--source", required=False, default=RIMA_SOURCE_STR)
parser.add_argument("-y", "--year", required=True)

args = parser.parse_args()
args_vars = vars(args)

# Rima config
RIMA_BASE_KEY = "RIMA"

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
    "user": POSTGRE_USER,
    "password": POSTGRE_PASSWORD,
    "host": args_vars["pg_host"],
    "port": args_vars["pg_port"],
}

SOURCE_SET = set(args_vars["source"].split(" "))
SOURCE_SLUG_MAPPER_DATA = source_slug_mapper_maker(SOURCE_SLUG_MAPPER)
YEAR = args_vars["year"]

connection, cursor = None, None
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


def get_raw_data(source_name) -> List[tuple]:
    """
    Get postgres raw data by source name

    :param source_name:
    :return:
    """

    _query = SELECT_RIMA_RAW_QUERY.format(
        schema="public",
        table="parsed_web_content",
        year=YEAR,
        s=source_name,
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

        match_pd = entities_pd[
            (entities_pd["tag"] == ner_item[0]) & (entities_pd["name"] == ner_name)
        ]

        if match_pd.shape[0] == 0:
            continue
        elif match_pd.shape[0] > 1:
            raise ValueError
        elif match_pd.shape[0] == 1:
            entity_id = match_pd.iloc[0]["entity_id"]
            article_x_entity = (
                article_id,
                entity_id,
                is_title,
            )

            article_x_entity_batch.append(article_x_entity)


def process_article(source_item):
    """

    :param source_item:
    :return:
    """

    # Insert article
    article_id = uuid4()
    article = (
        article_id,
        source_item[2],  # title
        source_item[4],  # plain_text
        source_item[3],  # date
        source_item[6],  # link
        SOURCE_SLUG_MAPPER_DATA[source_item[1]],  # source
        source_item[5],  # mapped genre
        RIMA_BASE_KEY,
        source_item[0],  # rima id
    )

    articles_batch.append(article)

    # Extract & insert title NER
    article_ner_data = extract_ner(source_item[2])
    process_article_ner(article_id, article_ner_data, is_title=True)

    # Extract & insert plain text NER
    article_ner_data = extract_ner(source_item[4])
    process_article_ner(article_id, article_ner_data, is_title=False)


if __name__ == "__main__":

    while len(SOURCE_SET):

        source = SOURCE_SET.pop()

        with SSHTunnelForwarder(
                (SSH_HOST, 22),
                ssh_private_key=SSH_PRIVATE_KEY,
                ssh_username=SSH_USERNAME,
                remote_bind_address=(SSH_BIND_ADDRESS, 5432),
        ) as ssh:
            ssh.start()

            params = POSTGRE_CONFIG.copy()
            params["port"] = ssh.local_bind_port
            params["dbname"] = "rima_de"
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()

            data = get_raw_data(source)

            connection.close()

            params["dbname"] = "rima_ext"
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()

            entities = execute_query(SELECT_ENTITIES_DICT_QUERY)
            entities_pd = pd.DataFrame(entities, columns=["entity_id", "tag", "name"])

            articles_batch = []
            article_x_entity_batch = []

            for item in data:
                try:
                    process_article(item)

                except Exception as e:
                    print(e)
                    print(item[0], item[1])

                if len(articles_batch) == 1000:
                    cursor.executemany(
                        INSERT_ARTICLE_QUERY,
                        articles_batch,
                    )

                    cursor.executemany(
                        INSERT_ARTICLE_X_ENTITY_QUERY,
                        article_x_entity_batch,
                    )

                    connection.commit()

                    articles_batch = []
                    article_x_entity_batch = []

            print(f"For source `{source}` {len(data)} items has been added")

            connection.close()
            ssh.stop()
