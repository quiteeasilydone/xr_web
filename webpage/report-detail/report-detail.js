let reportContent;

document.addEventListener("DOMContentLoaded", function () {
  // URL에서 파라미터 값 가져오기
  const urlParams = new URLSearchParams(window.location.search);
  const infra = urlParams.get("infra");
  const id = urlParams.get("id");
  console.log(`id : ${id}`);

  // 보고서 제목 설정
  const reportTitle = `${infra} 점검 보고서 (${id})`;
  const reportTitleElement = document.getElementById("report-title");
  reportContent = document.getElementById("report-content");
  reportTitleElement.textContent = reportTitle;

  // report 정보 불러오기
  getPostedReport(id);

  // 보고서 내용 로드 (이 부분은 필요에 따라 구현해야 합니다)
});

function getPostedReport(id) {
  const apiUrl = `/api/posted-report?posted_report_id=${id}`;

  fetch(apiUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      console.log(data.report); // 받아온 JSON 데이터를 콘솔에 출력
      reportContent.textContent = JSON.stringify(data.report, null, "\t"); // 객체를 문자열로 변환하여 표시
      // 필요에 따라 데이터를 처리하는 로직 추가
    })
    .catch((error) => {
      console.error("Error fetching the posted report:", error);
    });
}
