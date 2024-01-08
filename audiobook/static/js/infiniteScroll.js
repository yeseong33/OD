// infiniteScroll.js
let isLoading = false;
let page = 1;
const loadingDiv = document.getElementById('loading');

function appendBooks(books) {
    const container = document.getElementById('bookContainer');
    books.forEach(book => {
        const bookElement = document.createElement('div');
        bookElement.innerHTML = `
            <div class="book-card">
                <a href="/books/${book.book_id}/">
                    <img src="${book.book_cover}" alt="${book.title}" />
                    <div>
                        <h5>${book.title}</h5>
                        <p>${book.author}</p>
                    </div>
                </a>
            </div>
        `;
        container.appendChild(bookElement);
    });
}

function loadMoreBooks() {
    if (isLoading) return;
    isLoading = true;
    loadingDiv.style.display = 'block';

    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query') || '';

    fetch(`/api/book/list/?page=${page}&query=${query}`)
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                appendBooks(data.results);
                page++;
            } else {
                loadingDiv.innerHTML = 'No more books to load.';
                window.removeEventListener('scroll', onScroll);
            }
            isLoading = false;
        })
        .catch(error => {
            console.error('Error:', error);
            isLoading = false;
        })
        .finally(() => {
            loadingDiv.style.display = 'none';
        });
}

function onScroll() {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
        loadMoreBooks();
    }
}

window.addEventListener('scroll', onScroll);
