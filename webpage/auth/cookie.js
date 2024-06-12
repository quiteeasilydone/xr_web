// 쿠키 값을 읽는 함수
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

// 우측 상단에 사용자 정보 띄울 곳 만드는 함수
function createUserInfo(email, name) {
  console.log("태그들 생성");
  // user-info div 생성
  var userInfoDiv = document.createElement("div");
  userInfoDiv.id = "user-info";

  // user-email span 생성
  var userEmailSpan = document.createElement("span");
  userEmailSpan.id = "user-email";
  userEmailSpan.textContent = email;

  // user-name span 생성
  var userNameSpan = document.createElement("span");
  userNameSpan.id = "user-name";
  userNameSpan.textContent = name;

  // 로그아웃 버튼 생성
  var logoutButton = document.createElement("button");
  logoutButton.textContent = "로그아웃";
  logoutButton.onclick = logout;

  // 각 요소를 user-info div에 추가
  userInfoDiv.appendChild(userEmailSpan);
  userInfoDiv.appendChild(userNameSpan);
  userInfoDiv.appendChild(logoutButton);

  // user-info div를 body에 추가
  document.body.appendChild(userInfoDiv);
}

function deleteAllCookies() {
  const cookies = document.cookie.split(";");
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i];
    const eqPos = cookie.indexOf("=");
    const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
  }
}

function logout() {
  deleteAllCookies();
  window.location.href = "https://accounts.google.com/Logout";
}

// 페이지 로드 시 이메일과 이름을 표시
document.addEventListener("DOMContentLoaded", () => {
  console.log("cookie.js activated");
  createUserInfo();
  const company = getCookie("company");
  const number = getCookie("employee_number");

  if (company) {
    document.getElementById("user-email").textContent = `회사: ${company}`;
  } else {
    console.log("쿠키가 없네요");
    window.location.href = "/login";
  }

  if (number) {
    document.getElementById("user-name").textContent = `회사 번호: ${number}`;
  } else {
    window.location.href = "/login";
  }
});
