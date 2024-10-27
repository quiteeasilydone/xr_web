const email = sessionStorage.getItem("emailToCheck");
console.log(email);
document.getElementById("company_email").value = email;
function signup() {
  const companyEmail = document.getElementById("company_email").value;
  const companyName = document.getElementById("company_name").value;
  const companyNumber = document.getElementById("company_number").value;

  const data = {
    email: companyEmail,
    company_name: companyName,
    employee_identification_number: parseInt(companyNumber, 10),
  };

  fetch("/api/sign-up", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message === "User registered successfully") {
        setAuthCookies(companyName, companyNumber);
        alert("회사 등록이 완료되었습니다.");
        window.location.href = "/menu";
      } else if (data.detail) {
        console.error("Sign-up failed:", data);
        alert(`회사 등록에 실패했습니다: ${data.detail}`);
      } else {
        console.error("Unexpected response:", data);
        alert("예상치 못한 응답이 발생했습니다.");
      }
    });
}

function setAuthCookies(company_name, company_num) {
  console.log("쿠키 설정");
  setCookie("company", company_name, 1); // 1시간 유효한 쿠키
  setCookie("employee_number", company_num, 1); // 1시간 유효한 쿠키
  redirectToMenu();
}

function setCookie(name, value, hours) {
  let expires = "";
  if (hours) {
    const date = new Date();
    date.setTime(date.getTime() + hours * 60 * 60 * 1000);
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = `${name}=${value || ""}${expires}; path=/`;
}

function redirectToMenu() {
  window.location.href = "/report";
}
