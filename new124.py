#-*-coding:utf-8 -*-

import re
import string
import sys
import os
import time
import urllib
import urllib2
import requests
from bs4 import BeautifulSoup
from lxml import etree
reload(sys)
sys.setdefaultencoding('utf-8')

requests.adapters.DEFAULT_RETRIES = 5
WEIBOFLAG = True
account1 = ['账号1', '密码1']
account2 = ['账号2', '密码2']

#user_id<type 'str'>
if (len(sys.argv) >= 2):
    usr_id = sys.argv[1]
    id_pool = []
    id_pool.append(usr_id)
else:
    #user_id = raw_input(u'plz input user_id')
    id_pool = [
                    '目标用户1id',
                    '目标用户2id',
                    '...'
                    ]

def get_cookie_from_network(name, pwd):
    from selenium import webdriver
    url_login = 'https://passport.weibo.cn/signin/login'
    driver = webdriver.PhantomJS()
    driver.set_page_load_timeout(5)
    driver.set_window_size(800, 600)
    driver.get(url_login)
    time.sleep(5)
    #发送用户名密码登录
    driver.find_element_by_xpath('//body/div[1]/form/section/div/p/input[@type="text"]').send_keys(name)
    driver.find_element_by_xpath('//input[@type="password"]').send_keys(pwd)
    driver.find_element_by_id('loginAction').click()

    cookie_list = driver.get_cookies()
    #print cookie_list
    driver.quit()
    cookie_dict = {}
    for cookie in cookie_list:
        if cookie.has_key('name') and cookie.has_key('value'):
            cookie_dict[cookie['name']] = cookie['value']
    return cookie_dict

def get_profile_pic(uid, user_id, cookie):
    url_photo_list_set = set()
    url_photo = 'https://weibo.cn/%s/photo' % uid
    with requests.Session() as s:
        s.keep_alive = False
        photo1 = s.get(url_photo, cookies = cookie).content
    soup1 = BeautifulSoup(photo1, "lxml")
    #print soup1.prettify()
    url_temp = soup1.find_all('a', href = re.compile(r'^/album/(\d)+', re.I))
    try:
        url2 = 'https://weibo.cn' + str(url_temp[-1]['href'])
    except:
        time.sleep(5)
        try:
            url2 = 'https://weibo.cn' + str(url_temp[-1]['href'])
        except Exception as e:
            print e
            return

    with requests.Session() as s:
        s.keep_alive = False
        profile_pic = s.get(url2, cookies = cookie).content
    selector2 = etree.HTML(profile_pic)
    try:
        pageNum2 = (int)(selector2.xpath('//input[@name="mp"]')[0].attrib['value'])
    except:
        pageNum2 = 1

    for page in range(1, pageNum2+1):
        url3 = '%s/?rl=11&page=%d' % (url2, page)
        with requests.Session() as s:
            s.keep_alive = False
            lxml2 = s.get(url3, cookies = cookie).content
        soup2 = BeautifulSoup(lxml2, "lxml")
        urllist1 = soup2.find_all('a', href = re.compile(r'^/album/(\d)+/photo/', re.I))
        for i in urllist1:
            imgurl = 'https://weibo.cn' + i['href']
            with requests.Session() as s:
                s.keep_alive = False
                #try
                lxml3 = s.get(imgurl, cookies = cookie).content
            soup3 = BeautifulSoup(lxml3, "lxml")
            urllist2 = soup3.find_all('a', href = re.compile(r'^http://\w\w\d.sinaimg.cn/large/', re.I))
            for imgurl2 in urllist2:
                with requests.Session() as s:
                    s.keep_alive = False
                    imgurl3 = s.get(imgurl2['href'], cookies = cookie)
                    url_photo_list_set.add(imgurl3.url) 

    if not url_photo_list_set:
        print u'profile_pic is not exit'
    else:
        image_path1 = os.getcwd() + '/%s/profile_pic'%user_id
        #if os.path.exists(image_path1) is False:
        os.mkdir(image_path1)
        x = 1
        for imgurl in url_photo_list_set:
            #temp = image_path1 + '%d.jpg' % x
            temp1 = image_path1 + '/%d.jpg' % x
            try:
                urllib.urlretrieve(urllib2.urlopen(imgurl).geturl(),temp1)
            except Exception,e:
                print e
                print u'downroad pic fail:%s' % imgurl
            x += 1

