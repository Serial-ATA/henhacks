CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(30) NOT NULL UNIQUE,
    bio VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS friends (
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (friend_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    artist TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    artist TEXT NOT NULL,
    album INT NOT NULL,
    FOREIGN KEY (album) REFERENCES albums(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    song INT NOT NULL,
    content TEXT,
    rating INT NOT NULL,
    time TIMESTAMP NOT NULL DEFAULT current_timestamp,
    CONSTRAINT CheckRating CHECK ( rating <= 5 ),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (song) REFERENCES songs(id)
);