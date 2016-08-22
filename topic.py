#coding=utf-8
import crawl_weibo as cw
import re
def crawl_topic(url):
    from selenium import webdriver
    driver = webdriver.Firefox()
    is_login = cw.login_new(driver)
    if not is_login:
        return
    urls = [re.sub('page=\d', 'page=%d',
                   url + "?page=1") % i for i in range(1, 25)]
    # cw.crawl_pages(urls, driver, csv_name = '台风妮妲',start_num=23)  # 获取一个主页的所有页面
    cw.crawl_comments_pages_by_csv(driver, 5, csv_name = '台风妮妲'.encode('gbk'),href_lack=False)
    driver.close()

if __name__ == '__main__':
    crawl_topic('http://weibo.com/p/1008083776f637dbbb811dd34a5e7d70b332d7')
