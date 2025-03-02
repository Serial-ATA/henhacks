# ForTheRecord

**ForTheRecord** is a music reviewing site with the following features:
* An auto-generated database of the most popular albums and songs (~35,000!) from [ListenBrainz](https://listenbrainz.org)
* User account creation with unique names and emails
* The ability to friend other users
* The ability to review individual songs and view all reviews on user profiles
* [Google Gemini](https://gemini.google.com/)-powered recommendation system, where users can get a list of song
  recommendations based on their highest rated songs as well as the highest rated songs of their friends.

## Prerequisites

* A [ListenBrainz API key](https://listenbrainz.readthedocs.io/en/latest/users/api/index.html)
* A [Gemini API key](https://aistudio.google.com/apikey)
* [python3](https://python.org)
* [PostgreSQL](https://www.postgresql.org/)

Install the python dependencies using `pip install -r requirements.txt`

## Usage

Create a `.env` file with `cp .env.example .env` and change values as needed.

To run this, simply do `python app.py` and visit <http://localhost:5000>

The front page has a registration box, which takes a username and email. To view your profile, or others
visit <http://localhost:5000/profile/<name>>.

To start finding songs, click the button on the front page to take you to a random song.