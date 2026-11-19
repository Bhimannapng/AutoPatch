document.addEventListener('DOMContentLoaded', () => {
    const postsContainer = document.getElementById('posts-container');
    const postForm = document.getElementById('post-form');

    function renderPosts(posts) {
        if (!postsContainer) return;
        postsContainer.innerHTML = '';
        if (posts.length === 0) {
            postsContainer.innerHTML = '<p class="empty-state">No articles published yet.</p>';
            return;
        }
        posts.forEach(post => {
            const article = document.createElement('article');
            article.className = 'post-card';
            article.innerHTML = `
                <h3>${escapeHTML(post.title)}</h3>
                <div class="post-meta">By ${escapeHTML(post.author)} &bull; ${new Date(post.created_at).toLocaleDateString()}</div>
                <p>${escapeHTML(post.content)}</p>
            `;
            postsContainer.appendChild(article);
        });
    }

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function fetchPosts() {
        fetch('/api/posts')
            .then(res => {
                if (!res.ok) throw new Error('Network response failed');
                return res.json();
            })
            .then(data => renderPosts(data))
            .catch(() => {
                if (postsContainer) {
                    postsContainer.innerHTML = '<p class="error-state">Failed to load articles.</p>';
                }
            });
    }

    if (postForm) {
        postForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const titleInput = document.getElementById('post-title');
            const authorInput = document.getElementById('post-author');
            const contentInput = document.getElementById('post-content');

            const payload = {
                title: titleInput ? titleInput.value : '',
                author: authorInput ? authorInput.value : '',
                content: contentInput ? contentInput.value : ''
            };

            fetch('/api/posts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => {
                if (!res.ok) throw new Error('Submission failed');
                return res.json();
            })
            .then(() => {
                if (postForm) postForm.reset();
                fetchPosts();
            })
            .catch(() => {
                alert('Could not publish article. Please verify inputs.');
            });
        });
    }

    fetchPosts();
});
