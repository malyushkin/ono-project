SELECT_RAW_QUERY = """
SELECT * FROM {schema}.{table} 
WHERE source_slug='{s}' 
AND date_trunc('year', published_dt) = '2020-01-01'"""

# _HELP_QUERY = "SELECT * FROM {table} WHERE source='Lenta.ru' AND title='Бывшая жена богатейшего человека мира на время стала богатейшей женщиной планеты'"

SELECT_SPEC_ENTITY_QUERY = "SELECT * FROM {schema}.{table} WHERE model='{m}' AND tag='{t}' AND name='{n}'"

# INSERT_ARTICLE_QUERY = "INSERT INTO ono.article(article_id, title, plain_text, published_dt, link_url, source_slug) VALUES(%s, %s, %s, %s, %s, %s);"
INSERT_RIMA_ARTICLE_QUERY = """
INSERT INTO ono.article(article_id, title, plain_text, published_dt, link_url, source_slug, mapped_genre, base, base_article_id) 
VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);"""

INSERT_ENTITY_QUERY = "INSERT INTO ono.entity(entity_id, model, tag, name) VALUES(%s, %s, %s, %s);"
INSERT_ARTICLE_X_ENTITY_QUERY = "INSERT INTO ono.article_x_entity(article_id, entity_id, is_title) VALUES(%s, %s, %s);"
