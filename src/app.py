# app.py
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

def get_current_user():
    user = User.query.first()
    return user

@app.route('/people', methods=['GET'])
def list_people():
    people = Character.query.all()
    return jsonify([p.serialize() for p in people]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = Character.query.get(people_id)
    if person is None:
        return jsonify({"msg": "Character not found", "id": people_id}), 404
    return jsonify(person.serialize()), 200

@app.route('/planets', methods=['GET'])
def list_planets():
    planets = Planet.query.all()
    return jsonify([p.serialize() for p in planets]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "Planet not found", "id": planet_id}), 404
    return jsonify(planet.serialize()), 200

@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200

@app.route('/users/favorites', methods=['GET'])
def list_current_user_favorites():
    user = get_current_user()
    if user is None:
        return jsonify({"msg": "No users found. Create a user via Flask Admin first."}), 404

    favs = Favorite.query.filter_by(user_id=user.id).all()
    results = []
    for f in favs:
        item = f.serialize()
        if f.planet:
            item['planet'] = f.planet.serialize()
        if f.character:
            item['character'] = f.character.serialize()
        results.append(item)

    return jsonify(results), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user = get_current_user()
    if user is None:
        return jsonify({"msg": "No users found. Create a user via Flask Admin first."}), 404

    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "Planet not found", "id": planet_id}), 404


    existing = Favorite.query.filter_by(user_id=user.id, planet_id=planet_id).first()
    if existing:
        return jsonify({"msg": "Favorite already exists", "favorite": existing.serialize()}), 400

    fav = Favorite(user_id=user.id, planet_id=planet_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.serialize()), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user = get_current_user()
    if user is None:
        return jsonify({"msg": "No users found. Create a user via Flask Admin first."}), 404

    person = Character.query.get(people_id)
    if person is None:
        return jsonify({"msg": "Character not found", "id": people_id}), 404

    existing = Favorite.query.filter_by(user_id=user.id, character_id=people_id).first()
    if existing:
        return jsonify({"msg": "Favorite already exists", "favorite": existing.serialize()}), 400

    fav = Favorite(user_id=user.id, character_id=people_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.serialize()), 201


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user = get_current_user()
    if user is None:
        return jsonify({"msg": "No users found. Create a user via Flask Admin first."}), 404

    fav = Favorite.query.filter_by(user_id=user.id, planet_id=planet_id).first()
    if fav is None:
        return jsonify({"msg": "Favorite not found for this user", "planet_id": planet_id}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite planet removed", "planet_id": planet_id}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    user = get_current_user()
    if user is None:
        return jsonify({"msg": "No users found. Create a user via Flask Admin first."}), 404

    fav = Favorite.query.filter_by(user_id=user.id, character_id=people_id).first()
    if fav is None:
        return jsonify({"msg": "Favorite not found for this user", "character_id": people_id}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite character removed", "character_id": people_id}), 200


@app.route('/user', methods=['GET'])
def handle_hello():
    response_body = {"msg": "Hello, this is your GET /user response"}
    return jsonify(response_body), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
