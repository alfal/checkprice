# checkprice
检测商品价格

目前只支持检测京东商品

使用说明：

需要通过pip安装以下模块

pip install httplib2 argparse BeautifulSoup4

更改发送邮件的账号密码，只测试过用QQ的邮箱发送

- mailconfuser="12345@qq.com"
- mailconfpass="password"

使用方式

    python main.py 
    
    usage: main.py [-h] {clear,add,list,check,delete} ...
    
    main.py: error: too few arguments


添加商品：

    python main.py  add -e "112233@qq.com" -u "http://item.jd.com/1035733.html" -p 1000 -t "2018-01-01"
    
    在2018年1月1日之前如果http://item.jd.com/1035733.html的价格低于1000就给112233


检测商品价格：

    python main.py check 0 
    
    0代表检测所有商品，也可以为指定ID



查看当前在监测的商品

    python main.py list


不再监测某个商品：

    python main.py delete 1


清除缓存（所有失效的商品）：

    python main.py  clear


