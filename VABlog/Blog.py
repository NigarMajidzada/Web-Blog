from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask import g, request, redirect, url_for


#Kullanici giris decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın. ")
            return redirect(url_for("login"))
        
    return decorated_function

#Kullanici kayit formu

class RegisterForm(Form):
    name = StringField("Isim Soyisim",validators=[validators.Length(min=4,max=25,message="Lutfen 4 ile 25 sayisi arasinda karakter giriniz")])
    username = StringField("Kullanici adi",validators=[validators.Length(min=5,max=35,message="Lutfen 5 ile 25 sayisi arasind akarakter giriniz")])  
    email = StringField("Email adresi",validators=[validators.Email(message="Lutfen gecerli bir email adresi girin")])
    password=PasswordField("Parola: ",validators=[
        validators.DataRequired(message="Lutfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolaniz uyusmuyor")
    ])

    confirm=PasswordField("Parola dogrula")
 
app = Flask(__name__)
app.secret_key= "vablog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "vablog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")   
  
def index():
     
     return render_template("index.html")

@app.route("/about")

def about():
    return render_template("about.html")



#Article Page

@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="select * from articles"

    result=cursor.execute(sorgu)

    if result>0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")



@app.route("/dashboard")
@login_required

def dashboard():

    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author=%s"
    result=cursor.execute(sorgu,(session["username"],))

    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return  render_template("dashboard.html")



    return render_template("dashboard.html")

#Kayit olma

@app.route("/register",methods=["GET","POST"])

def register():
    form=RegisterForm(request.form)

    if request.method == "POST" and form.validate() : 

        name=form.name.data
        username=form.username.data
        email=form.email.data
        password= sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()
        sorgu="Insert into users (name,username,email,password) values(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))

        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla kayıt oldunuz...","success")
        return redirect(url_for("login"))



        return redirect(url_for("index"))
    else:
        return render_template("register.html",form = form)




#Giris yapmak
    
class LoginForm(Form):

    username=StringField("Kullanıcı adı")
    password=PasswordField("Parola")


    
@app.route("/login",methods=["GET","POST"])

def login():

    form=LoginForm(request.form)

    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data 


        cursor=mysql.connection.cursor()

        sorgu="Select * from users where username=%s"

        result=cursor.execute(sorgu,(username,))

        if result>0:
            data=cursor.fetchone()
            real_password=data["password"]

            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız...","success")

                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yalnış Girdiniz...","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))


    return render_template("login.html",form=form)




#Detay Sayfasi

@app.route("/article/<string:id>")


def article(id):
    cursor=mysql.connection.cursor()
    sorgu="select * from articles where id= %s"
    result=cursor.execute(sorgu,(id,))

    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

#Logout

@app.route("/logout")


def logout():
    session.clear()
    return redirect(url_for("index"))




#Add artiles 

@app.route("/addarticle",methods=["GET","POST"])

def addarticle():
    form=ArticleForm(request.form)

    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()
        sorgu="Insert into articles (title,author,content) values(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()
        cursor.close()


        flash("Makale başarıyla eklendi","success")
        return redirect (url_for("dashboard"))
   
    return render_template("addarticle.html",form=form)




#Delete article 

@app.route("/delete/<string:id>")
@login_required

def delete(id):

    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author=%s AND id=%s"
    result = cursor.execute(sorgu, (session["username"], id))

    if result > 0:
        sorgu2 = "DELETE FROM articles WHERE id=%s"
        cursor.execute(sorgu2, (id,))

        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale veya bu işlem için yetkiniz yok", "danger")
        return redirect(url_for("index"))


#Edit article 
    
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required

def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="select * from articles where id=%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))

        if result==0:
            flash("Böyle bir makale yok ve ya bu işleme yetkiniz yok")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()


            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
    else:
        #post request

        form=ArticleForm(request.form)

        newTitle=form.title.data
        newContent=form.content.data

        sorgu2="update articles set title=%s, content=%s where id=%s"

        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))




#Makale form

class ArticleForm(Form):

    title=StringField("Makale başlığı",validators=[validators.Length(min=5, max=100)])
    content=TextAreaField("Makale içeriği",validators=[validators.Length(min=100)])




#Searh URL
    
@app.route("/search", methods=["GET", "POST"])

def search():
    if request.method=="GET":
        return redirect (url_for("index"))  
    else:
        keyword=request.form.get("keyword")

        cursor=mysql.connection.cursor()
        sorgu="select * from articles where title like '%"+ keyword +"%'"

        result=cursor.execute(sorgu)

        if result==0:
            flash("Aranan kelimeye uygun makale bulunamadi","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)
        

        


if __name__=="__main__":
    app.run(debug=True)

    