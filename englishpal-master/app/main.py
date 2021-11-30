#! /usr/bin/python3
# -*- coding: utf-8 -*-

###########################################################################
# Copyright 2019 (C) Hui Lan <hui.lan@cantab.net>
# Written permission must be obtained from the author for commercial uses.
###########################################################################

from WordFreq import WordFreq
from wordfreqCMD import youdao_link, sort_in_descending_order
from UseSqlite import InsertQuery, RecordQuery
import pickle_idea, pickle_idea2
import os
import random, glob
from datetime import datetime
from flask import Flask, request, redirect, render_template, url_for, session, abort, flash, get_flashed_messages
from difficulty import get_difficulty_level, text_difficulty_level, user_difficulty_level

#获取flask对象
app = Flask(__name__)
#设置秘钥（不知道什么意义）
app.secret_key = 'lunch.time!'
#意义不明的路径
path_prefix = '/var/www/wordfreq/wordfreq/'
#根目录
path_prefix = './' # comment this line in deployment


#随机取得图片（未能解释）
def get_random_image(path):
    #1.glob，python自带的一个文件操作相关模块，用它可以查找符合自己目的的文件，类似于Windows下的文件搜索，
    #支持通配符操作*,?,[]这三个通配符
    #2.glob.glob()，该方法返回所有匹配的文件路径列表（list）；该方法需要一个参数用来指定匹配的路径字符串
    #（字符串可以为绝对路径也可以为相对路径），其返回的文件名只包括当前目录里的文件名，不包括子文件夹里的文件。
    #3.os.path.join(path1[, path2[, ...]]) 	把目录和文件名合成一个路径
    #4.rfind() 返回字符串最后一次出现的位置，如果没有匹配项则返回 -1。

    #获取所有path路径下的图片？
    img_path = random.choice(glob.glob(os.path.join(path, '*.jpg')))
    #返回图片路径中从/static开始的内容？
    return img_path[img_path.rfind('/static'):]


#随机获得广告词
def get_random_ads():
    #广告词选项
    ads = random.choice(['个性化分析精准提升', '你的专有单词本', '智能捕捉阅读弱点，针对性提高你的阅读水平'])
    return ads


#获取文章总数
def total_number_of_essays():
    #创建查询类，写在UseSqlite.py中
    rq = RecordQuery(path_prefix + 'static/wordfreqapp.db')
    rq.instructions("SELECT * FROM article")
    rq.do()
    result = rq.get_results()
    return  len(result)


#读取？？历史
def load_freq_history(path):
    #1.os.path.exists(path) 如果路径 path 存在，返回 True；如果路径 path 不存在，返回 False。
    #2.pickle_idea中有pickle包，pickle模块实现了用于序列化和反序列化Python对象结构的二进制协议
    # “Pickling”是将Python对象层次结构转换为字节流的过程，
    # “unpickling”是反向操作，从而将字节流（来自二进制文件或类似字节的对象）转换回对象层次结构。

    d = {}
    #检测文件是否存在
    if os.path.exists(path):
        #把文件读取出来，返回字典d
        d = pickle_idea.load_record(path)
    return d


#验证用户
def verify_user(username, password):
    #创建查询类，写在UseSqlite.py中
    rq = RecordQuery(path_prefix + 'static/wordfreqapp.db')
    rq.instructions_with_parameters("SELECT * FROM user WHERE name=? AND password=?", (username, password))
    #方法名，带参执行的意思
    rq.do_with_parameters()
    result = rq.get_results()
    return result != []


#添加用户
def add_user(username, password):
    start_date = datetime.now().strftime('%Y%m%d')
    #到期时间，意义不明
    expiry_date = '20211230'
    rq = InsertQuery(path_prefix + 'static/wordfreqapp.db')
    rq.instructions("INSERT INTO user Values ('%s', '%s', '%s', '%s')" % (username, password, start_date, expiry_date))
    rq.do()


#检验用户名称可用性
def check_username_availability(username):
    rq = RecordQuery(path_prefix + 'static/wordfreqapp.db')
    rq.instructions("SELECT * FROM user WHERE name='%s'" % (username))
    rq.do()
    result = rq.get_results()
    return  result == []


