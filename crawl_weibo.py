#coding=utf-8
import hashlib
from datetime import datetime
from lxml import html
import cPickle as pickle
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import csv
import sys
import getpass
csv.field_size_limit(sys.maxsize)
reload(sys)
sys.setdefaultencoding('utf-8')

WEIBO_NAME = ''
WEIBO_PASSWORD = ''
WEIBO_USER = '阿文' #微博昵称，用于验证是否登录成功
MYSQL_USER='root'
MYSQL_PASSWORD='123456'
DATABASE='weibo'
ONE_MAIN_NUM = 40 #一个主页默认爬取的页数
ONE_URL_LOAD_TIME = 3 #一个url如果访问失败应该尝试的次数
PAGE_TIMEOUT = 20 #selenium默认的访问一个页面的超时时间（秒）
SAVE_TO_CSV = True

def login(driver,weibo_name,weibo_password):
    '''登录新浪通信证页面'''
    driver.get(r'https://login.sina.com.cn/signup/signin.php?entry=sso')
    user_name = driver.find_element_by_xpath('//*[@id="username"]')
    pass_word = driver.find_element_by_xpath('//*[@id="password"]')
    user_name.clear()
    pass_word.clear()
    user_name.send_keys(weibo_name)
    pass_word.send_keys(weibo_password)
    login = driver.find_element_by_xpath('//*[@class="btn_submit_m"]')
    login.click()
    time.sleep(10)
    if WEIBO_USER in driver.page_source or weibo_name in driver.page_source:
        print u'登陆成功'
        return True
    else:
        print u'登录失败'
        return False

def login_new(driver,weibo_name,weibo_password):
    '''登录新浪通信证页面'''
    # #先在命令行获取用户名和密码
    # WEIBO_NAME = raw_input("input weibo username:")
    # WEIBO_PASSWORD = getpass.getpass()

    driver.get(r'https://login.sina.com.cn/')
    user_name = driver.find_element_by_xpath('//*[@id="username"]')
    pass_word = driver.find_element_by_xpath('//*[@id="password"]')
    user_name.clear()
    pass_word.clear()
    user_name.send_keys(weibo_name)
    pass_word.send_keys(weibo_password)
    login = driver.find_element_by_xpath('//input[@class="smb_btn"]')
    login.click()
    time.sleep(5)
    if WEIBO_USER in driver.page_source or weibo_name in driver.page_source:
        print u'登陆成功'
        return True
    else:
        print u'登录失败'
        return False

def get_weibos_html(url,driver):
    '''打开微博主页，获取页面'''
    try:
        driver.get(url)
    except Exception as e:
        print e
        print "url loading time out: ",url
        return None
    #等待页面加载
    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'WB_info'))
        )
    except Exception, e:
        print Exception, ":", e
        print "content loading failed: ",url
        # print driver.page_source
        return None
    print u'页面加载成功'
    # 将页面滚动条拖到底部
    js = "window.scrollTo(0,50000)"
    driver.execute_script(js)
    time.sleep(5)
    driver.execute_script(js)
    time.sleep(5)
    return driver.page_source

