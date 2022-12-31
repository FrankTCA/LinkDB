import scrapy
from credentials import Credentials
import mysql.connector as mysql
from urllib.parse import urlparse, urljoin
import hashlib
from bs4 import BeautifulSoup
import re

class GlobalSpider(scrapy.Spider):
    name = 'global'
    start_urls = ['https://infotoast.org/site/index.php/2022/06/16/how-to-optimize-minecraft-1-19-for-m1/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conn = None
        try:
            self.conn = mysql.connect(host=Credentials.host,
                                 database=Credentials.database,
                                 user=Credentials.username,
                                 password=Credentials.password,
                                 auth_plugin='mysql_native_password')
            if self.conn.is_connected():
                self.log('Connected to MySQL Database!')
        except Exception as e:
            self.logger.error(e)

    def is_valid_url(self, url):
        regex = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url is not None and regex.search(url)

    def parse(self, response):
        #try:
            cursor = self.conn.cursor()
            body = str(response.body)
            url = str(response.url)
            self.logger.info(">> Crawling URL: " + url)
            u = urlparse(url)
            url_no_query = urljoin(url, urlparse(url).path)
            pre_hash = url_no_query + body
            page_md5 = hashlib.md5(pre_hash.encode()).hexdigest()
            cursor.execute("SELECT * FROM pages WHERE contents_md5 = %s", [page_md5])
            results = cursor.fetchall()
            for row in results:
                # Page already crawled
                return
            # First of all, verify the site label is even registered
            hostarr = u.hostname.split('.')
            top = hostarr.pop()
            maindomain = hostarr.pop()
            label = maindomain + '.' + top
            # Attempt to check and then insert
            cursor.execute("SELECT id FROM sitelabels WHERE domain_label = %s;", [label])
            results2 = cursor.fetchall()
            labelid = None
            for row in results2:
                labelid = results2[0]

            if labelid is None:
                cursor.execute("INSERT INTO sitelabels (domain_label) VALUES (%s);", [label])
                cursor.execute("SELECT id FROM sitelabels WHERE domain_label LIKE %s;", [label])
                resultslabelid = cursor.fetchall()
                for row in resultslabelid:
                    labelid = row[0]
                self.logger.info("> Registered new label with id " + str(labelid) + " and name " + label)

            # Now for subdomain
            subdomain = u.hostname
            if u.hostname == label:
                # Domain will be # if equal
                subdomain = '#.' + label

            cursor.execute("SELECT id FROM subdomains WHERE `domain` LIKE %s;", [subdomain])
            results3 = cursor.fetchall()
            subdomain_id = None
            for row in results3:
                subdomain_id = row[0]

            if subdomain_id is None:
                cursor.execute("INSERT INTO subdomains (label_id, `domain`) VALUES (%s, %s);", [labelid, subdomain])
                cursor.execute("SELECT id FROM subdomains WHERE `domain` LIKE %s;", [subdomain])
                resultssubdomainid = cursor.fetchall()
                for row in resultssubdomainid:
                    subdomain_id = row[0]
                self.logger.info("> Created new subdomain with id " + str(subdomain_id) + " and name " + subdomain)

            # Now, look and see if the url has been crawled. If so, it has been changed
            cursor.execute("SELECT id, content_changed FROM pages WHERE url LIKE %s", [url])
            results4 = cursor.fetchall()
            for row in results4:
                # There is at least one instance of changed content
                if row[1] == 0:
                    cursor.execute("UPDATE pages SET content_changed = 1 WHERE id = %s;", [row[0]])
            cursor.execute("INSERT INTO pages (subdomain_id, url, contents_md5) VALUES (%s, %s, %s);", [subdomain_id, url, page_md5])
            cursor.execute("SELECT id FROM pages WHERE contents_md5 LIKE %s;", [page_md5])
            resultspageid = cursor.fetchall()
            page_id = None
            for row in resultspageid:
                page_id = row[0]

            soup = BeautifulSoup(response.body, 'html.parser')
            for link in soup.find_all('a', href=True):
                if self.is_valid_url(link['href']):
                    href = link['href']
                    hrefurl = urlparse(href)
                    hostname1 = hrefurl.hostname
                    hostarr = hostname1.split('.')
                    hreftop = hostarr.pop()
                    hrefmain = hostarr.pop()
                    hreflabel = hrefmain + '.' + hreftop
                    hostname = hostname1
                    if hostname == hreflabel:
                        hostname = '#.' + hostname
                    cursor.execute("SELECT * FROM subdomains WHERE `domain` LIKE %s", [hostname])
                    resultshrefhostid = cursor.fetchall()
                    href_host_id = None
                    for row in resultshrefhostid:
                        href_host_id = row[0]

                    if href_host_id is None:
                        # Check if label exists
                        cursor.execute("SELECT * FROM sitelabels WHERE domain_label LIKE %s;", [hreflabel])
                        resultshreflabel = cursor.fetchall()
                        href_label_id = None
                        for row in resultshreflabel:
                            href_label_id = row[0]

                        if href_label_id is None:
                            self.logger.info("> Post-Creating new site label for " + hreflabel)
                            cursor.execute("INSERT INTO sitelabels (domain_label) VALUES (%s);", [hreflabel])
                            cursor.execute("SELECT id FROM sitelabels WHERE `domain_label` LIKE %s;", [hreflabel])
                            resultshreflabelid = cursor.fetchall()
                            for row in resultshreflabelid:
                                href_label_id = row[0]
                                self.logger.info("-> Created with name " + hreflabel + " and id " + str(href_label_id))
                        # Create new subdomain
                        self.logger.info("> Post-Creating new subdomain for " + hostname)
                        cursor.execute("INSERT INTO subdomains (label_id, `domain`) VALUES (%s, %s);", [href_label_id, hostname])
                        cursor.execute("SELECT id FROM subdomains WHERE `domain` LIKE %s;", [hostname])
                        resultshrefsubdomainid = cursor.fetchone()
                        href_host_id = resultshrefsubdomainid[0]
                        self.logger.info("-> Created with name " + hostname + " and id " + str(href_host_id))
                    # Hash the two urls so they are not mistaken for each other
                    pre_hash_href = url + href
                    href_composite_md5 = hashlib.md5(pre_hash_href.encode()).hexdigest()
                    cursor.execute("SELECT * FROM backlinks WHERE composite_md5 = %s;", [href_composite_md5])
                    resultscompositemd5 = cursor.fetchall()
                    docontinue = True
                    for row in resultscompositemd5:
                        yield scrapy.Request(href, callback=self.parse)
                        docontinue = False
                    if docontinue:
                        cursor.execute("INSERT INTO backlinks (subdomain_to, subdomain_from, url_to, url_from, from_page_id, composite_md5) VALUES (%s, %s, %s, %s, %s, %s);", [href_host_id, subdomain_id, href, url, page_id, href_composite_md5])
                        self.logger.info("Registered backlink from " + url + " to " + href)
                        yield scrapy.Request(href, callback=self.parse)
                else:
                    self.logger.debug(link['href'] + " is not a valid url")
            self.conn.commit()
            cursor.close()
        #except Exception as e:
         #   self.logger.error(e)
          #  return
