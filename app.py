import json
import os
from statistics import mean

import psycopg2
import requests
from flask import Flask, redirect, url_for, jsonify, request, render_template, abort
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

conn = psycopg2.connect(database=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"),
                        password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("POSTGRES_HOST"), port=os.getenv("POSTGRES_PORT"))

@app.after_request
def handle_options(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With"

    return response

@app.route('/api/user/add', methods=['POST'])
def add_user():
    data = request.get_json(force=True)
    if "name" not in data or "email" not in data:
        return jsonify({"error": "missing name or email"}), 400

    cur = conn.cursor()
    try:
        cur.execute(f"INSERT INTO users (name, email) VALUES ('{data['name']}', '{data['email']}');")
        conn.commit()
    except:
        conn.rollback()
        return jsonify({"error": "database error"}), 500
    finally:
        cur.close()

    return jsonify(get_user_by_name(data["name"])), 201

@app.route('/api/song/random', methods=['GET'])
def random_song():
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id FROM songs ORDER BY RANDOM() LIMIT 1;")
        song_id = cur.fetchone()
    except:
        conn.rollback()
        return jsonify({"error": "database error"}), 500
    finally:
        cur.close()

    return str(song_id[0]), 200

@app.route('/api/user/<user_id>/add_review', methods=['POST'])
def add_review(user_id):
    data = request.get_json(force=True)
    if "song_id" not in data or "rating" not in data:
        return jsonify({"error": "missing song_id or rating"}), 400

    text = "null"
    if "text" in data:
        text = repr(data["text"])

    cur = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO reviews (user_id, song, content, rating) VALUES ('{user_id}', '{data['song_id']}', {text}, {data['rating']});")
        conn.commit()
    except:
        conn.rollback()
        return jsonify({"error": "database error"}), 500
    finally:
        cur.close()

    return {}, 201

def get_reviews_for_user(user_id):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM reviews WHERE user_id = {user_id};")
    reviews = cur.fetchall()
    cur.close()
    return [{
         "id": review[0],
         "user_id": review[1],
         "song": review[2],
         "content": review[3],
         "rating": review[4],
         "timestamp": review[5].isoformat() if review[5] else None
    } for review in reviews]


@app.route('/recommendations')
def recommendations():
    user_id = request.args.get("user_id")
    if not user_id:
        abort(400, description="Missing user_id parameter")
    user = get_user_by_id(user_id)
    if not user:
        abort(404, description="User not found")

    user_reviews = get_reviews_for_user(user_id)
    for review in user_reviews:
        song = get_song_by_id(review["song"])
        if song:
            review["song_name"] = song["name"]
            review["artist"] = song["artist"]

    friends = friends_of_user(user_id)
    friend_reviews = []
    for friend in friends:
        reviews = get_reviews_for_user(friend["id"])
        for review in reviews:
            song = get_song_by_id(review["song"])
            if song:
                review["song_name"] = song["name"]
                review["artist"] = song["artist"]
            review["friend_name"] = friend["name"]
        friend_reviews.extend(reviews)

    user_reviews_text = "\n".join([
        f"{review.get('song_name', 'Unknown Song')} by {review.get('artist', 'Unknown Artist')}: rating {review['rating']}"
        for review in user_reviews
    ])
    friend_reviews_text = "\n".join([
        f"{review.get('song_name', 'Unknown Song')} by {review.get('artist', 'Unknown Artist')}: rating {review['rating']} (reviewed by {review.get('friend_name', 'Unknown')})"
        for review in friend_reviews
    ])

    prompt = (
        "Generate a ranked list of song recommendations based on the following reviews.\n\n"
        "User Reviews:\n" + user_reviews_text + "\n\n"
        "Friend Reviews:\n" + friend_reviews_text + "\n\n"
        "Return the list in a sorted JSON array, sorted by the song's rank number.\n\n"
        "This array will contain objects with the following fields: rank (integer), title (string), artist (string), average_rating (integer), recommended_by_friend (bool).\n\n"
        "If any songs have an unknown artist or name, ignore them.\n\n"
        "For any song that is highly rated by a friend (rating >= 4), set the 'recommended_by_friend' field in the JSON to true.\n\n"
        "Do not include any text outside of the list.\n\n"
        "Do not wrap the JSON in a markdown code block, return it to me raw."
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.removeprefix("```json").removesuffix("```")
        recommendations_response = json.loads(text)
    except Exception as e:
        abort(500, description="Gemini API error: " + str(e))

    return render_template("recommendations.html", recommendations=recommendations_response, user=user)

@app.route('/api/user/reviews/<user_id>', methods=['GET'])
def reviews_for_user(user_id):
    reviews = get_reviews_for_user(user_id)
    return jsonify(reviews)


@app.route('/api/user/add_friend', methods=['POST'])
def add_friend():
    data = request.get_json(force=True)
    if "user_id" not in data or "friend_id" not in data:
        return jsonify({"error": "missing user_id or friend_id"}), 400

    cur = conn.cursor()
    try:
        cur.execute(f"INSERT INTO friends (user_id, friend_id) VALUES ('{data['user_id']}', '{data['friend_id']}');")
        conn.commit()
    except:
        conn.rollback()
        return jsonify({"error": "database error"}), 500
    finally:
        cur.close()

    return {}, 201

def get_user_by_name(name):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE name = '{name}';")
    user = cur.fetchone()
    if user is None:
        return None
    conn.commit()
    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "bio": user[3]
    }

def get_user_by_id(user_id):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id = {user_id};")
    user = cur.fetchone()
    if user is None:
        return None
    conn.commit()
    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "bio": user[3]
    }

