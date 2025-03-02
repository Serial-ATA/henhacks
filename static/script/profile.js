// Change this to the actual user ID you want to display
const userId = "1";

// On page load, fetch data
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const userRes = await fetch(`http://localhost:5000/api/user/${userId}`);
    if (userRes.ok) {
      const userData = await userRes.json();
      document.getElementById("username").textContent = userData.name;
      document.getElementById("songs-reviewed").textContent =
        `Songs reviewed: ${userData.songsReviewedCount || 0}`;
      document.getElementById("albums-reviewed").textContent =
        `Albums reviewed: ${userData.albumsReviewedCount || 0}`;
      document.getElementById("follows").textContent =
        `Follows: ${userData.followsCount || 0}`;
      document.getElementById("bio").textContent =
        userData.bio || "No bio available.";

      if (userData.profileImg) {
        document.getElementById("profile-img").src = userData.profileImg;
      }
      // Also update the friends section title
      document.getElementById("friends-title").textContent =
        `${userData.name}'s Friends`;
    }

    const friendsRes = await fetch(
      `http://localhost:5000/api/user/friends/${userId}`,
    );
    if (friendsRes.ok) {
      const friends = await friendsRes.json();
      const friendsList = document.getElementById("friends-list");
      friendsList.innerHTML = ""; // Clear any placeholders

      friends.forEach((friend) => {
        const friendDiv = document.createElement("div");
        friendDiv.className = "friend";

        const img = document.createElement("img");
        img.src =
          friend.profileImg || "https://via.placeholder.com/80?text=Friend";
        img.alt = friend.name + " profile";

        const nameP = document.createElement("p");
        nameP.textContent = friend.name;

        friendDiv.appendChild(img);
        friendDiv.appendChild(nameP);
        friendsList.appendChild(friendDiv);
      });
    }

    // 3. Fetch user’s reviews
    //    GET /api/user/reviews/<user_id> -> returns array of reviews
    //    Example review object: { type: 'song' | 'album', title, artist, rating, image, ... }
    const reviewsRes = await fetch(
      `http://localhost:5000/api/user/reviews/${userId}`,
    );
    if (reviewsRes.ok) {
      const reviews = await reviewsRes.json();

      // Sort reviews by created date (descending) or however your API is structured
      // For "recently reviewed," we’ll just take the first 4 from the array if it’s sorted
      // Or if your API already returns them in chronological order, skip sorting.
      // Example:
      // reviews.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

      // Display up to 4 "recently reviewed"
      const recentlyReviewedContainer =
        document.getElementById("recently-reviewed");
      recentlyReviewedContainer.innerHTML = "";
      const recentlyReviewed = reviews.slice(0, 4);

      recentlyReviewed.forEach((review) => {
        const card = document.createElement("div");
        card.className = "review-card";

        // Placeholder album/song image
        const img = document.createElement("img");
        img.src =
          review.image || "https://via.placeholder.com/200x100?text=Album+Art";
        card.appendChild(img);

        const titleP = document.createElement("p");
        titleP.textContent = `[${review.type.toUpperCase()}] ${review.title}`;
        card.appendChild(titleP);

        const artistP = document.createElement("p");
        artistP.textContent = `Artist: ${review.artist}`;
        card.appendChild(artistP);

        const ratingP = document.createElement("p");
        ratingP.textContent = `Rating: ${review.rating}`;
        card.appendChild(ratingP);

        recentlyReviewedContainer.appendChild(card);
      });

      // Determine highest-rated song and album
      // Filter out songs, then sort by rating descending
      const songs = reviews.filter((r) => r.type === "song");
      songs.sort((a, b) => b.rating - a.rating);
      const highestSong = songs[0];

      const albums = reviews.filter((r) => r.type === "album");
      albums.sort((a, b) => b.rating - a.rating);
      const highestAlbum = albums[0];

      // Populate Highest Rated Song
      const songCard = document.getElementById("highest-rated-song");
      songCard.innerHTML = "<h3>Highest Rated Song</h3>"; // Clear placeholder

      if (highestSong) {
        const songImg = document.createElement("img");
        songImg.src =
          highestSong.image ||
          "https://via.placeholder.com/200x120?text=Song+Art";
        songCard.appendChild(songImg);

        const songTitle = document.createElement("p");
        songTitle.textContent = `Title: ${highestSong.title}`;
        songCard.appendChild(songTitle);

        const songArtist = document.createElement("p");
        songArtist.textContent = `Artist: ${highestSong.artist}`;
        songCard.appendChild(songArtist);

        const songRating = document.createElement("p");
        songRating.textContent = `Rating: ${highestSong.rating}`;
        songCard.appendChild(songRating);
      } else {
        const noSong = document.createElement("p");
        noSong.textContent = "No songs reviewed yet.";
        songCard.appendChild(noSong);
      }

      // Populate Highest Rated Album
      const albumCard = document.getElementById("highest-rated-album");
      albumCard.innerHTML = "<h3>Highest Rated Album</h3>";

      if (highestAlbum) {
        const albumImg = document.createElement("img");
        albumImg.src =
          highestAlbum.image ||
          "https://via.placeholder.com/200x120?text=Album+Art";
        albumCard.appendChild(albumImg);

        const albumTitle = document.createElement("p");
        albumTitle.textContent = `Title: ${highestAlbum.title}`;
        albumCard.appendChild(albumTitle);

        const albumArtist = document.createElement("p");
        albumArtist.textContent = `Artist: ${highestAlbum.artist}`;
        albumCard.appendChild(albumArtist);

        const albumRating = document.createElement("p");
        albumRating.textContent = `Rating: ${highestAlbum.rating}`;
        albumCard.appendChild(albumRating);
      } else {
        const noAlbum = document.createElement("p");
        noAlbum.textContent = "No albums reviewed yet.";
        albumCard.appendChild(noAlbum);
      }
    }
  } catch (err) {
    console.error("Error fetching profile data:", err);
  }
});
