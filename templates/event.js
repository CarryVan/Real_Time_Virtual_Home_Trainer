const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');
const links = document.querySelectorAll('.nav-links li');

//햄버거바 클릭 이벤트
hamburger.addEventListener('click', () => {
    navLinks.classList.toggle("open");
})
