# -*- coding: utf-8 -*-

from flask.ext.oauthlib.client import OAuthException

from flask.ext.login import login_user, logout_user, current_user, login_required

from flask import render_template, request, redirect, url_for, flash, session, g

from sqlalchemy import desc

from apps import app, db, login_manager, facebook

from core import variables, OAuthManagement

import pusher

import google.appengine.ext as google 

class Photo(google.db.Model):
    photo = google.db.BlobProperty()

from apps.models import (User, Comment, Log, Group, Project, Member)


@login_manager.unauthorized_handler
def unauthorized():
    flash(u"로그인이 필요합니다.", "warning")
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user




@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login/login.html')

#
# @OAuth login management
#

@app.route('/login/facebook/')
def login_facebook():
    callback = url_for(
        'facebook_authorized',
        _external=True
    )
    return facebook.authorize(callback=callback)


@app.route('/login/facebook/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        flash(u"로그인 인증에 실패하였습니다.", "error")
        return redirect(url_for('login'))

    session['oauth_token'] = (resp['access_token'], '')

    userinfo = facebook.get('/me')

    # return userinfo.data['id']
    # return str(userinfo.data)

    register_result = OAuthManagement.OAuth2RegisterToUser(userinfo.data, 'FACEBOOK')

    return OAuthManagement.OAuthRegisterAndLoginRedirect(register_result)


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    OAuthManagement.OAuthSessionPop()
    return redirect(url_for('login'))



# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         user_id = request.form['user_id']
        
#         # login success
#         session.permanent = True
#         session['user_id'] = user_id

#         return redirect(url_for('main'))

#     users = User.query.all()

#     return render_template('login/login.html', users=users)


# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))


# @app.route('/join', methods=['GET', 'POST'])
# def join():
#     # 인증 아직 없음..
#     if request.method == 'POST':
#         user_id = request.form['user_id']
#         pw = request.form['pw']
#         name = request.form['name']

#         user = User(
#                 id = user_id,
#                 password = pw,
#                 name = name,
#             )

#         db.session.add(user)
#         db.session.commit()

#         flash('join success!','success')

#         return redirect(url_for('login'))

#     # 유저 확인 위해 임시로 넣어놓은 코드
#     users = User.query.all()

#     return render_template('join/join.html', users = users)


@app.route('/main')
def main():
    
    projects = Project.query.all()

    # result = ''
    # for project in projects:
    #     result += str(project.id) + " : "
    #     for member in project.members:
    #         result += member.user_id
    #     result += '<br>'
    # return result;

    return render_template('main/main.html', projects=projects)


@app.route('/my_project')
def my_project():
    # 유저 정보로.. 
    user = User.query.get(g.user.id)

    # 유저가 만든 프로젝트 정보
    projects = user.projects

    # 유저가 초대된 프로젝트 정보도..
    members = user.members

    return render_template('main/main.html', is_mine=True , projects=projects, members=members)

@app.route('/delete_project', methods=['GET', 'POST'] )
def delete_project():

    if request.method == 'POST':
        project_id = request.form['project_id']
        project = Project.query.get(project_id)
        db.session.delete(project)
        db.session.commit()

        flash('delete success', 'success')

    # 유저 정보로.. 
    user = User.query.get(g.user.id)
    projects = user.projects

    return render_template('delete_project/delete_project.html' , projects=projects)


@app.route('/project_detail/<proj_id>')
def project_detail(proj_id):
    project = Project.query.get(proj_id)

    #최신순 이거 야매아니야...?
    # logs = project.logs.reverse()

    #filter로 하면 안된다.
    logs = Log.query.order_by(desc(Log.date_created)).filter_by(project_id=proj_id)

    list_string = "";
    if project.schedule:  
        list_string = project.schedule

    list_item = list_string.split('*&*')
    list_item.pop()

    return render_template('project_detail/project_detail.html', project=project , logs=logs, list_item=list_item)

@app.route('/statistics/<proj_id>')
def statistics(proj_id):

    project = Project.query.get(proj_id)

    return render_template('statistics/statistics.html', project= project)

@app.route('/add_member_to/<proj_id>', methods=['GET', 'POST'])
def add_member_to(proj_id):

    if request.method == 'POST':
        user_id = request.form['user_id']
        user = User.query.get(user_id)

        project = Project.query.get(proj_id)

        #원랜 다 안써도 되지 않나? 자동으로 채워주는 부분이 어디까진지 몰라서 다쓴다.
        member = Member(
                user = user,
                user_id = user_id,
                project = project,
                project_id = proj_id,
            )
        db.session.add(member)
        db.session.commit()

        flash('add success!','success')

        return redirect(url_for('project_detail', proj_id=proj_id))

    users = User.query.all()

    return render_template('add_member/add_member.html', users= users)



@app.route('/test', methods=['GET', 'POST'])
def test():

    group_list = []
    user_list = []

    if request.method == 'POST':
        if request.form['hidden_val'] == 'test1':
            user_id = request.form['user_id']

            user = User.query.get(user_id)

            users_comments = user.comments

            # return users_comments[0].content

            for comment in users_comments:
                group_list.append(comment.log.project.groups[0].title)
                group_list.append(comment.log.project.groups[1].title)
                group_list.append(comment.log.project.groups[2].title)

            group_list = set(group_list)

        elif request.form['hidden_val'] == 'test2':
            project_id = request.form['project_id']

            project = Project.query.get(project_id)

            for log in project.logs:
                for comment in log.comments:
                    if comment.user_id not in user_list:
                        user_list.append(comment.user_id)


    users = User.query.all()
    projects = Project.query.all()

    return render_template('test/test.html', users = users, group_list=group_list, projects=projects, user_list=user_list)

@app.route('/time_line', methods=['GET'])
def time_line():
    
    logs = Log.query.order_by(desc(Log.date_created)).filter_by(user_id=g.user.id)

    return render_template('time_line/time_line.html', logs=logs)


@app.route('/create_project', methods=['GET', 'POST'])
def create_project():

    if 'user_id' not in session:
        return '로그인 안됐음'

    if request.method == 'POST':
        project_name = request.form['project_name']
        project_desc = request.form['project_desc']

        # 여기서 그룹은 쓸대 없는 짓하고 있는거임..?
        g1 = request.form['group1']
        c1 = request.form['category1']

        g2 = request.form['group2']
        c2 = request.form['category2']

        g3 = request.form['group3']
        c3 = request.form['category3']

        
        # file 저장
        file_key = None
        if request.files['photo']:
            post_data = request.files['photo']
            filestream = post_data.read()
            upload_data = Photo()
            upload_data.photo = google.db.Blob(filestream)
            upload_data.put()
            file_key = str(upload_data.key())


        # 현재 로그인 한 사람의 아이디를 저장한다. 프로젝트 생성자로
        user = User.query.get(g.user.id)

        proj = Project(
                title = project_name,
                description = project_desc,
                file_key = file_key,
                user_id = g.user.id,
                user = user,
            )

        g1 = Group(
                project = proj,
                title = c1,
            )
        g2 = Group(
                project = proj,
                title = c2,
            )

        g3 = Group(
                project = proj,
                title = c3,
            )


        db.session.add(proj)
        db.session.add(g1)
        db.session.add(g2)
        db.session.add(g3)
        db.session.commit()

        flash('create project success','success')

        return redirect(url_for('my_project'))

    projects = Project.query.all()
       
    return render_template('create_project/create_project.html', projects = projects)
    


@app.route('/make_log/<project_id>', methods=['GET', 'POST'])
def make_log(project_id):

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        # file 저장

        file_key = None
        if request.files['photo']:
            post_data = request.files['photo']
            filestream = post_data.read()
            upload_data = Photo()
            upload_data.photo = google.db.Blob(filestream)
            upload_data.put()
            file_key = str(upload_data.key())
            

        project = Project.query.get(project_id)
        user = User.query.get(g.user.id)

        # 확신해도 되는건 project, user 제대로 들어감.

        log = Log(
                project = project,
                project_id = project_id,
                user = user,
                user_id = g.user.id,
                title = title,
                content = content,
                file_key = file_key
            )

        db.session.add(log)
        db.session.commit()

        flash('write log success','success')

        return redirect(url_for('project_detail', proj_id=project_id))

    logs = Log.query.all()
    return render_template('make_log/make_log.html', logs = logs)


@app.route('/make_log_delete_sche/<project_id>/<item_num>', methods=['GET', 'POST'])
def make_log_delete_sche(project_id, item_num):

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        # file 저장
        file_key = None
        if request.files['photo']:
            post_data = request.files['photo']
            filestream = post_data.read()
            upload_data = Photo()
            upload_data.photo = google.db.Blob(filestream)
            upload_data.put()
            file_key = str(upload_data.key())
            

        project = Project.query.get(project_id)
        user = User.query.get(g.user.id)

        # 확신해도 되는건 project, user 제대로 들어감.

        log = Log(
                project = project,
                project_id = project_id,
                user = user,
                user_id = g.user.id,
                title = title,
                content = content,
                file_key = file_key
            )

        db.session.add(log)
        db.session.commit()

        flash('write log success(delete shchedule)','success')


        # 해당 계획 완료이므로 스케쥴 스트링에서 꺼내와 쪼갠후, 해당 번호 계획 지운다. 
        list_item = project.schedule.split("*&*")
        list_item.pop()
        list_item.pop(int(item_num))
        list_str = "*&*".join(list_item) + "*&*"

        project.schedule = list_str
        db.session.commit()


        return redirect(url_for('project_detail', proj_id=project_id))

    logs = Log.query.all()
    return render_template('make_log/make_log.html', logs = logs)




@app.route('/log_detail/<log_id>', methods=['GET', 'POST'])
def log_detail(log_id):
    log = Log.query.get(log_id)

    if request.method == 'POST':
        log_id = request.form['log_id']
        user_id = g.user.id
        is_like = False
        if request.form['islike'] == 'like_with_feed':
            is_like = True
        content = request.form['content']


        log = Log.query.get(log_id)
        user = User.query.get(user_id)

        comment = Comment(
                log = log,
                user = user,
                is_like = is_like,
                content = content,
            )
        db.session.add(comment)
        db.session.commit()

        flash('comment write success','success')

    return render_template('log_detail/log_detail.html', log=log)

@app.route('/show/<key>')
def shows(key):
    upload_data = google.db.get(key)
    return app.response_class(upload_data.photo)


@app.route('/make_comment/', methods=['GET', 'POST'])
def make_comment():
     # projects = Project.query.all()
    users = User.query.all()
    logs = Log.query.all()

    if request.method == 'POST':
        log_id = request.form['log_id']
        user_id = g.user.id
        is_like = False
        if request.form['islike'] == 'like_with_feed':
            is_like = True
        content = request.form['content']


        log = Log.query.get(log_id)
        user = User.query.get(user_id)

        comment = Comment(
                log = log,
                user = user,
                is_like = is_like,
                content = content,
            )
        db.session.add(comment)
        db.session.commit()

        flash('submit success','success')
        
    comments = Comment.query.all()

    return render_template('make_comment/make_comment.html', users=users, logs=logs, comments=comments)


# #
# # @password check
# #
# @app.route('/pwcheck/<path:type>/target/<int:id>/', methods=['GET', 'POST'])
# def password_check(type, id):
# if request.method == 'GET':
# return render_template('pwcheck.html')
#     elif request.method == 'POST':
#         if type == 'COMMENT_UPDATE':
#             return redirect(url_for('comment_update', id=id))
#         elif type == 'COMMENT_DELETE':
#             return redirect(url_for('comment_delete', id=id))


#
# @error Handlers
#
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404


# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('error/500.html'), 500





# #
# # *Pusher & meeting application
# #

@app.route('/meeting/<proj_id>', methods=['GET'])
def meeting(proj_id):

    project = Project.query.get(proj_id)

    return render_template('meeting/meeting.html', project=project)

@app.route('/init_list/<proj_id>', methods=['GET'])
def init_list(proj_id):

    p = pusher.Pusher(
      app_id='85292',
      key='2f1737dadfe8bacfb3a1',
      secret='f155f7d0a772622f9a67'
    )

    project = Project.query.get(proj_id)

    list_sring = ""
    if project.schedule:  
        list_string = project.schedule

    return list_string


@app.route('/save_list/<proj_id>')
def save_list(proj_id):
    list_str = request.args['list_string']

    # 해당 프로젝트의 해달 컬럼에 저장
    proj = Project.query.get(proj_id)
    proj.schedule = list_str
    db.session.commit()

    return "success"

@app.route('/send', methods=['GET'])
def sendmsg():

    p = pusher.Pusher(
      app_id='85292',
      key='2f1737dadfe8bacfb3a1',
      secret='f155f7d0a772622f9a67'
    )

    chat_name = request.args.get('name_data')
    chat_msg = request.args.get('msg_data')


    # 이 채널을 유동적으로.
    p['test_channel'].trigger('chat_msg', {'name': chat_name, 'msg': chat_msg})

    return ""

@app.route('/add_list', methods=['GET'])
def add_list():

    p = pusher.Pusher(
      app_id='85292',
      key='2f1737dadfe8bacfb3a1',
      secret='f155f7d0a772622f9a67'
    )

    list_item = request.args.get('list_item')


    # 이 채널을 유동적으로.
    p['test_channel'].trigger('add_list', {'list_item': list_item})

    return ""

@app.route('/update_list', methods=['GET'])
def update_list():

    p = pusher.Pusher(
      app_id='85292',
      key='2f1737dadfe8bacfb3a1',
      secret='f155f7d0a772622f9a67'
    )

    list_string = request.args.get('list_string')


    # 이 채널을 유동적으로.
    p['test_channel'].trigger('update_list', {'list_string': list_string})

    return ""    