def parse_weibo_items(res):
    '''解析一个微博页面的所有微博'''

    res_tree = html.fromstring(res)
    # weibos = res_tree.xpath('//*[@class="WB_cardwrap WB_feed_type S_bg2 "]')
    weibos = res_tree.xpath('//div[contains(@class,"WB_cardwrap WB_feed_type S_bg2")]')
    print len(weibos)
    weibo_items = []
    for weibo in weibos:
        weibo_item = {}
        try:

            publish_time = weibo.xpath('.//div[contains(@class, "WB_from")]/a[@date]/@date')[0]

            weibo_item['Publish_Time'] = datetime.fromtimestamp(float(publish_time) / 1000.0).strftime('%Y-%m-%d %H:%M:%S')

            weibo_item['weibo_URL'] = 'http://weibo.com' + weibo.xpath(
                './/div[contains(@class, "WB_from")]/a/@href')[0]

            weibo_item['Sina_Weibo_ID'] = hashlib.md5(weibo_item['weibo_URL']).hexdigest()
            weibo_item['Collect_Time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            weibo_item['weibo_Text'] = ''.join(weibo.xpath('.//div[contains(@class, "WB_text")]//text()')).replace("'",r"\'")

            pics = []
            for img in weibo.xpath('.//ul[@node-type="fl_pic_list"]//img/@src'):
            # for img in weibo.xpath('.//ul[@node-type="picChoose"]//img/@src'):
                pics.append(img.replace('sinaimg.cn/square/', 'sinaimg.cn/mw690/'))
            if not pics:
                pics = weibo.xpath('//div[@node-type="imgSpanBox"]/img[@node-type="imgShow"]/@src')

            weibo_item['Pic_URL_List'] = pics
            weibo_item['img'] = pics

            weibo_item['Publisher_Name'] = weibo.xpath(
                './/div[@class="WB_info"]/a/text()')[0].replace("'",r"\'")

            weibo_item['Publisher_Main_URL'] = weibo.xpath(
                './/div[contains(@class, "WB_info")]/a/@href')[0]
            rec_num = weibo.xpath(
                './/div[contains(@class, "WB_feed_handle")]/div[contains(@class, "WB_handle")]//span[@node-type="forward_btn_text"]/span/em[2]/text()')[0]
            if rec_num == '转发':
                weibo_item['Recommend_Number'] = 0
            else:
                weibo_item['Recommend_Number'] = rec_num
            com_num = weibo.xpath(
                './/div[contains(@class, "WB_feed_handle")]/div[contains(@class, "WB_handle")]//span[@node-type="comment_btn_text"]/span/em[2]/text()')[0]
            if com_num == '评论':
                weibo_item['Comment_Number'] = 0
            else:
                weibo_item['Comment_Number'] = com_num
            like_num = weibo.xpath(
                './/div[contains(@class, "WB_feed_handle")]/div[contains(@class, "WB_handle")]//span[@node-type="like_status"]/em[1]/text()')[0]
            if like_num == '赞':
                weibo_item['Like_Number'] = 0
            else:
                weibo_item['Like_Number'] = like_num
            weibo_items.append(weibo_item)
        except Exception as e:
            print e
            print weibo_item['weibo_URL']
    return weibo_items

def get_comments_html(driver,com_url):
    '''访问一个微博详细内容页面，获取该微博的所有评论'''
    try:
        driver.get(com_url)
    except Exception as e:
        print e
        print "page load fail:", com_url
    time.sleep(3)
    print com_url
    return driver.page_source

def parse_comments_items(com_html,weibo_id,com_url):
    '''解析一条微博的所有评论'''
    com_tree = html.fromstring(com_html)
    coms = com_tree.xpath('//*[@node-type="comment_list"]/div')
    com_items=[]
    for com in coms:
        try:
            comment_item = {}
            comment_item['Sina_Weibo_ID'] = weibo_id
            comment_item['weibo_URL'] = com_url

            comment_item['comment_id'] = com.xpath('./@comment_id')[0]

            comment_item['Commenter_Main_URL'] = 'http://weibo.com' + com.xpath(
                './/div[@class="WB_text"]/a[@usercard]/@href')[0]
            comment_item['Commenter_Name'] = com.xpath(
               './/div[@class="WB_text"]/a[@usercard]/text()')[0].replace("'",r"\'")

            comment_item['Comment_date'] = com.xpath(
                './/div[contains(@class, "WB_func")]/div[contains(@class, "WB_from")]/text()')[0]

            comment_text = ''.join(com.xpath('.//div[contains(@class, "WB_text")]//text()'))
            comment_item['Comment_Text'] = ''.join(comment_text).replace(comment_item['Commenter_Name'] + '：', '').replace("'",r"\'")
            com_items.append(comment_item)
        except Exception as e:
            print e
            print com_url
    return com_items

def save_weibos_to_mysql(weibo_items):
    '''保存微博到mysql'''
    import mysql.connector
    conn = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, database=DATABASE, use_unicode=True)
    cursor = conn.cursor()
    for weibo_item in weibo_items:
        try:
            cursor.execute("insert into weibos values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');"
                           % (weibo_item['Publish_Time'], weibo_item['weibo_URL'], weibo_item['Sina_Weibo_ID'],
                              weibo_item['weibo_Text'], '\t'.join(weibo_item['Pic_URL_List']), weibo_item['Publisher_Name'],
                              weibo_item['Publisher_Main_URL'], weibo_item['Collect_Time'], weibo_item['Recommend_Number'],
                              weibo_item['Comment_Number'], weibo_item['Like_Number']))
        except Exception as e:
            print e
    conn.commit()
    cursor.close()
    conn.close()

