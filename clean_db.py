from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict

# Step 1: Setup Flask and DB
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # your DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Step 2: Define the NGO model
class NGO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    district = db.Column(db.String(100))
    address = db.Column(db.String(300))
    contact = db.Column(db.String(50))
    needs = db.Column(db.String(300))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

# Step 3: Cleaning duplicates
with app.app_context():
    all_ngos = NGO.query.all()
    print(f"Total NGOs before cleaning: {len(all_ngos)}")

    seen = defaultdict(list)

    # Group NGOs by (name + district)
    for ngo in all_ngos:
        key = (ngo.name.strip().lower(), ngo.district.strip().lower())
        seen[key].append(ngo)

    # Remove duplicates & merge needs
    for key, ngos in seen.items():
        if len(ngos) > 1:
            main_ngo = ngos[0]
            all_needs = set()
            for n in ngos:
                if n.needs:
                    all_needs.update([x.strip() for x in n.needs.split(',')])
            main_ngo.needs = ', '.join(sorted(all_needs))
            for n in ngos[1:]:
                db.session.delete(n)

    db.session.commit()
    print("Duplicates removed and needs merged successfully!")

    # Verify12.925508779.1269684
    all_ngos = NGO.query.all()
    print(f"Total NGOs after cleaning: {len(all_ngos)}")
from app import app, db, NGO

with app.app_context():
    ngo = NGO.query.get(81)   # 🔹 change 51 to your NGO ID

    if ngo:
        print("Before:", ngo.name, ngo.latitude, ngo.longitude)

        ngo.latitude = 12.9361565 # ✅ correct latitude
        ngo.longitude = 79.2546794   # ✅ correct longitude

        db.session.commit()

        print("After:", ngo.name, ngo.latitude, ngo.longitude)
        print("Updated successfully!")
    else:
        print("NGO with that ID not found.")