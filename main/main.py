import argparse
import json
import re
import sys

import pandas as pd
import psycopg2.extras
from uuid import uuid4

from pullenti_analyzer import PullentiAnalyzer

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--postgre-host", default="localhost")
parser.add_argument("-f", "--file", required=True, help="JSON file name")

args = parser.parse_args()
args_vars = vars(args)

PULLENTI_CONFIG = {
    "host": "localhost",
    "port": 8081,
}

POSTGRE_CONFIG = {
    "dbname": "ono_db",
    "user": "server",
    "password": "server",
    "host": args_vars["postgre_host"],
    "port": 5432
}

# sql queries
SEARCH_ARTICLE_SQL = "SELECT article_id FROM article WHERE rima_article_id={id};"
INSERT_ARTICLE_SQL = "INSERT INTO article(article_id, rima_article_id, title, plain_text, published_dt, source_slug) VALUES(%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;"
INSERT_ENTITY_SQL = "INSERT INTO entity(entity_id, tag, name) VALUES(%s, %s, %s);"
INSERT_ENTITY_ATTR_SQL = "INSERT INTO entity_attribute(entity_id, key, value) VALUES(%s, %s, %s);"
INSERT_ARTICLE_X_ENTITY_SQL = "INSERT INTO article_x_entity(article_id, entity_id, is_title) VALUES(%s, %s, %s);"

# db connection
psycopg2.extras.register_uuid()
connection = psycopg2.connect(**POSTGRE_CONFIG)
cursor = connection.cursor()


def join_str(e):
    name = []
    if "firstname" in e.keys():
        name.append(e.firstname)
    if "lastname" in e.keys():
        name.append(e.lastname)

    return " ".join(name)


def extend_name(text: str, pattern: str, check_name: str, add_name: str):
    news_by_words = text.split(" ")
    matches_by_words = [type(re.search(pattern, w)) for w in news_by_words]

    if re.Match not in matches_by_words:
        return text

    idx = matches_by_words.index(re.Match)

    if idx == 0:
        result = (re.search(check_name, news_by_words[idx + 1]))
    elif idx == len(news_by_words) - 1:
        result = (re.search(check_name, news_by_words[idx - 1]))
    else:
        result = (re.search(check_name, news_by_words[idx - 1]) or
                  re.search(check_name, news_by_words[idx + 1]))

    if not result:
        news_by_words.insert(idx, add_name)
        return " ".join(news_by_words)

    return text


def insert_ner(ner_data, is_title=False):
    for idx, row in ner_data.iterrows():
        entity_id = uuid4()
        entity_name = join_str(row) if row.tag == "PERSON" else row["name"]

        entity = (entity_id, row.tag, entity_name)
        cursor.execute(INSERT_ENTITY_SQL, entity)

        for k, v in row.items():
            if k not in ["name", "tag"] and type(v) != float:
                entity_attrs = (entity_id, k, v)
                cursor.execute(INSERT_ENTITY_ATTR_SQL, entity_attrs)

        article_x_entity = (article_id, entity_id, is_title)
        cursor.execute(INSERT_ARTICLE_X_ENTITY_SQL, article_x_entity)
        connection.commit()


# read source file
with open(args_vars["file"]) as f:
    json_data = json.load(f)

for article_item in json_data[:1]:

    cursor.execute(SEARCH_ARTICLE_SQL.format(id=article_item["rima_id"]))
    search = cursor.fetchone()

    if search:
        article_id = search[0]

    else:
        article_id = uuid4()
        article = (article_id,
                   article_item["rima_id"],
                   article_item["title"],
                   article_item["plain_text"],
                   article_item["published_dt"],
                   article_item["source_slug"])
        cursor.execute(INSERT_ARTICLE_SQL, article)
        connection.commit()

    # Title
    title_process = False
    if title_process:
        try:
            title = extend_name(article_item["title"], "Навальн", "Алекс", "Алексей")
            analyzer = PullentiAnalyzer(title, [], PULLENTI_CONFIG)
            ner_data: pd.DataFrame = pd.concat([
                analyzer.data("GEO"), analyzer.data("ORGANIZATION"), analyzer.data("PERSON")
            ])

            if ner_data.shape[0]:
                insert_ner(ner_data, True)

        except Exception as e:
            print(e)
            print(article_item["rima_id"], article_item["title"])
            connection.commit()

    # Content
    try:
        content = extend_name(article_item["plain_text"], "Навальн", "Алекс", "Алексей")
        analyzer = PullentiAnalyzer(content, [], PULLENTI_CONFIG)
        ner_data: pd.DataFrame = pd.concat([
            analyzer.data("GEO"), analyzer.data("ORGANIZATION"), analyzer.data("PERSON")
        ])

        if ner_data.shape[0]:
            insert_ner(ner_data, False)

    except Exception as e:
        print(e)
        print(article_item["rima_id"], "...")
        connection.commit()