def save_comments_to_mysql(com_items):
    '''保存评论到mysql'''
    import mysql.connector
    conn = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, database=DATABASE, use_unicode=True)
    cursor = conn.cursor()
    for com_item in com_items:
        try:
            cursor.execute("insert into comments values('%s','%s','%s','%s','%s','%s','%s');"
                       % (com_item['Sina_Weibo_ID'], com_item['weibo_URL'], com_item['comment_id'],
                          com_item['Commenter_Main_URL'], com_item['Commenter_Name'], com_item['Comment_date'],
                          com_item['Comment_Text']))
        except Exception as e:
            print e
    conn.commit()
    cursor.close()
    conn.close()

def save_weibos_to_csv(weibo_items,index,csv_name=''):
    '''保存微博到csv'''
    if not os.path.exists('csv_weibo'):
        os.mkdir('csv_weibo')
    #默认保存的csv名称为"微博博主名_页面号.csv"
    if csv_name == '':
        filename = 'csv_weibo/'+weibo_items[0]['Publisher_Name']+'_'+str(index)+'.csv'
    else:
        filename = 'csv_weibo/'+csv_name+'_'+str(index)+'.csv'
    csv_file = file(filename, 'w')
    field_name = ["发布时间","微博url","微博id","微博内容",
                  "图片url","发布者名称","发布者主页url",
                  "爬取时间","转发个数","评论个数","点赞个数"]
    writer = csv.writer(csv_file)
    writer.writerow(field_name)
    for weibo_item in weibo_items:
        try:
            writer.writerow([
                weibo_item['Publish_Time'], weibo_item['weibo_URL'], weibo_item['Sina_Weibo_ID'],
                  weibo_item['weibo_Text'], '\t'.join(weibo_item['Pic_URL_List']), weibo_item['Publisher_Name'],
                  weibo_item['Publisher_Main_URL'], weibo_item['Collect_Time'], weibo_item['Recommend_Number'],
                  weibo_item['Comment_Number'], weibo_item['Like_Number']
                             ])
        except Exception as e:
            print e
    csv_file.close()

def save_comments_to_csv(com_items,csv_name):
    '''保存评论到csv'''
    if not os.path.exists('csv_comment'):
        os.mkdir('csv_comment')
    # 保存的csv名称为"微博博主名字.csv"
    filename = 'csv_comment/' + csv_name + '.csv'
    if not os.path.exists(filename):
        csv_file = file(filename, 'w')
        field_name = ["微博id", "微博url", "评论id", "评论者url",
                    "评论者名字", "评论时间", "评论内容"]
        writer = csv.writer(csv_file)
        writer.writerow(field_name)
    else:
        csv_file = file(filename, 'a')
        writer = csv.writer(csv_file)
    for com_item in com_items:
        try:
            writer.writerow([
                com_item['Sina_Weibo_ID'], com_item['weibo_URL'], com_item['comment_id'],
                  com_item['Commenter_Main_URL'], com_item['Commenter_Name'], com_item['Comment_date'],
                  com_item['Comment_Text']
            ])
        except Exception as e:
            print e
    csv_file.close()

def parse_page(final_urls): #暂时不用
    '''打开保存的每一页，进行解析,存入mysql'''
    for url in final_urls:
        with open('pkl/' + str(url) + '.pkl') as pkl_file:
            weibos_html = pickle.load(pkl_file)
            weibo_items= parse_weibo_items(weibos_html)
            save_weibos_to_mysql(weibo_items)

def crawl_comments_pages(driver,min_com_num,csv_name='',href_lack=True):
    import mysql.connector
    conn = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, database=DATABASE, use_unicode=True)
    cursor = conn.cursor()
    # cursor.execute("select Sina_Weibo_ID,weibo_URL from weibos")
    #选择今天刚加入的微博（而且评论数不为0），获取微博id、链接
    # cursor.execute('select Sina_Weibo_ID,weibo_URL,Publisher_Name from weibos where to_days(Collect_Time)=to_days(now()) and Comment_Number>={min_num};'.format(min_num=min_com_num))
    cursor.execute(
        'select Sina_Weibo_ID,weibo_URL,Publisher_Name from weibos where TO_DAYS( NOW( ) ) - TO_DAYS(Collect_Time) <= 1 and Comment_Number>={min_num};'.format(
            min_num=min_com_num))

    all_rec = cursor.fetchall()
    for rec in all_rec:
        if href_lack:
            com_html = get_comments_html(driver,rec[1])
        else:
            com_url = rec[1].replace('http://weibo.comh','h')
            com_html = get_comments_html(driver, com_url)
        com_items = parse_comments_items(com_html,rec[0],rec[1])
        pub_name = rec[2]
        save_comments_to_mysql(com_items)
        if SAVE_TO_CSV:
            if csv_name == '':
                save_comments_to_csv(com_items,pub_name)
            else:
                save_comments_to_csv(com_items,csv_name)
    cursor.close()
    conn.close()

