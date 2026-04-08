# import webbrowser
# import threading

# def open_browser():
#     webbrowser.open_new("http://127.0.0.1:5000/")

# threading.Timer(1, open_browser).start()



from flask import Flask, render_template, redirect ,url_for,flash,request
from forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from utils import haversine
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from forms import AddNGOForm
import requests
app = Flask(__name__)
app.config['SECRET_KEY']='c6ee8e8b40029c5c2207c4dd3d3ba9c4'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
db = SQLAlchemy(app)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)   # increase size
    is_admin = db.Column(db.Boolean, default=False)
    def __repr__(self):
        return f"<User {self.username}>"

    # STEP 2 INSERT HERE
    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
class NGO(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30),nullable=False)
    district=db.Column(db.String(60),nullable=False)
    address=db.Column(db.String(200))
    contact=db.Column(db.String(30))
    needs=db.Column(db.String(100))
    latitude=db.Column(db.Float)
    longitude=db.Column(db.Float)      
    
    def __repr__(self):
        return f"<user {self.id}{self.name}{self.district}{self.address}{self.contact}{self.needs}{self.latitude}{self.longitude}"
    
def get_coordinates(district):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": district,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "NGO-Locator-App"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=20
        )

        if response.status_code != 200:
            print("Nominatim error:", response.status_code)
            return None, None

        if not response.text.strip():
            return None, None

        data = response.json()

        if not data:
            return None, None

        return float(data[0]["lat"]), float(data[0]["lon"])

    except Exception as e:
        print("Geocoding error:", e)
        return None, None
# import requests

