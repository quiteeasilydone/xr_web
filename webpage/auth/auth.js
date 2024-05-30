let emailToCheck = "";

document.addEventListener("DOMContentLoaded", () => {
  const code = getQueryParam("code");

  if (code) {
    // authenticateUser(code);
    authenticateUser(code, checkEmail);
  } else {
    console.error("No code parameter found in the URL");
  }
});

// URL에서 쿼리 파라미터 추출 함수
function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

// 쿠키 설정 함수
function setCookie(name, value, hours) {
  let expires = "";
  if (hours) {
    const date = new Date();
    date.setTime(date.getTime() + hours * 60 * 60 * 1000);
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = `${name}=${value || ""}${expires}; path=/`;
}

// 응답 데이터로 쿠키 설정 함수
function setAuthCookies(data) {
  setCookie("email", data.email, 1); // 1시간 유효한 쿠키
  setCookie("name", data.name, 1); // 1시간 유효한 쿠키
}

// 응답 데이터를 콘솔에 출력하는 함수
function printResponseData(data) {
  console.log("User ID:", data.id);
  console.log("Email:", data.email);
  console.log("Verified Email:", data.verified_email);
  console.log("Name:", data.name);
  console.log("Given Name:", data.given_name);
  console.log("Family Name:", data.family_name);
  console.log("Picture URL:", data.picture);
  console.log("Locale:", data.locale);
}

// /menu로 리다이렉트하는 함수
function redirectToMenu() {
  window.location.href = "/menu";
}

// 사용자 인증 함수
function authenticateUser(code, callback) {
  const apiUrl = `/api/auth/google?code=${code}`;

  fetch(apiUrl)
    .then((response) => response.json())
    .then((data) => {
      printResponseData(data); // 응답 데이터를 콘솔에 출력
      emailToCheck = data.email;
      callback(emailToCheck);

      //   setAuthCookies(data); // 응답 데이터로 쿠키 설정
      //   redirectToMenu(); // /menu로 리다이렉트
    })
    .catch((error) => {
      console.error("Error fetching the API:", error);
    });
}

function checkEmail(email) {
  console.log(`Checking email: ${email}`);

  fetch("/api/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.exists) {
        console.log("User exists:", data.user);
        // 유저가 존재할 경우 처리할 로직
      } else {
        console.log("User does not exist");
        // 유저가 존재하지 않을 경우 처리할 로직
      }
    })
    .catch((error) => {
      console.error("Error checking email:", error);
    });
}