#获取到期时间
def get_expiry_date(username):
    rq = RecordQuery(path_prefix + 'static/wordfreqapp.db')
    rq.instructions("SELECT expiry_date FROM user WHERE name='%s'" % (username))
    rq.do()
    result = rq.get_results()
    if len(result) > 0:
        #返回到期时间
        return  result[0]['expiry_date']
    else:
        #意义不明
        return '20191024'
    

#比较大小（意义不明）
def within_range(x, y, r):
    return x > y and abs(x - y) <= r 


#获取标题
def get_article_title(s):
    #分隔字符串，分隔成列表，然后取第一个
    return s.split('\n')[0]

#获取内容
def get_article_body(s):
    lst = s.split('\n')
    #移除第一行
    lst.pop(0)
    return '\n'.join(lst) 


#获取今天的文章
def get_today_article(user_word_list, articleID):

    rq = RecordQuery(path_prefix + 'static/wordfreqapp.db')
    if articleID == None:    
        rq.instructions("SELECT * FROM article")
    else:
        rq.instructions('SELECT * FROM article WHERE article_id=%d' % (articleID))
    rq.do()
    result = rq.get_results()
    #random.shuffle() 函数将序列中的元素随机打乱
    random.shuffle(result)
    
    #根据用户的水平选择文章？？？
    #读取频率？
    d1 = load_freq_history(path_prefix + 'static/frequency/frequency.p')
    #读取单词的等级
    d2 = load_freq_history(path_prefix + 'static/words_and_tests.p')
    #获得文章中每个单词的等级
    d3 = get_difficulty_level(d1, d2)

    d = {}
    d_user = load_freq_history(user_word_list)
    #根据某种算法算得用户等级
    user_level = user_difficulty_level(d_user, d3) # more consideration as user's behaviour is dynamic. Time factor should be considered.

    #这一段是为什么？
    random.shuffle(result) # shuffle list
    d = random.choice(result)
    text_level = text_difficulty_level(d['text'], d3)

    #如果没有选出文章（什么地方已经选了文章？）
    if articleID == None:
        for reading in result:
            text_level = text_difficulty_level(reading['text'], d3)
            #random.guass()返回具有高斯分布的随机浮点数
            factor = random.gauss(0.8, 0.1) # a number drawn from Gaussian distribution with a mean of 0.8 and a stand deviation of 1
            #用到了上面的意义不明的算法
            if within_range(text_level, user_level, (8.0 - user_level)*factor):
                d = reading
                break


    article_title = get_article_title(d['text'])
    article_body = get_article_body(d['text'])
    article = {"user_level": user_level, "text_level": text_level, "data": d['date'], "article_title": article_title,
               "article_body": article_body, "soure": d['source'], "question": get_question_part(d['question']),
               "answer": get_answer_part(d['question'])}
    session['articleID'] = d['article_id']
    return article

#还不懂
def appears_in_test(word, d):
    if not word in d:
        return ''
    else:
        return ','.join(d[word])

#获取时间
def get_time():
    return datetime.now().strftime('%Y%m%d%H%M') # upper to minutes

#获取问题？
def get_question_part(s):
    s = s.strip()
    result = []
    flag = 0
    for line in s.split('\n'):
        line = line.strip()
        if line == 'QUESTION':
            result.append(line)
            flag = 1
        elif line == 'ANSWER':
            flag = 0
        elif flag == 1:
            result.append(line)
    return result

#获取答案？
def get_answer_part(s):
    s = s.strip()
    result = []
    flag = 0
    for line in s.split('\n'):
        line = line.strip()
        if line == 'ANSWER':
            flag = 1
        elif flag == 1:
            result.append(line)
    # https://css-tricks.com/snippets/javascript/showhide-element/

    result = "".join(result)
    return result

#获取闪现信息未被使用过
def get_flashed_messages_if_any():
    #get_flashed_messages() 方法：
    #返回之前在Flask中通过 flash() 传入的闪现信息列表。
    #把字符串对象表示的消息加入到一个消息队列中，然后通过调用 get_flashed_messages() 方法取出
    #(闪现信息只能取出一次，取出后闪现信息会被清空)。
    messages = get_flashed_messages()
    s = ''
    for message in messages:
        s += '<div class="alert alert-warning" role="alert">'
        s += f'Congratulations! {message}'
        s += '</div>'
    return s

#重置用户
@app.route("/<username>/reset", methods=['GET', 'POST'])
def user_reset(username):
    #此处request是包名，但与传统意义上的request相同（session同理）
    if request.method == 'GET':
        session['articleID'] = None
        #url_for()函数是用于构建指定函数的URL，而且url_for操作对象是函数，而不是route里的路径。
        return redirect(url_for('userpage', username=username))
    else:
        return 'Under construction'


