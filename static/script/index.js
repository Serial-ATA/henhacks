const form = document.getElementById("signup-form");
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;

  try {
    const response = await fetch("http://127.0.0.1:5000/api/user/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email }),
    });

    if (!response.ok) {
      throw new Error("Server responded with " + response.status);
    }

    const data = await response.json();
    alert(
      `User created successfully!\nName: ${data.name}\nEmail: ${data.email}\nID: ${data.id || "No ID returned"}`,
    );
  } catch (error) {
    console.error(error);
    alert("Error creating user. Please try again.");
  }
});

const mysteryButton = document.getElementById("mystery-song-button");

mysteryButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/song/random");
    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }
    let data = await response.json();
    if (!data) {
      throw new Error("Song ID not found in response.");
    }
    window.location.href = `/song/${data}`;
  } catch (error) {
    console.error("Failed to fetch random song:", error);
    alert("Failed to load a random song. Please try again later.");
  }
});
