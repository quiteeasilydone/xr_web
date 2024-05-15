document.addEventListener("DOMContentLoaded", function () {
    const infraName = document.getElementById("infra-name");
    const dateList = document.getElementById("date-list");
  
    // URL에서 파라미터 값 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const infra = urlParams.get("infra");
  
    // 설비 이름 설정
    infraName.textContent = infra;
  
    // 날짜 버튼 생성
    const startDate = new Date("2024-05-01");
    const endDate = new Date("2024-05-30");
  
    const dates = [];
    const currentDate = new Date(startDate);
  
    while (currentDate <= endDate) {
      const year = currentDate.getFullYear();
      const month = String(currentDate.getMonth() + 1).padStart(2, "0");
      const day = String(currentDate.getDate()).padStart(2, "0");
      const dateString = `${year}-${month}-${day}`;
      dates.push(dateString);
      currentDate.setDate(currentDate.getDate() + 1);
  
      // 날짜 버튼 생성 및 이벤트 리스너 추가
      const button = document.createElement("button");
      button.classList.add("date-button");
      button.textContent = dateString;
      button.addEventListener("click", function () {
        redirectToReportDetail(infra, dateString);
      });
      dateList.appendChild(button);
    }
  });
  
  function redirectToReportDetail(infra, date) {
    console.log('보고서 상세보기로 이동')
    // window.location.href = window.location.hostname + `/report-detail?infra=${infra}&date=${date}`;
    window.location.href = `/report-detail?infra=${infra}&date=${date}`;
  }
  