document.addEventListener("DOMContentLoaded", function () {
    // URL에서 파라미터 값 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const infra = urlParams.get("infra");
    const date = urlParams.get("date");
  
    // 보고서 제목 설정
    const reportTitle = `${infra} 점검 보고서 (${date})`;
    const reportTitleElement = document.getElementById("report-title");
    reportTitleElement.textContent = reportTitle;
  
    // 보고서 내용 로드 (이 부분은 필요에 따라 구현해야 합니다)
  });
  