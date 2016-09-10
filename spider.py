# -*- coding: utf-8 -*-
import requests
import cookielib
import re
import urllib2
import MySQLdb
from bs4 import BeautifulSoup as BS
import logger
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class ZhiHu():

	def __init__(self):
	# Request headers
		agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
		host = 'www.zhihu.com'
		referer = 'https://www.zhihu.com/search?type=content&q=%E5%BC%A0%E6%B1%9F'
		# Change the last numbe to see the "more" questions
		self.url = "https://www.zhihu.com/r/search?q=%E5%BC%A0%E6%B1%9F&type=content&offset="
		self.logger = logger.Logger('log.txt', "zhlog").getlog()
		self.qtable = "zhihu_zj_q"
		self.atable = "zhihu_zj_a" 
		self.headers = {
		    'User-Agent': agent,
		   	'Host': host,
		   	'Referer': referer
		}

	def getHtml(self, url):
		logger = self.logger
		logger.info("Collecting data from page: " + url)
		html = urllib2.urlopen(url)
		content = html.read()
		return content

	def clean(self,item):
		#Delete the extra'\'
		item = re.sub(r'\\',"",item)
		#Delete the \n
		item = re.sub(r'\n',"",item)
		item.strip()
		return item

	def getQuestionUrls(self, html):
		url_pattern = re.compile('data-type=.*?Answer.*?href.*?"(.*?)" class.*?>', re.S)
		raw_urls = re.findall(url_pattern, html)
		urllist = []
		for raw_url in map(self.clean, raw_urls):
			urllist.append("https://www.zhihu.com" + raw_url)
		return urllist

	def savetomysql(self, table, data):
		try:
			db = MySQLdb.connect('localhost','root','891105','mysql')
			cur = db.cursor()
		except MySQLdb.Error, e:
			print "The error found in connnecting database%d: %s" % (e.args[0], e.args[1])
		try:
			db.set_character_set('utf8')
			cols = ', '.join(str(v) for v in data.keys())
			values = '"'+'","'.join(str(v) for v in data.values())+'"'
			sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, cols, values) #the primary key is photo_id
			# print sql
			try:
				result = cur.execute(sql)
				db.commit()
				#Check the result of command execution
				if result:
					print "This data is imported into database."
				else:
					return 0
			except MySQLdb.Error,e:
				 #rollback if error
				db.rollback()
				 #duplicate primary key
				if "key 'PRIMARY'" in e.args[1]:
					print "Data Existed"
				else:
					print "Insertion faied, reason is %d: %s" % (e.args[0], e.args[1])
		except MySQLdb.Error,e:
			print "Error found in database, reason is %d: %s" % (e.args[0], e.args[1])

	def getQuestionInfo(self, url):
		logger = self.logger
		qtable = self.qtable
		atable = self.atable
		logger.info("collecting data from question: " + url)
		# Get question id
		idmatch = re.search(re.compile('\d+'),url)
		q_id = idmatch.group(0)
		# Open url and read
		try:
			page = urllib2.urlopen(url)
		except Exception, e:
			logger.info('Fail to open page: '+url+" reason is "+str(e))
		content = page.read()
		soup = BS(content, 'lxml')
		# print soup.prettify()
		# Get information of question
		# Tags of question
		taglist = []
		tags = soup.find_all(class_='zm-item-tag')
		for tag in tags:
			taglist.append(self.clean(tag.text))
		# Title of question
		q_title = soup.find_all('span', class_='zm-editable-content')
		# print q_title[0].text

		# Content of question
		q_content = soup.find_all('div', class_='zm-editable-content')
		# print q_content[0].text

		# Number of answers
		try:
			no_ans = soup.find_all('h3')
			number = re.search(r'\d+', no_ans[0].text).group()
		except Exception, e:
			number = 1
		# print number

		info_question = {
					"question_id": q_id,
					"title":q_title[0].text,
					"tags": str(taglist).decode("unicode_escape"),
					"content": q_content[0].text,
					"number_ans":  number

		}
		self.savetomysql(qtable,info_question)
		print "finish question collection"

		# Get information of answerer
		answers = soup.find_all(class_ = 'zm-item-answer zm-item-expanded')
		print "start answer collection"
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
			# get votes
			voters = answer.find_all(class_='count')
			# print voters[0].text
			info_answer = {
							"answer_id":answer_id.group(1),
							"question_id":q_id,
							"author_name":name.group(1),
							"content":content,
							"votes": voters[0].text
			}
			self.savetomysql(atable, info_answer)
			print "finish one answer collection"
	def main(self):
		logger = self.logger
		number = 0
		StartCollection = True
		while StartCollection:
			url = self.url + str(number)
			# print url
			html = self.getHtml(url)
			# print html
			if "item clearfix" not in html:
				StartCollection = False
			else:
				urllist = self.getQuestionUrls(html)
				for q_url in urllist:
					self.getQuestionInfo(q_url)
			number += 10

test = ZhiHu()
test.main()
