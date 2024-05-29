// 쿠키 값을 읽는 함수
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

// 페이지 로드 시 이메일과 이름을 표시
document.addEventListener("DOMContentLoaded", () => {
  const email = getCookie("email");
  const name = getCookie("name");

  if (email) {
    document.getElementById("user-email").textContent = `Email: ${email}`;
  }

  if (name) {
    document.getElementById("user-name").textContent = `Name: ${name}`;
  }
});
