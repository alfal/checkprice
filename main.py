#coding=utf-8
__author__ = 'alfa'
import sqlite3
import os
import httplib2
import re
import json
import smtplib
import argparse
from datetime import datetime
import time
from email.mime.text import  MIMEText
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class CheckList:
    _sqlobj = ""
    _tablename = "productlist1"
    _priceobj = ""

    # 初始化
    def __init__(self):
        dbfile = sys.path[0] + "/productlist.db"
        if ( not os.path.exists(dbfile)):
            self._sqlobj = sqlite3.connect(dbfile)
            cu = self._sqlobj.cursor()
            cu.execute('CREATE TABLE '+self._tablename+' ( "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "site" text(20,0),"url" text(20,0),"title" text(20,0), "productid" varchar(20), "lowprice" integer, "email" varchar(100),"enddate" varchar(100),"status" integer not null default 0,"checktime" varchar(30),"nowprice" integer);')
            self._sqlobj.commit()
        else:
            self._sqlobj = sqlite3.connect(dbfile)

        self._priceobj = Price()

    #  析构函数
    def __del__(self):
        self._sqlobj.close()

    ### 新加一个列表
    def AddProduct(self,args):
        (site,title,productid) = self._priceobj.GetProductInfoByUrl(args.u)
        cu = self._sqlobj.cursor()
        cu.execute('insert into %s(site,url,title,productid,lowprice,email,enddate,status) values("%s","%s","%s","%s","%s","%s","%s",1)' % (self._tablename,site,args.u,title,productid,args.p,args.e,args.t))
        self._sqlobj.commit()
        print("Insert successed")

    ### 检测所有列表
    def CheckProduct(self,args):
        if(args.id == 0):
            where = " 1=1 "
        else:
            where = " id= " + args.id

        cu = self._sqlobj.cursor()
        cu.execute('select id,site,url,title,productid,lowprice,enddate,email,status from %s where status = 1 and %s' % (self._tablename,where))
        allproduct = cu.fetchall()

        for row in allproduct:
            nowprice = self._priceobj.GetNowPriceBySiteAndId(row[1],row[4])
            print ("Check Url:%s ==>> %s(%s)"%(row[2],nowprice,row[5]))
            status = 1
            if(nowprice<=row[5]):
                status = 2
                self._priceobj.SendMsg(row[7],row[1],row[2],row[3],nowprice,row[5])
            checkdate = time.strftime("%Y-%m-%d %X", time.localtime())
            if(checkdate > row[6]):
                status = 3
            cu.execute('update %s set nowprice="%s",checktime="%s",status="%s" where id = %s'%(self._tablename,nowprice,checkdate,status,row[0]))
            self._sqlobj.commit()



    ### 检测目前所有列表
    def ListProduct(self,args):
        cu = self._sqlobj.cursor()
        if(args.t !=0 ):
            where = " status = " + str(args.t)
        else:
            where = " 1=1 "
        cu.execute('select id,url,nowprice,lowprice,checktime,enddate,status from %s where %s' % (self._tablename,where))
        allproduct = cu.fetchall()
        print("ID\tURL\tprice(lowprice)\tchecktime(enddate)\tstatus")
        for row in allproduct:
            print('%s\t%s\t%s(%s)\t%s(%s)\t%s' %( row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

    ### 删除指定产品
    def DeleteProduct(self,args):
        cu=self._sqlobj.cursor()
        sql = "update %s set status=4 where id in (%s)"%(self._tablename,",".join([str(i) for i in args.id]))
        cu.execute(sql)
        print sql
        self._sqlobj.commit()
        print("delete finish")

    ### 清除所有已完成列表
    def ClearHistory(self):
        cu = self._sqlobj.cursor()
        cu.execute("delete from %s where status != 1"%(self._tablename))
        self._sqlobj.commit();
        print("clear finished")



class Price:

    def GetSiteByUrl(self,url):
        return "jd"

    ### 根据URL检测出产品ID、名称
    def GetProductInfoByUrl(self,url):
        site = self.GetSiteByUrl(url)
        if(site == "jd"):
            http = httplib2.Http(sys.path[0]+'/phttp.cache')
            (resp,content) = http.request(url)
            soup = BeautifulSoup(content,'html.parser')
            title = soup.h1.text
            productid = re.sub(".*/([0-9]*)\.html.*","\\1",url)
            return (site,title,productid)

    ### 根据网站和ID检测价格
    def GetNowPriceBySiteAndId(self,site,productid):
        if(site == "jd"):
            url='http://pm.3.cn/prices/pcpmgets?callback=jQuery2919828&skuids=' + productid + '&origin=2&source=1&area=1_72_2819_0&_=1453196782587'
            http = httplib2.Http(sys.path[0] + '/phttp.cache')
            (resp,content) = http.request(url)
            print(url)
            if(resp.status == 200):
                pattern = re.compile(r'jQuery2919828\(\[(.*)\]\);')
                productinfo = pattern.sub(r'\1',content)
                productarry = json.loads(productinfo) #['master']['name']
                nowprice = float(productarry['p'])

        return nowprice

    #### 发送信息
    def SendMsg(self,email,site,url,title,nowprice,lowprice):
        subject = site + " 上的 "+ title + ' 降价到了:' + str(nowprice)
        body = "您关注的 " + site + ' 上的商品 ' + title + " 降价到 " + str(nowprice) + "; \n" + " 达到了你的心里价位 " + str(lowprice) + "\n" + url + ""
        for mail in email.split(","):
            print("Send mail:%s =>> %s"%(url,email))
            self.SendMail(mail,subject ,body )
        return 0

    ### 发送邮件
    def SendMail(self,email,subject,content):
        mailconfhost = "smtp.qq.com"
        mailconfuser = "12345@qq.com"
        mailconfpass = "654321"
        mailconffrom = "alfa<12345@qq.com>"

        server = smtplib.SMTP()
        server.connect(mailconfhost)
        server.starttls()
        server.login(mailconfuser,mailconfpass)

        msg = MIMEText(content,"plain","utf-8")
        msg["From"] = mailconffrom
        msg["To"] = email
        msg["Subject"] = subject


        server.sendmail(mailconffrom,email,msg.as_string())
        server.quit()


if __name__ == "__main__" :

    checllistobj = CheckList()
    parser = argparse.ArgumentParser(description='Check price of JD')
    subparsers = parser.add_subparsers(help='sub-command help ')
    ### add product
    subparsers_add = subparsers.add_parser('add',help='add new product',description="add a new product ")
    subparsers_add.add_argument("-e",metavar="Email",help="Recieve message email")
    subparsers_add.add_argument("-u",metavar="Url",help="URL of JD")
    subparsers_add.add_argument("-p",metavar="Price",help="You Want price")
    subparsers_add.add_argument("-t",metavar="End date",help="End date")
    subparsers_add.set_defaults(func=checllistobj.AddProduct)


    ### check product
    subparsers_check = subparsers.add_parser("check",help='check price of all product',description="check the price of product")
    subparsers_check.add_argument("id",metavar="ID",help="Id of list(default:0,check all product)",default=0 ,type=int)
    subparsers_check.set_defaults(func=checllistobj.CheckProduct)

    ### list product
    subparsers_list = subparsers.add_parser("list",help='list all product ',description="list all product")
    subparsers_list.add_argument("-t",metavar="type",choices=xrange(0,5),help="status type of list (0/1/2/3/4=all/checking/finished/timeout/deleted)",default=0)
    subparsers_list.set_defaults(func=checllistobj.ListProduct)

    ### delete some product
    subparsers_delete = subparsers.add_parser("delete",help="Delete product",description='delete product')
    subparsers_delete.add_argument("id",metavar="ID",help="ids should delete",nargs='+',type=int)
    subparsers_delete.set_defaults(func=checllistobj.DeleteProduct)

    ### clean finished product
    subparsers_clear = subparsers.add_parser("clear",help='delete product data of finished or timeout from database ',description='delete product data of finished or timeout from database ')
    subparsers_clear.set_defaults(func=checllistobj.ClearHistory)


    args=parser.parse_args()
    args.func(args)


    exit(0)








