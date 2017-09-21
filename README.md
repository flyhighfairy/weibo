# weibo
Crawl weibo comments under the mblogs of 38 domains @ sina weibo

# Prerequisite
* Create mysql database 'crawlerweb'
* Create tables 'crawled_weibov_mblogs' & 'crawled_weibov_comments' with SQL queries in crawlerweb.sql
* Modify settings.py, set DB_CONN_DICT according to your own database settings

# How to run?
* Open weibo project in PyCharm
* Mark weibo/weibo directory as Sources Root
* Open main.py, right click & select Run 'main'
