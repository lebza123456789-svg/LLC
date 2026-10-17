
document.addEventListener("click", async function (event) {
    const button = event.target.closest(".like-button");

    if (!button || button.disabled) {
        return;
    }

    const postId = button.dataset.postId;
    const label = button.querySelector(".like-label");
    const count = button.querySelector(".like-count");
    const wasLiked = button.dataset.liked === "true";

    button.disabled = true;

    try {
        const response = await fetch(`/like/${postId}`, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });

        const result = await response.json();

        if (response.status === 401 && result.login_required) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok || !result.success) {
            alert(result.message || "Could not update like.");
            return;
        }

        button.dataset.liked = String(result.liked);
        label.textContent = result.liked ? "❤️ Liked" : "🤍 Like";
        count.textContent = result.like_count;

    } catch (error) {
        alert("Connection error. Please try again.");
        console.error(error);
    } finally {
        button.disabled = false;
    }
});
