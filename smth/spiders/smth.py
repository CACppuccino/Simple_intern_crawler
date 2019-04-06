import scrapy
import requests
import re
import redis
from scrapy.crawler import CrawlerProcess

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
job_smth_urls = []

class SmthSpider(scrapy.Spider):
    name = 'smth'
    allowed_domains = ['newsmth.net']
    start_urls = ['https://www.newsmth.net/nForum/board/Career_Campus']
    
    def parse(self, response):
        titles = response.xpath('//td/a/text()').extract()
        urls = response.xpath('//td/a/@href').extract()
        output = []
        max = 0
        for url in urls:
            if re.search(r'\/nForum/article/Career_Campus/[0-9]{6}$',url):
                num = int(re.search(r'[0-9]{6}$',url).group())
                if num > max:
                    max = num
        r.set('smth_job_id_max', max)
        if not r.exists('smth_job_id_current'):
            r.set('smth_job_id_current', max-100)


class SmthInfoSpider(scrapy.Spider):
    name = 'job_smth'
    allowed_domains = ['newsmth.net']
    start_urls = job_smth_urls 

    def __init__(self):
        max = int(r.get('smth_job_id_max'))
        current = int(r.get('smth_job_id_current'))
        for i in range(current, max):
            job_smth_urls.append('https://www.newsmth.net/nForum/article/Career_Campus/'+str(i))            
        print('init', job_smth_urls)
        r.set('smth_job_id_current', max)


    def parse(self, response):
        title = response.xpath('//title/text()').extract()[0]
        content = response.xpath('//td[@class="a-content"]').extract()[0]
        req = requests.post('https://lordvice.com/courses/interninfo/', data={'title':title, 'content':content,'other':'smth'})
        print('statuscode', req.status_code)
        print('============================')

class PkuSpider(scrapy.Spider):
    name = 'pku'
    allowed_domains = ['pku.edu.cn']
    url = 'https://bbs.pku.edu.cn/v2/thread.php?bid=896&mode=topic&page='
    url_head = 'https://bbs.pku.edu.cn/v2/'
    start_urls = []

    def __init__(self):
        for i in range(1,5):
            self.start_urls.append(self.url + str(i))
        print(self.start_urls)

    def parse(self, response):
        block = response.xpath('//div[@class="list-item-topic list-item"]')
        #firstpage = block[0].xpath('//div[@class="autho l"]/a[@class="link"]').extract()        
        if r.exists('pku_job_id_max'):
            jid_max = int(r.get('pku_job_id_max'))
        else:
            jid_max = 0
        job_list = []
        for b in block:
            #title = b.xpath('//div[@class="title l limit"]/text()').extract()
            link = self.url_head + b.xpath('a/@href').extract()[0]
            r.lpush('job_pku_urls', link)
            jid_max = jid_max + 1
        r.set('pku_job_id_max', jid_max)
        if not r.exists('pku_job_id_current'):
            r.set('pku_job_id_current', 0)


job_pku_urls = []

class PkuInfoSpider(scrapy.Spider):
    name = 'job_pku'
    allowed_domains = ['pku.edu.cn']

    def __init__(self):
        current = int(r.get('pku_job_id_current'))
        max = int(r.get('pku_job_id_max'))
        r.set('pku_job_id_current', max)
        self.start_urls = r.lrange('job_pku_urls', current, max)

    def parse(self, response):
        title =  response.xpath('//header/h3/text()').extract()[0]
        content = response.xpath('//div[@class="post-main"]/div[@class="content"]/div[@class="body file-read image-click-view"]')[0].extract()
        if '实习' in title or '招聘' in title:
            req = requests.post('https://lordvice.com/courses/interninfo/', data={'title':title, 'content':content, 'other':'pku'})
            print('statuscode', req.status_code)
            print('============================')
            
