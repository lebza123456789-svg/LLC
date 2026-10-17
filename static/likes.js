
document.addEventListener("click", async function (event) {
    const button = event.target.closest(".like-button");

    if (!button || button.disabled) {
        return;
    }

    event.preventDefault();

    const postId = button.dataset.postId;
    const label = button.querySelector(".like-label");
    const countElement = button.closest(".post-card")
        ?.querySelector(".like-count");

    if (!postId || !label || !countElement) {
        console.error("Like button is missing required elements.");
        return;
    }

    // Prevent double-clicking while the request is running.
    button.disabled = true;

    try {
        const response = await fetch(`/like/${postId}`, {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            credentials: "same-origin"
        });

        const data = await response.json();

        if (!response.ok || data.success !== true) {
            throw new Error(data.error || `Request failed: ${response.status}`);
        }

        // Update the button using the server's confirmed database state.
        button.dataset.liked = String(data.liked);
        button.classList.toggle("is-liked", data.liked);

        label.textContent = data.liked ? "♥" : "♡";
        countElement.textContent = data.like_count;

    } catch (error) {
        console.error("Like request failed:", error);
        alert("Could not update the like. Please try again.");
    } finally {
        button.disabled = false;
    }
});
