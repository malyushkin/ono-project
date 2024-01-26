SELECT_RAW_QUERY = """
SELECT * FROM {schema}.{table} 
WHERE source_slug='{s}' 
AND date_trunc('year', published_dt) = '{yaer}-01-01'"""

SELECT_RIMA_RAW_QUERY = """
SELECT pwc.id
     , pwc.source_slug
     , pwc.title
     , pwc.published_dt
     , pwc.plain_text
     , pwc.genre
     , cwu.url
FROM {schema}.{table} pwc
 JOIN crawled_web_url cwu ON cwu.id = pwc.crawled_web_url_id
WHERE date_trunc('year', pwc.published_dt) = '{year}-01-01'
  AND pwc.source_slug='{s}' 
  AND pwc.is_success;
"""

# _HELP_QUERY = "SELECT * FROM {table} WHERE source='Lenta.ru' AND title='Бывшая жена богатейшего человека мира на время стала богатейшей женщиной планеты'"

SELECT_SPEC_ENTITY_QUERY = "SELECT * FROM {schema}.{table} WHERE model='{m}' AND tag='{t}' AND name='{n}'"

SELECT_ENTITIES_DICT_QUERY = """
SELECT e.entity_id, e.tag, e.name
FROM ono.article_x_entity axe
         INNER JOIN ono.entity e ON e.entity_id = axe.entity_id
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 25
"""

# INSERT_ARTICLE_QUERY = "INSERT INTO ono.article(article_id, title, plain_text, published_dt, link_url, source_slug) VALUES(%s, %s, %s, %s, %s, %s);"
INSERT_ARTICLE_QUERY = """
INSERT INTO ono.article(article_id, title, plain_text, published_dt, link_url, source_slug, mapped_genre, base, base_article_id) 
VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);"""

INSERT_ARTICLE_X_ENTITY_QUERY = "INSERT INTO ono.article_x_entity(article_id, entity_id, is_title) VALUES(%s, %s, %s);"
INSERT_ENTITY_QUERY = """
INSERT INTO ono.entity(entity_id, model, tag, name) 
VALUES(%s, %s, %s, %s)
ON CONFLICT(model, tag, name)
DO UPDATE SET entity_id = %s;
"""