import argparse
import sys
import psycopg2.extras

from typing import Any, Dict, List, Set
from uuid import uuid4

from ono.ner.natasha.client import NatashaClient, MODEL_NAME
from queries import (
    INSERT_ARTICLE_QUERY,
    INSERT_ENTITY_QUERY,
    INSERT_ARTICLE_X_ENTITY_QUERY,
    SELECT_ALL_QUERY,
    SELECT_SPEC_ENTITY_QUERY,
)
from ono.pipeline.config import (
    SOURCE_SLUG_MAPPER,
    SOURCE_STR,
)
from ono.pipeline.utils import source_slug_mapper_maker

parser = argparse.ArgumentParser()
parser.add_argument("--pg_host", default="localhost")
parser.add_argument("--pg_port", default="5432")
parser.add_argument("-f", "--file", required=False, help="JSON file name")
parser.add_argument("-s", "--source", required=False, default=SOURCE_STR)

args = parser.parse_args()
args_vars = vars(args)

POSTGRE_CONFIG = {
    "dbname": "ono_db",
    "user": "server",
    "password": "server",
    "host": args_vars["pg_host"],
    "port": args_vars["pg_port"]
}

SOURCE_SET = set(args_vars["source"].split(" "))
print(SOURCE_SET)
SOURCE_SLUG_MAPPER_DATA = source_slug_mapper_maker(SOURCE_SLUG_MAPPER)

psycopg2.extras.register_uuid()
connection = psycopg2.connect(**POSTGRE_CONFIG)
cursor = connection.cursor()


def get_raw_data(source_name) -> List:
    """
    Get postgres raw data by source name

    :param source_name:
    :return:
    """
    _query = SELECT_ALL_QUERY.format(
        table="archive_articles_master_export",
        s=source_name
    )
    cursor.execute(_query)

    return cursor.fetchall()


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
    :return:
    """
    for ner_item in ner_data:
        ner_name = ner_item[1].replace("'", "''")

        _params = {
            "table": "entity",
            "m": MODEL_NAME,
            "t": ner_item[0],
            "n": ner_name,
        }
        _query = SELECT_SPEC_ENTITY_QUERY.format(**_params)
        cursor.execute(_query)
        ner_db = cursor.fetchall()

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

            # print(entity)
            cursor.execute(INSERT_ENTITY_QUERY, entity)

        article_x_entity = (
            article_id,
            entity_id,
            is_title,
        )

        # print(article_x_entity)
        cursor.execute(INSERT_ARTICLE_X_ENTITY_QUERY, article_x_entity)


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

    cursor.execute(INSERT_ARTICLE_QUERY, article)
    connection.commit()

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
        # data = get_raw_data(source) TODO: remove
        data = get_raw_data(source)[:100]

        for item in data:
            try:
                process_article(item)

            except Exception as e:
                print(e)
                print(item[0], item[1])

        print(f"For source `{source}` {len(data)} items has been added")
