#coding=utf-8
import os
import csv
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def get_weibo_text():
    csv_files = [file_name for file_name in os.listdir('csv_weibo/')
                 if file_name.endswith('.csv') and '台风妮妲'.encode('gbk') in file_name]
    weibo_urls = []
    text_file = open('weibo_text.txt','w')
    for csv_file in csv_files:
        file = open('csv_weibo/' + csv_file)
        reader = csv.DictReader(file)
        for line in reader:
            text_file.write(line['微博内容'])
        file.close()
    text_file.close()

if __name__ == '__main__':
    get_weibo_text()