@app.route('/api/user/<user_id>', methods=['GET'])
def user_by_id(user_id):
    try:
        user = get_user_by_id(user_id)
        if user is None:
            return {}, 404
    except:
        conn.rollback()
        return jsonify({"error": "database error"}), 500

    return jsonify(user), 201

@app.route('/api/user/by_name/<name>', methods=['GET'])
def user_by_name(name):
    try:
        user = get_user_by_name(name)
        if user is None:
            return {}, 404
    except:
        conn.rollback()
        return jsonify({"error": "database error"}), 500

    return jsonify(user), 201

@app.route('/profile/<name>')
def profile(name):
    try:
        user = get_user_by_name(name)
    except:
        conn.rollback()
        return jsonify({"error": "database error"}), 500

    if user is None:
        abort(404)

    friends = friends_of_user(user["id"])
    reviews = get_reviews_for_user(user["id"])

    highest_rated_song = 0
    highest_rated_album = 1

    if user["bio"] is None:
        user["bio"] = "No bio yet..."

    return render_template(
        'profile.html',
        user=user,
        friends=friends,
        reviews=reviews,
        songs_reviewed_count=len(reviews),
        highest_rated_song=highest_rated_song,
        highest_rated_album=highest_rated_album
    )

def friends_of_user(user_id):
    cur = conn.cursor()
    cur.execute(f"""
        SELECT
            *
        FROM
            friends
        WHERE
            user_id = {user_id}
        UNION
        SELECT
            *
        FROM
            friends
        WHERE
            friend_id = {user_id};
    """)
    raw_friends = cur.fetchall()

    friends = []
    user_id = int(user_id)

    for user, friend in raw_friends:
        if user == user_id:
            friends.append(get_user_by_id(friend))
            continue
        friends.append(get_user_by_id(user))

    return friends

@app.route('/api/user/friends/<user_id>', methods=['GET'])
def get_friends(user_id):
    friends = friends_of_user(user_id)
    return jsonify(friends)

def get_album_by_id(album_id):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM albums WHERE id = {album_id};")
    album = cur.fetchone()
    if album is None:
        return None
    conn.commit()
    return {
        "id": album[0],
        "name": album[1],
        "artist": album[2]
    }

def get_song_by_id(song_id):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM songs WHERE id = {song_id};")
    song = cur.fetchone()
    if song is None:
        return None
    conn.commit()
    return {
        "id": song[0],
        "name": song[1],
        "artist": song[2],
        "album": song[3]
    }

def get_reviews_for_song(song_id):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM reviews WHERE song = {song_id};")
    reviews = cur.fetchall()
    cur.close()
    return [{
        "id": review[0],
        "user_id": review[1],
        "song": review[2],
        "content": review[3],
        "rating": review[4],
        "timestamp": review[5]
    } for review in reviews]

@app.route('/song/<int:song_id>')
def show_song(song_id):
    song = get_song_by_id(song_id)
    if not song:
        abort(404, "Song not found")

    song_reviews = get_reviews_for_song(song_id)
    for review in song_reviews:
        review["username"] = get_user_by_id(review["user_id"])["name"]

    if song_reviews:
        avg_rating = mean([r["rating"] for r in song_reviews])
    else:
        avg_rating = None

    album = get_album_by_id(song["album"])
    song["album"] = album["name"]

    return render_template(
        'song.html',
        song=song,
        reviews=song_reviews,
        avg_rating=avg_rating
    )

@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')

API_ROOT = "https://api.listenbrainz.org"

AUTH_HEADER = {
    "Authorization": f"Token {os.getenv("LB_API_KEY")}"
}


def initialize_song_db(cursor):
    cursor.execute(f"SELECT * FROM songs;")
    songs = cursor.fetchall()
    if len(songs) != 0:
        return

    songs = requests.get(API_ROOT + "/1/stats/sitewide/artists", headers=AUTH_HEADER).json()
    payload = songs['payload']
    for artist in payload['artists']:
        if "artist_mbid" not in artist:
            continue
        artist_name = artist['artist_name'].replace('"', '\\"').replace("'", "''")
        mbid = artist['artist_mbid']

        top_recordings = requests.get(API_ROOT + f"/1/popularity/top-recordings-for-artist/{mbid}", headers=AUTH_HEADER).json()
        recordings_sorted = {}
        for recording in top_recordings:
            recording_name = recording['recording_name'].replace('"', '\\"').replace("'", "''")
            if "release_name" not in recording or recording['release_name'] is None:
                continue

            album = recording['release_name'].replace('"', '\\"').replace("'", "''")
            if album not in recordings_sorted:
                recordings_sorted[album] = []

            if recording_name in recordings_sorted[album]:
                continue

            recordings_sorted[album].append(recording_name)

        for album, songs in recordings_sorted.items():
            cursor.execute(f"INSERT INTO albums (name, artist) VALUES ('{album}', '{artist_name}') RETURNING id;")
            album_id = cursor.fetchone()[0]
            for song in songs:
                cursor.execute(f"INSERT INTO songs (name, artist, album) VALUES ('{song}', '{artist_name}', '{album_id}');")


with app.app_context():
    cur = conn.cursor()
    with open("./schema.sql") as f:
        cur.execute(f.read())
    initialize_song_db(cur)
    conn.commit()
    cur.close()

if __name__ == '__main__':
    app.run()