def get_weibo(html, user_id, cookie):
    global WEIBOFLAG
    selector = etree.HTML(html)
    try:
        pageNum = (int)(selector.xpath('//input[@name="mp"]')[0].attrib['value'])
    except:
        pageNum = 1


    result = ''
    urllist_set = set()
    word_count = 1
    image_count = 1

    print u'ready.....'
    print 'pageNum is %d' % pageNum
    test = 0
    for page in range(1, pageNum+1):
        test += 1
        print test
        url = 'https://weibo.cn/%s?filter=1&page=%d' % (user_id, page)
        try:
            with requests.Session() as s:
                s.keep_alive = False
                lxml1 = s.get(url, cookies = cookie).content
        except Exception as e1:
            print e1

        if lxml1 is '':
            print 'the content is empty'
            print url
            #time.sleep(20)

        try:
            selector = etree.HTML(lxml1)
            '''if test > 20:
                time.sleep(5)'''
        except Exception as e2:
            print e2
            print 'lxml1 is %s' % lxml1
            print 'failed to try again'
            WEIBOFLAG = not WEIBOFLAG
            break

        content = selector.xpath('//span[@class="ctt"]')
        print len(content)
        for each in content:
            text = each.xpath('string(.)')
            if word_count >= 4:
                text = "%d : "%(word_count - 3) + text + "\n\n"
            else:
                text = text + "\n\n"
            result = result + text
            word_count += 1

        soup = BeautifulSoup(lxml1, "lxml")

        urllist1 = soup.find_all('a', href = re.compile(r'^https://weibo.cn/mblog/picAll', re.I))
        if urllist1:
            try:
                for imgurl in urllist1:
                    with requests.Session() as s:
                        s.keep_alive = False
                        imgurl3 = s.get(imgurl['href'], cookies = cookie).content
                        soup1 = BeautifulSoup(imgurl3, 'lxml')
                        urllist2 = soup1.find_all('img', src = re.compile(r'^http://\w\w\d.sinaimg.cn/.+\.jpg', re.I))
                        for i in urllist2:
                            url3 = i['src']
                            pattern = re.search(r'(?<=http://\w\w\d.sinaimg.cn/)\w+(?=/)', url3).group(0)
                            z = url3.replace(pattern, 'large')
                            urllist_set.add(z)
            except Exception as e:
                print e

        urllist = soup.find_all('img', src = re.compile(r'^http://\w\w\d.sinaimg.cn/.+\.jpg', re.I))
        for imgurl in urllist:
            url4 = imgurl['src']
            pattern1 = re.search(r'(?<=http://\w\w\d.sinaimg.cn/)\w+(?=/)', url4).group(0)
            z1 = url4.replace(pattern1, 'large')
            urllist_set.add(z1)

    with open("./%s/%s.txt"%(user_id, user_id), 'ab') as fo:
        fo.write(result)
    word_path = os.getcwd() + '/%s'%user_id
    print u'weibo done'

    link = ""
    image_count = len(urllist_set)
    with open("./%s/%s_imageurls.txt"%(user_id, user_id), "ab") as fo2:
        print len(urllist_set)
        for eachlink in urllist_set:
            link = link + eachlink + "/n"
        fo2.write(link)
        print u'picture done'

    if not urllist_set:
        print u'pic is not exit'
        image_path = ''
    else:
        image_path = os.getcwd() + '/%s/weibo_image'%user_id
        #if os.path.exists(image_path) is False:
        os.mkdir(image_path)
        x = 1
        for imgurl in urllist_set:
            #temp = image_path + '%d.jpg' % x
            temp = image_path + '/%d.jpg' % x
            try:
                #urllib.urlretrieve(urllib2.urlopen(imgurl).geturl(),temp)
                res = requests.get(imgurl)
                with open(temp, 'ab') as fo1:
                    fo1.write(res.content)
            except Exception, e:
                print e
                print u'downroad pic fail:%s' % imgurl
            x += 1

    print u'weibo done %d, path:%s' % (word_count-4, word_path)
    print u'pic done %d, path:%s' % (image_count-1, image_path)

cookieX = get_cookie_from_network(account1[0], account1[1])
cookieY = get_cookie_from_network(account2[0], account2[1])
for t in range(0, len(id_pool)):
    user_id = id_pool[t] 
    if user_id not in os.listdir('.'):
        os.mkdir(str(user_id))
        url = 'https://weibo.cn/%s?filter=1&page=1' % user_id
        with requests.Session() as s:
            s.keep_alive = False
            #两个cookie交替使用
            if WEIBOFLAG is True:
                print 'c1'
                lxml = s.get(url, cookies = cookieX).content
            else:
                print 'c2'
                lxml = s.get(url, cookies = cookieY).content
        soup = BeautifulSoup(lxml, "lxml")
        uid_href = soup.find_all('a', href = re.compile(r'(?<=/attention/add\?uid=)\d+', re.I))
        uid = re.search(r'(?<=/attention/add\?uid=)\d+', uid_href[0]['href']).group(0)
        print uid
        if WEIBOFLAG is True:
            get_profile_pic(uid, user_id, cookieX)
            get_weibo(lxml, user_id, cookieX)
        else:
            get_profile_pic(uid, user_id, cookieY)
            get_weibo(lxml, user_id, cookieY)


        if len(id_pool) > 1:
            time.sleep(5)
    else:
        print 'exist'