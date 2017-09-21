# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WeiboVMblogsItem(scrapy.Item):
    domain = scrapy.Field()
    uid = scrapy.Field()
    mblog_id = scrapy.Field()
    mblog_content = scrapy.Field()
    created_time = scrapy.Field()
    crawled_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into crawled_weibov_mblogs(domain, uid, mblog_id, mblog_content, created_time, crawled_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        params = (self["domain"], self["uid"], self["mblog_id"], self["mblog_content"], self["created_time"], self["crawled_time"])

        return insert_sql, params


class WeiboVCommentsItem(scrapy.Item):
    mblog_id = scrapy.Field()
    uid = scrapy.Field()
    comment_id = scrapy.Field()
    comment_content = scrapy.Field()
    created_time = scrapy.Field()
    crawled_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into crawled_weibov_comments(mblog_id, uid, comment_id, comment_content, created_time, crawled_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        params = (self["mblog_id"], self["uid"], self["comment_id"], self["comment_content"], self["created_time"], self["crawled_time"])

        return insert_sql, params