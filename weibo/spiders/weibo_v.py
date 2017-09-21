# -*- coding: utf-8 -*-
import scrapy
from urllib import parse
import re
import json
import datetime
import logging
from w3lib.html import remove_tags

from items import WeiboVMblogsItem, WeiboVCommentsItem


class WeiboVSpider(scrapy.Spider):
    name = 'weibo_v'
    logger = logging.getLogger(name)
    allowed_domains = ['www.weibo.com', 'www.weibo.cn']
    start_urls = ['http://v6.bang.weibo.com/czv/domainlist?luicode=40000050/']
    headers = {
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Host": "m.weibo.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
    }
    mblog_pages = 2

    def input_process(self, value):
        value = remove_tags(value)
        value = value.replace("...全文", "")
        value = value.replace("\u200b", "")
        return value

    def extract_num(self, text, prefix=""):
        # 从字符串中提取出数字，可指定数字的前缀字符串
        match_re = re.match(".*%s?(\d+).*" % prefix, text)
        if match_re:
            nums = int(match_re.group(1))
        else:
            nums = 0
        return nums

    def extract_json(self, text):
        # 从字符串中提取出JSON
        match_re = re.match(".*?({.*}).*", text)
        if match_re:
            json_data = match_re.group(1)
        else:
            json_data = {}
        return json_data

    def parse(self, response):
        self.logger.debug('parse url: {0}'.format(response.url))
        domains = response.css('.clearfix>li>a')
        for domain in domains:
            domain_url = domain.css("::attr(href)").extract_first("")
            domain_name = domain.css("::text").extract_first("")
            next_url = parse.urljoin(response.url, domain_url)
            yield scrapy.Request(url=next_url, meta={"domain": domain_name}, dont_filter=True, callback=self.parse_domain)

    def parse_domain(self, response):
        self.logger.debug('parse_domain url: {0}'.format(response.url))
        domain = response.meta.get("domain", "")
        relink = '"uid":"(.*?)"'
        v_ids = re.findall(relink, response.text)
        for v_id in v_ids:
            next_url = "https://m.weibo.cn/api/container/getIndex?type=uid&value={0}&containerid=107603{1}".format(v_id, v_id)
            headers = self.headers
            headers.update({"Referer": "https://m.weibo.cn/u/{0}".format(v_id)})
            meta_dict = {"domain": domain, "uid": v_id}
            for i in range(self.mblog_pages):
                next_page_url = "{0}&page={1}".format(next_url, i+11)
                yield scrapy.Request(url=next_page_url, meta=meta_dict, headers=headers, dont_filter=True, callback=self.parse_mblog)

    def parse_mblog(self, response):
        self.logger.debug('parse_mblog url: {0}'.format(response.url))
        domain = response.meta.get("domain","")
        uid = response.meta.get("uid", "")
        json_data = json.loads(self.extract_json(response.text.strip()))

        if json_data["ok"]:
            for card in json_data["cards"]:
                if "mblog" in card:
                    item = WeiboVMblogsItem()
                    item["domain"] = domain
                    item["uid"] = uid
                    mblog_id = card["mblog"]["id"]
                    item["mblog_id"] = mblog_id
                    mblog_content = card["mblog"]["text"]
                    if "retweeted_status" in card["mblog"]:
                        retweeted_text = card["mblog"]["retweeted_status"]["text"]
                        mblog_content = "//".join([mblog_content, retweeted_text])
                    item["mblog_content"] = self.input_process(mblog_content)
                    item["created_time"] = card["mblog"]["created_at"]
                    item["crawled_time"] = datetime.datetime.now()
                    yield item

                    next_url = "https://m.weibo.cn/api/comments/show?id={0}&page=1".format(mblog_id)
                    headers = self.headers
                    headers.update({"Referer": "https://m.weibo.cn/status/{0}".format(mblog_id)})
                    yield scrapy.Request(url=next_url, headers=headers, dont_filter=True, callback=self.parse_comm)

    def parse_comm(self, response):
        self.logger.debug('parse_comm url: {0}'.format(response.url))
        page = self.extract_num(response.url, prefix="page=")
        mblog_id = self.extract_num(response.url, prefix="id=")
        json_data = json.loads(self.extract_json(response.text.strip()))

        if json_data["ok"]:
            for entry in json_data["data"]:
                content = remove_tags(entry["text"])
                if content:
                    item = WeiboVCommentsItem()
                    item["mblog_id"] = mblog_id
                    item["uid"] = entry["user"]["id"]
                    item["comment_id"] = entry["id"]
                    item["comment_content"] = remove_tags(entry["text"])
                    item["created_time"] = entry["created_at"]
                    item["crawled_time"] = datetime.datetime.now()
                    yield item
            next_url = response.url.replace("page={0}".format(page), "page={0}".format(page+1))
            headers = self.headers
            headers.update({"Referer": "https://m.weibo.cn/status/{0}".format(mblog_id)})
            yield scrapy.Request(url=next_url, headers=headers, dont_filter=True, callback=self.parse_comm)