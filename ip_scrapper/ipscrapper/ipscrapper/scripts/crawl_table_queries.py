# crawl_table_Select_query


IP_TABLE_SELECT_QUERY = 'SELECT sk, reference_url FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT 100;'

IP_TABLE_SELECT_QUERY_LIMIT = 'SELECT sk, reference_url FROM %s WHERE crawl_type="%s" AND crawl_status=0 AND content_type="%s" ORDER BY crawl_type DESC LIMIT %s;'

UPDATE_QUERY = 'UPDATE %s SET crawl_status=9, modified_at=NOW() WHERE crawl_type="%s" AND crawl_status=0 AND sk = "%s" AND content_type="%s";'

UPDATE_WITH_9_STATUS = 'UPDATE %s SET crawl_status=%s, modified_at=NOW() WHERE crawl_status=9 AND crawl_type="%s" AND sk="%s" AND content_type="%s";'