@app.route("/mark", methods=['GET', 'POST'])
def mark_word():
    if request.method == 'POST':
        d = load_freq_history(path_prefix + 'static/frequency/frequency.p')
        lst_history = pickle_idea.dict2lst(d)
        lst = []
        for word in request.form.getlist('marked'):
            lst.append((word, 1))
        d = pickle_idea.merge_frequency(lst, lst_history)
        pickle_idea.save_frequency_to_pickle(d, path_prefix + 'static/frequency/frequency.p')
        return redirect(url_for('mainpage'))
    else:
        return 'Under construction'



@app.route("/", methods=['GET', 'POST'])
def mainpage():
    #用POST方法获取主页--mainpage_post.html
    if request.method == 'POST':  # when we submit a form
        content = request.form['content']
        f = WordFreq(content)
        lst = f.get_freq()

        # save history 
        d = load_freq_history(path_prefix + 'static/frequency/frequency.p')
        lst_history = pickle_idea.dict2lst(d)
        d = pickle_idea.merge_frequency(lst, lst_history)
        pickle_idea.save_frequency_to_pickle(d, path_prefix + 'static/frequency/frequency.p')

        return render_template("mainpage_post.html",lst = lst)
    #用GET方法获取主页--mainpage_get.html
    elif request.method == 'GET': # when we load a html page

        #获取过去的记录？
        d = load_freq_history(path_prefix + 'static/frequency/frequency.p')
        des_ord = sort_in_descending_order(pickle_idea.dict2lst(d))
        #把需要的内容都保存到一个列表中，youdao_link(x[0])，x[0]，x[1]
        you_list = []
        for x in des_ord:
            if x[1] <= 99:
                break
            you_list.append({"link":youdao_link(x[0]),"x":x[0],"y":x[1]})
        #文章总数
        num = total_number_of_essays()
        #随机广告
        ads = get_random_ads()
        lend = len(d)
        #返回到前端mainpage_get.html
        return render_template("mainpage_get.html",
                               d = d,
                               ads = ads,
                               num = num,
                               you_list = you_list,
                               lend = lend)


@app.route("/<username>/mark", methods=['GET', 'POST'])
def user_mark_word(username):
    username = session[username]
    user_freq_record = path_prefix + 'static/frequency/' +  'frequency_%s.pickle' % (username)
    if request.method == 'POST':
        d = load_freq_history(user_freq_record)
        lst_history = pickle_idea2.dict2lst(d)
        lst = []
        for word in request.form.getlist('marked'):
            lst.append((word, [get_time()]))
        d = pickle_idea2.merge_frequency(lst, lst_history)
        pickle_idea2.save_frequency_to_pickle(d, user_freq_record)
        return redirect(url_for('userpage', username=username))
    else:
        return 'Under construction'

#不熟悉调用这个
@app.route("/<username>/<word>/unfamiliar", methods=['GET', 'POST'])
def unfamiliar(username,word):
    user_freq_record = path_prefix + 'static/frequency/' + 'frequency_%s.pickle' % (username)
    pickle_idea.unfamiliar(user_freq_record,word)
    session['thisWord'] = word  # 1. put a word into session
    session['time'] = 1
    return redirect(url_for('userpage', username=username))


#熟悉调用这个
@app.route("/<username>/<word>/familiar", methods=['GET', 'POST'])
def familiar(username,word):
    user_freq_record = path_prefix + 'static/frequency/' + 'frequency_%s.pickle' % (username)
    pickle_idea.familiar(user_freq_record,word)
    session['thisWord'] = word  # 1. put a word into session
    session['time'] = 1
    return redirect(url_for('userpage', username=username))


#删除单词
@app.route("/<username>/<word>/del", methods=['GET', 'POST'])
def deleteword(username,word):
    user_freq_record = path_prefix + 'static/frequency/' + 'frequency_%s.pickle' % (username)
    pickle_idea2.deleteRecord(user_freq_record,word)
    flash(f'<strong>{word}</strong> is no longer in your word list.')
    return redirect(url_for('userpage', username=username))

