# -*- coding: utf-8 -*-
import requests
import cookielib
import re
import urllib2
from bs4 import BeautifulSoup as BS

class ZhiHu():

	def __init__(self):
	# Request headers
		agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
		host = 'www.zhihu.com'
		referer = 'https://www.zhihu.com/search?type=content&q=%E5%BC%A0%E6%B1%9F'
		self.headers = {
		    'User-Agent': agent,
		   	'Host': host,
		   	'Referer': referer
		}

	def getHtml(self):
		headers = self.headers
		session = requests.session()
		session.cookies = cookielib.LWPCookieJar(filename='cookies')
		r = session.get("https://www.zhihu.com/r/search?q=%E5%BC%A0%E6%B1%9F&type=content&offset=0", headers = headers)
		html = r.content
		return html

	def clean(item):
		#Delte the extra'\'
		item = re.sub(r'\\',"",item)
		return item

	def getQuestionUrls(self, html):
		url_pattern = re.compile('.*?item clearfix.*?href.*?"(.*?)" class.*?>', re.S)
		raw_urls = re.findall(url_pattern, html)
		urllist = []
		for raw_url in map(self.clean, raw_urls):
			urllist.append("https://www.zhihu.com" + raw_url)
		return urllist

	def getQuestionInfo(self, url):
		page = urllib2.urlopen(url)
		content = page.read()
		soup = BS(content, 'lxml')
		# print soup.prettify()
		# Get information of question
		# Tags of question
		tags = soup.find_all(class_='zm-item-tag')
		for tag in tags:
			print tag.text
		# Title of question
		q_title = soup.find_all('span', class_='zm-editable-content')
		print q_title[0].text
		# Content of question
		q_content = soup.find_all('div', class_='zm-editable-content')
		print q_content[0].text
		# Number of answers
		no_ans = soup.find_all('h3')
		number = re.search(r'\d+', no_ans[0].text).group()
		print number
		# Get information of answerer
		answers = soup.find_all(class_ = 'zm-item-answer zm-item-expanded')
		for answer in answers:
			# get answer id
			id_pattern = re.compile('content="(\d+)".*?answer-id', re.S)
			answer_id = re.search(id_pattern, str(answer))
			# get author name
			name_pattern = re.compile('data-author-name="(.*?)"', re.S)
			name = re.search(name_pattern,str(answer))
			# get the content of answer
			content = answer.find_all('div',class_='zm-editable-content clearfix')
			content = content[0].text



test = ZhiHu()
test.getQuestionInfo('https://www.zhihu.com/question/26611852')
