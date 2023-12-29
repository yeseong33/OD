document.addEventListener('DOMContentLoaded', function() {  
    const wrappers = document.querySelectorAll('.scrolling-wrapper');
    
    wrappers.forEach(function(wrapper) {
      const scrollContainer = wrapper.querySelector('.scrolling-container');
      const scrollLeftButton = wrapper.querySelector('.scroll-left-button');
      const scrollRightButton = wrapper.querySelector('.scroll-right-button');
      
      // 스크롤 버튼을 초기 상태에서 숨김 처리
      scrollLeftButton.style.display = 'none';
      scrollRightButton.style.display = 'none';

      // 콘텐츠 너비가 컨테이너 너비보다 크면 버튼을 표시
      if (scrollContainer.scrollWidth > scrollContainer.clientWidth) {  
          scrollLeftButton.style.display = 'block';
          scrollRightButton.style.display = 'block';
      }

      scrollLeftButton.addEventListener('click', function() {
          scrollContainer.scrollBy({ left: -300, behavior: 'smooth' });
      });
  
      scrollRightButton.addEventListener('click', function() {
          scrollContainer.scrollBy({ left: 300, behavior: 'smooth' });
      });
    });
});