#用户主页
@app.route("/<username>", methods=['GET', 'POST'])
def userpage(username):

    #检查是否已经登录--login_first.html
    if not session.get('logged_in'):
        return render_template("login_first.html")

    #检查用户是否过期--over_expiry.html
    user_expiry_date = session.get('expiry_date')
    if datetime.now().strftime('%Y%m%d') > user_expiry_date:
        '''
        此处应有html代码，不过被我删了
        '''
        return render_template("over_expiry.html",username = username)

    
    username = session.get('username')

    user_freq_record = path_prefix + 'static/frequency/' +  'frequency_%s.pickle' % (username)

    #显示已经选取的生词--check_unknow_post.html
    if request.method == 'POST':  # when we submit a form
        content = request.form['content']
        f = WordFreq(content)
        lst = f.get_freq()

        count = 1
        words_tests_dict = pickle_idea.load_record(path_prefix + 'static/words_and_tests.p')
        you_list=[]
        for x in lst:

            you_list.append(
                {"count": count, "link": youdao_link(x[0]), "appear": appears_in_test(x[0], words_tests_dict),
                 "x0": x[0], "x1": x[1]})
            count += 1

        return render_template("check_unknow_post.html", you_list = you_list,username = username)
    #在没有未知单词的时候？check_unknow_get.html
    elif request.method == 'GET': # when we load a html page
        '''
        此次应该有前端代码，不过被我删了，太烦了,后面同理
        '''
        d = load_freq_history(user_freq_record)

        des_ord = []
        if len(d) > 0:
            lst = pickle_idea2.dict2lst(d)
            lst2 = []
            for t in lst:
                lst2.append((t[0], len(t[1])))


            #创建一个用来传值的容器

            count = 0
            for x in sort_in_descending_order(lst2):
                des_ord.append({"sessioncheck":True,"wlist":True,"you_link":None,"word":None,"jword":None,"freq":None,"username":None})
                word = x[0]
                freq = x[1]
                #用sessioncheck来保存信息
                if session.get('thisWord') == x[0] and session.get('time') == 1:
                    session['time'] = 0   # discard anchor
                else:
                    des_ord[count]["sessioncheck"] = False

                #用wlist来保存信息
                if isinstance(d[word], list): # d[word] is a list of dates
                    des_ord[count]["you_link"] = youdao_link(word)
                    des_ord[count]["word"] = word
                    des_ord[count]["jword"] = '; '.join(d[word])
                    des_ord[count]["freq"] = freq
                    des_ord[count]["username"] = username
                elif isinstance(d[word], int): # d[word] is a frequency. to migrate from old format.
                    des_ord[count]["wlist"] = False
                    des_ord[count]["you_link"] = youdao_link(word)
                    des_ord[count]["word"] = word
                    des_ord[count]["freq"] = freq

                count +=1

        return render_template("check_unknow_get.html",
                               lend = len(d),
                               username = username,
                               article = get_today_article(user_freq_record, session['articleID']),
                               des_ord = des_ord
                               )

### Sign-up, login, logout ###
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        available = check_username_availability(username)
        if not available:
            flash('用户名 %s 已经被注册。' % (username))
            return render_template('signup.html')
        elif len(password.strip()) < 4:
            return '密码过于简单。'
        else:
            add_user(username, password)
            verified = verify_user(username, password)
            if verified:
                session['logged_in'] = True
                session[username] = username
                session['username'] = username
                session['expiry_date'] = get_expiry_date(username)
                session['articleID'] = None
                return render_template("congratulations_registration.html", username = username)
            else:
                return "用户名密码验证失败。"


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if not session.get('logged_in'):
            return render_template('login.html')
        else:
            return '你已登录 <a href="/%s">%s</a>。 登出点击<a href="/logout">这里</a>。' % (session['username'], session['username'])
    elif request.method == 'POST':
        # check database and verify user
        username = request.form['username']
        password = request.form['password']
        verified = verify_user(username, password)
        if verified:
            session['logged_in'] = True
            session[username] = username
            session['username'] = username
            user_expiry_date = get_expiry_date(username)
            session['expiry_date'] = user_expiry_date
            session['articleID'] = None
            return redirect(url_for('userpage', username=username))
        else:
            return '无法通过验证。'


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('mainpage'))


if __name__ == '__main__':
    #app.secret_key = os.urandom(16)
    #app.run(debug=False, port='6000')
    app.run(debug=True)        
    #app.run(debug=True, port='6000')
    #app.run(host='0.0.0.0', debug=True, port='6000')
