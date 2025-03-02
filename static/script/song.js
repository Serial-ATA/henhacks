const form = document.getElementById("add-review-form");
form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const userId = document.getElementById("review-user-id").value.trim();
  const rating = document.getElementById("review-rating").value.trim();
  const text = document.getElementById("review-text").value.trim();

  const reviewData = {
    song_id: songId,
    rating: parseInt(rating, 10),
  };

  if (text) {
    reviewData.text = text;
  }

  try {
    const response = await fetch(`/api/user/${userId}/add_review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reviewData),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    alert("Review submitted successfully!");
    window.location.reload();
  } catch (error) {
    console.error(error);
    alert("Error submitting review. Please try again.");
  }
});
