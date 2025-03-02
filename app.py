import os

import psycopg2
import requests
from flask import Flask, redirect, url_for, jsonify, request
from dotenv import load_dotenv

app = Flask(__name__)

conn = psycopg2.connect(database="ftr_db", user="postgres",
                        password="root", host="localhost", port="5432")

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
        return jsonify({"error": "database error"}), 500
    finally:
        cur.close()

    return {}, 201


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
        return jsonify({"error": "database error"}), 500
    finally:
        cur.close()

    return {}, 201


@app.route('/api/user/reviews/<user_id>', methods=['GET'])
def reviews_for_user(user_id):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM reviews WHERE id = {user_id};")
    reviews = cur.fetchall()
    cur.close()
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
        return jsonify({"error": "database error"}), 500
    finally:
        cur.close()

    return {}, 201


@app.route('/api/user/friends/<user_id>', methods=['GET'])
def get_friends(user_id):
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
    cur.close()

    friends = []
    user_id = int(user_id)

    for user, friend in raw_friends:
        if user == user_id:
            friends.append(friend)
            continue
        friends.append(user)

    return jsonify(friends)


API_ROOT = "https://api.listenbrainz.org"
load_dotenv()

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
