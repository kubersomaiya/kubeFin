import math
from bson import ObjectId
from flask import Flask, flash, render_template, request, url_for, redirect , session
from flask_pymongo import *
from pymongo import *
from datetime import datetime
import json
from flask_mail import Mail,Message

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.config.update(
    MAIL_SERVER ='smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = 'True',
    MAIL_USERNAME = params['gmail-user'],   
    MAIL_PASSWORD = params['gmail-password']
)
app.config["MAIL_DEFAULT_SENDER"] = "user@kubeFin.com"
app.config["MONGO_URI"] = "mongodb+srv://kubersomaiya:Kami%40234@kubefin.fd5lbve.mongodb.net/kubeFin"
app.secret_key = "330db21fe1067a7db9c151d6fc31ef4d4f4e4471"

mongodb_client = PyMongo(app)
usersCol = mongodb_client.db.users
mail = Mail(app)
postsCol = mongodb_client.db.posts

@app.route("/")
def home():
    posts = postsCol.find({})
    num_documents = postsCol.count_documents({})
    last = math.ceil(num_documents/int(params['no_of_posts']))

    page = request.args.get('page')

    if (not str(page).isnumeric()):
        page = 1

    page = int(page)

    posts_per_page = int(params['no_of_posts'])

    start_index = (page-1) * posts_per_page
    end_index = start_index + posts_per_page

    posts = posts[start_index:end_index]
    if page==1:
        prev = "#" 
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
       
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about.html")
def about():
    return render_template('about.html',params=params)

@app.route("/dashboard.html", methods=['GET', 'POST'])
def dashboard():
    if "user" in session and session['user'] == params['admin_user']:
        posts = postsCol.find({})
        return render_template('dashboard.html', params=params,posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            session['user'] = username
            posts = postsCol.find({})
            return render_template('dashboard.html', params=params ,posts=posts)
        
    else:
        return render_template('login.html', params=params)

@app.route("/edit.html/<string:id>", methods=['GET','POST'])
def edit(id):
    print(id)
    if "user" in session and session['user'] == params['admin_user']:
        print(request.method)
        if request.method == 'GET':
            print(id)
            if id =="0":
                post ={
                    "_id" : 0,
                    "title" :""
                }
            else :
                post = postsCol.find_one({"_id": ObjectId(id)})
            print(post)
            return render_template('edit.html', params=params, post = post)
        if request.method == 'POST':
            print(id)
            print(request.method)
            title = request.form.get('title')
            print(f'ths is {title}')
            subTitle = request.form.get('subTitle')
            slug = request.form.get('slug')
            imageUrl = request.form.get('imageUrl')
            content = request.form.get('content')
            current_date = datetime.now()
            date = current_date.strftime("%dth %b %Y")

            if id == '0':
                postInfo = {
                    "title": title,
                    "subTitle": subTitle,
                    "content": content,
                    "imageUrl": imageUrl,
                    "date": date,
                    "slug": slug
                }
                new_post = postsCol.insert_one(postInfo)
                
                print(new_post)
            else:
                updated_post = postsCol.update_one(
                    {"_id": ObjectId(id)}, 
                    {"$set": {
                    "title": title,
                    "subTitle": subTitle,
                    "slug": slug,
                    "content": content,
                    "imageUrl": imageUrl,
                    "date" : date
                }})
                print(updated_post)
            return redirect('/dashboard.html',code=302)

@app.route("/logout.html")
def logout():
    session.pop('user')
    return redirect('/dashboard.html')    
           
@app.route("/delete.html/<string:id>" ,methods =['POST','GET'])
def delete(id):
    if "user" in session and session['user'] == params['admin_user']:
        post_id = ObjectId(id)
        res = postsCol.delete_one({"_id": post_id})
        print(res)
        return redirect('/dashboard.html')  
    else:
        redirect('/login.html')             

@app.route("/contact.html", methods = ['POST', 'GET'])
def add_user():
    user_name = request.form.get('name')
    user_email = request.form.get('email')
    user_contact = request.form.get('contact')
    user_message = request.form.get('message')
    if(user_name != None and user_email != None and user_contact != None and user_message != None):
        usersCol.insert_one({
            "name": user_name,
            "email": user_email,
            "contact": user_contact,
            "message" : user_message,
            "date_created": datetime.utcnow()
        })
        msg = Message(f"You have recieved a New Message from {user_name}", sender=user_email , recipients=["kubersomaiya@gmail.com"],body = f"{user_message}\n" + f"Contact is : {user_contact} & , Email is : {user_email}")
        mail.send(msg)
        flash('Thankyou for submitting details , We will get back to you shortly...','success')
    # flashing karna hai
    # flash("Details Submitted Successfully", "success")
    return render_template('contact.html',params=params)

@app.route("/post.html/<string:post_slug>", methods = ['GET'])
def single_post(post_slug):
    new_post = postsCol.find_one({"slug": post_slug})
    return render_template('post.html',post = new_post,params=params)


app.run(debug=True )