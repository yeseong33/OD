// infiniteScroll.js
let isLoading = false;
let page = 1;
const loadingDiv = document.getElementById('loading');

function appendBooks(books) {
    const container = document.getElementById('bookContainer');
    books.forEach(book => {
        const bookElement = document.createElement('div');
        console.log(book.book_image_path)
        bookElement.innerHTML = `
            <div class="book-card">
                <a href="/content/${book.book_id}/">
                    <img class="book-img" src="${book.book_image_path}" alt="${book.book_title}" />
                </a>
                <div class="book-info">
                    <h5>${book.book_title}</h5>
                    <p>저자: ${book.book_author}</p>
                </div>
            </div>
        `;
        container.appendChild(bookElement);
    });
}

function loadMoreBooks() {
    if (isLoading) {
        console.log("Already loading books, returning");
        return;
    }
    console.log("Loading more books");
    isLoading = true;
    loadingDiv.style.display = 'block';

    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query') || '';

    fetch(`/api/book/list/?page=${page}&query=${query}`)
        .then(response => {
            console.log("Received response from API", response);
            return response.json();
        })
        .then(data => {
            if (data.results && data.results.length > 0) {
                console.log(data.results)
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
    console.log("Scroll event triggered");
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
        loadMoreBooks();
    }
}

window.addEventListener('scroll', onScroll);
