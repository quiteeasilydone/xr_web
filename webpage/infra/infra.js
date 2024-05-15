document.addEventListener("DOMContentLoaded", function () {
    const infraList = document.getElementById("infra-list");
  
    // 설비 버튼 생성
    for (let i = 1; i <= 10; i++) {
      const button = document.createElement("button");
      button.classList.add("infra-button");
      button.textContent = `설비 ${i}`;
      button.addEventListener("click", function () {
        redirectToReport(`infra${i}`);
      });
      infraList.appendChild(button);
    }
  });
  
  function redirectToReport(infra) {
    window.location.href = `/report-view?infra=${infra}`;
  }
  