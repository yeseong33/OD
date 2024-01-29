// 조정하기 버튼 함수
function submitTone() {
    fetch(playUrl, {
        method: 'POST',
        headers: {
            //'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log(data); 
        alert('생성이 완료되었습니다.');
        window.location.reload();           
    })
    .catch(error => console.error('Error:', error));
}