def get_external_ngos_osm(district, needs):

    lat, lon = get_coordinates(district)

    if not lat or not lon:
        print("Could not get coordinates")
        return []

    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="social_facility"](around:30000,{lat},{lon});
      node["office"="ngo"](around:30000,{lat},{lon});
      node["amenity"="charity"](around:30000,{lat},{lon});
    );
    out body;
    """

    try:
        headers = {
            "User-Agent": "NGO-Locator-App"
        }

        response = requests.post(
            overpass_url,
            data=query,
            headers=headers,
            timeout=30
        )

        #  Check status first
        if response.status_code != 200:
            print("Overpass Error Code:", response.status_code)
            print("Response Text:", response.text)
            return []

        # Check empty response
        if not response.text.strip():
            print("Empty response from Overpass")
            return []

        data = response.json()

    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        return []

    except ValueError:
        print("Invalid JSON received")
        print("Raw response:", response.text)
        return []

    ngos = []

    for element in data.get("elements", []):
        name = element.get("tags", {}).get("name")
        if not name:
            continue

        ngos.append({
            "name": name,
            "address": element.get("tags", {}).get("addr:full", "Not Available"),
            "contact": element.get("tags", {}).get("phone", "Not Available"),
            "needs": needs,
            "latitude": element.get("lat"),
            "longitude": element.get("lon")
        })

    print("External NGOs found:", len(ngos))
    return ngos
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')
def import_csv():
    df = pd.read_csv('data/NGO_DETAILS.csv')
    df = df.dropna(subset=['name'])
  
    for _, row in df.iterrows():
        ngo = NGO(
            name=row['name'],
            district=row['district'],
            address=row['address'],
            contact=row['contact'],
            needs=row['needs'],
            latitude=row['latitude'],
            longitude=row['longitude']
        )
        db.session.add(ngo)

    db.session.commit()
    print("CSV data imported successfully")
@app.route('/ngo_details')
@login_required
def ngo_details():
    if not current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('home'))

    ngos = NGO.query.all()
    return render_template("ngo_details.html", ngos=ngos)
@app.route('/add_ngo', methods=['GET', 'POST'])
@login_required
def add_ngo():
    if not current_user.is_admin:
        flash("You are not authorized!", "danger")
        return redirect(url_for('home'))

    form = AddNGOForm()

    if form.validate_on_submit():
        ngo = NGO(
            name=form.name.data,
            district=form.district.data,
            address=form.address.data,
            contact=form.contact.data,
            needs=form.needs.data,
            latitude=float(form.latitude.data) if form.latitude.data else None,
            longitude=float(form.longitude.data) if form.longitude.data else None
        )

        db.session.add(ngo)
        db.session.commit()

        flash("NGO added successfully!", "success")
        return redirect(url_for('ngo_details'))

    return render_template('add_ngo.html', form=form) 

@app.route('/search', methods=['GET', 'POST'])
def search():

    
    # Get Values (Voice = GET, Form = POST)
 
    if request.method == "GET":
        user_district = request.args.get("district")
        user_needs = request.args.get("needs")
        user_lat = request.args.get("latitude")
        user_lon = request.args.get("longitude")
    else:
        user_district = request.form.get("district")
        user_needs = request.form.get("needs")
        user_lat = request.form.get("latitude")
        user_lon = request.form.get("longitude")

    print("District:", user_district)
    print("Needs (Before Mapping):", user_needs)

    
    if user_needs:
        user_needs = user_needs.lower().strip()

        if "food" in user_needs:
            user_needs = "Food"
        elif "medical" in user_needs or "hospital" in user_needs or "clinic" in user_needs:
            user_needs = "Medical"
        elif "child" in user_needs:
            user_needs = "Child"
        elif "women" in user_needs:
            user_needs = "Women"
        elif "education" in user_needs:
            user_needs = "Education"

    print("Needs (After Mapping):", user_needs)

    # -------------------------
    # Filter NGOs
    # -------------------------
    filtered_ngos = []
    external_fallback = False

    if user_district == "current":
        filtered_ngos = NGO.query.all()

    elif user_district and user_needs:
        filtered_ngos = NGO.query.filter(
            NGO.district.ilike(f"%{user_district}%"),
            NGO.needs.ilike(f"%{user_needs}%")
        ).all()

  
    if not filtered_ngos and user_district != "current":
        external_fallback = True

        external_ngos = get_external_ngos_osm(user_district, user_needs)

        for ngo_data in external_ngos:

            existing = NGO.query.filter_by(
                name=ngo_data["name"],
                district=user_district
            ).first()

            if not existing:
                ngo = NGO(
                    name=ngo_data["name"],
                    district=user_district,
                    address=ngo_data["address"],
                    contact=ngo_data["contact"],
                    needs=ngo_data["needs"],
                    latitude=ngo_data["latitude"],
                    longitude=ngo_data["longitude"]
                )
                db.session.add(ngo)
                filtered_ngos.append(ngo)

        db.session.commit()

    # Distance Calculation
    nearest_ngos = []

    if user_lat and user_lon:
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
        except:
            user_lat = None
            user_lon = None

        if user_lat and user_lon:
            for ngo in filtered_ngos:
                if ngo.latitude and ngo.longitude:

                    distance = haversine(
                        user_lat,
                        user_lon,
                        ngo.latitude,
                        ngo.longitude
                    )

                    nearest_ngos.append({
                        "name": ngo.name,
                        "district": ngo.district,
                        "address": ngo.address,
                        "needs": ngo.needs,
                        "contact": ngo.contact,
                        "latitude": ngo.latitude,
                        "longitude": ngo.longitude,
                        "distance": round(distance, 2)
                    })

            nearest_ngos = sorted(
                nearest_ngos,
                key=lambda x: x["distance"]
            )[:5]

   
    
    return render_template(
        "results.html",
        all_ngos=filtered_ngos,
        nearest_ngos=nearest_ngos,
        user_lat=user_lat,
        user_lon=user_lon,
        external_fallback=external_fallback
    )
@app.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(form.password.data)

        # Proper admin assignment
        is_admin_user = True if form.email.data == "aids03670@gmail.com" else False

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            is_admin=is_admin_user   #  IMPORTANT LINE
        )

        db.session.add(user)
        db.session.commit()

        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)
@app.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            flash('Login successful!','success')
            return redirect(url_for('home'))
        else:
            flash('login unsuccessful.check email and password','danger')

    return render_template('login.html',title='Login',form=form)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RequestResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            reset_link = url_for('reset_token', token=token, _external=True)

            print("RESET LINK:", reset_link)  # temporary

            flash('Password reset link generated. Check console.', 'info')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email.', 'danger')

    return render_template('reset_request.html', form=form)
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):

    user = User.verify_reset_token(token)

    if user is None:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()

        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_token.html', form=form)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        number_of_rows=NGO.query.count()
        if(number_of_rows== 0):
            import_csv()
        else :
            pass
  
    app.run(debug=True)
# host="127.0.0.1", port=5000