def crawl_comments_pages_by_csv(driver,min_com_num,csv_name,href_lack=True):
    csv_files = [ file_name for file_name in os.listdir('csv_weibo/')
                  if file_name.endswith('.csv') and csv_name in file_name]
    weibo_urls = []
    if len(csv_files) == 0:
        print "no csv file ..."
        return
    for csv_file in csv_files:
        file = open('csv_weibo/'+csv_file)
        reader = csv.DictReader(file)
        for line in reader:
            if int(line['评论个数']) >= min_com_num:
                if href_lack:
                    weibo_url = line['微博url']
                else:
                    weibo_url = line['微博url'].replace('http://weibo.comh','h')
                com_html = get_comments_html(driver, weibo_url)
                com_items = parse_comments_items(com_html, line['微博id'], line['微博url'])
                pub_name = line['发布者名称']
                save_comments_to_mysql(com_items)
                if SAVE_TO_CSV:
                    if csv_name == '':
                        save_comments_to_csv(com_items, pub_name)
                    else:
                        save_comments_to_csv(com_items, csv_name)
        file.close()

def crawl_pages(urls,driver,csv_name='',start_num=0):
    '''获得一个主页的所有页面的内容'''
    # final_urls = []
    for index,url in enumerate(urls):
        for i in range(ONE_URL_LOAD_TIME):
            if i != 0:
                print "retry: ",url
            weibos_html = get_weibos_html(url, driver)
            if weibos_html != None:
                break
        #这里的else只会在break不执行的时候执行
        #也就是页面访问次数达到上限
        else:
            break
        weibo_items = parse_weibo_items(weibos_html)
        save_weibos_to_mysql(weibo_items)
        if SAVE_TO_CSV:
            save_weibos_to_csv(weibo_items,index+start_num,csv_name)

def crawl_one(url,driver):
    '''爬取一个主页的内容'''

    urls = [re.sub('page=\d', 'page=%d', url+"?is_search=0&visible=0&is_all=1&is_tag=0&profile_ftype=1&page=2#feedtop") % i for i in range(1, ONE_MAIN_NUM+1)]
    # crawl_pages(urls, driver) #获取一个主页的所有页面
    crawl_comments_pages(driver,10)

def crawl_all(driver):
    '''爬取所有主页的内容'''

    #所有微博主页的url
    main_urls = [
        'http://weibo.com/u/2015316631', #广东天气
        # 'http://weibo.com/u/2093990164',
        # 'http://weibo.com/zlinteriordesign',
        # 'http://weibo.com/shejishiclub',
        # 'http://weibo.com/deco365',
        # 'http://weibo.com/1234567xuanran',
        # 'http://weibo.com/zlinteriordesign',
        # 'http://weibo.com/to8tosjs',
        # 'http://weibo.com/idzoom',
        # 'http://weibo.com/zmqd',
        # 'http://weibo.com/u/2647081007',
        # 'http://weibo.com/u/1780801967',
        # 'http://weibo.com/u/2625738240',
        # 'http://weibo.com/lee8888888888',
        # 'http://weibo.com/u/3306279953',
        # 'http://weibo.com/starinfo',
        # 'http://weibo.com/u/2647993557',
        # 'http://weibo.com/u/1966380590',
    ]
    for url in main_urls:
        crawl_one(url,driver)

def main():
    # 先在命令行获取用户名和密码
    weibo_name = raw_input("input weibo username:")
    weibo_password = getpass.getpass()
    driver = webdriver.Firefox() #打开driver
    # driver = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chrome.exe')
    # driver = webdriver.PhantomJS(executable_path='F:/runtime/python/phantomjs-2.1.1-windows/bin/phantomjs.exe')
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    # is_login = login(driver) #首先模拟登陆
    is_login = login_new(driver,weibo_name,weibo_password)  # 首先模拟登陆
    if not is_login:
        return
    crawl_all(driver)

if __name__ == '__main__':
    main()
