let infra;

document.addEventListener("DOMContentLoaded", function () {
  const infraName = document.getElementById("infra-name");
  const dateList = document.getElementById("date-list");

  // URL에서 파라미터 값 가져오기
  infra = getUrlParameter("infra");

  // 설비 이름 설정
  setInfraName(infra);

  // 날짜 버튼 생성
  //generateDateButtons(infra);

  // API 경로
  const apiUrl = `/api/posted-reports?infra=${infra}`;

  // GET 요청 보내기
  sendGetRequest(apiUrl, handleApiResponse);
});

function getUrlParameter(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

function setInfraName(infra) {
  const infraName = document.getElementById("infra-name");
  infraName.textContent = `${infra} 보고서 모음`;
}

// function generateDateButtons(infra) {
//   const dateList = document.getElementById("date-list");
//   const startDate = new Date("2024-05-01");
//   const endDate = new Date("2024-05-30");

//   const currentDate = new Date(startDate);
//   while (currentDate <= endDate) {
//     const dateString = formatDate(currentDate);
//     createAndAppendDateButton(dateList, infra, dateString);
//     currentDate.setDate(currentDate.getDate() + 1);
//   }
// }

// function formatDate(date) {
//   const year = date.getFullYear();
//   const month = String(date.getMonth() + 1).padStart(2, "0");
//   const day = String(date.getDate()).padStart(2, "0");
//   return `${year}-${month}-${day}`;
// }

// function createAndAppendDateButton(dateList, infra, dateString) {
//   const button = document.createElement("button");
//   button.classList.add("date-button");
//   button.textContent = dateString;
//   button.addEventListener("click", function () {
//     redirectToReportDetail(infra, dateString);
//   });
//   dateList.appendChild(button);
// }

function redirectToReportDetail(infra, posted_report_id) {
  console.log("보고서 상세보기로 이동");
  //window.location.href = `/report-detail?infra=${infra}&date=${date}`;
  //window.location.href = reportPath;
  window.location.href = `/report-detail?infra=${infra}&id=${posted_report_id}`;
}

function sendGetRequest(url, callback) {
  fetch(url)
    .then((response) => response.json())
    .then((data) => callback(data))
    .catch((error) => console.error("Error fetching the API:", error));
}

function handleApiResponse(data) {
  const dateList = document.getElementById("date-list");
  const postedReports = data.posted_reports;

  console.log(data.posted_reports);

  // postedReports.forEach((report) => {
  //   console.log(`${report.posted_report_id}:${report.user_name}`);

  //   console.log(report.posted_report_path);
  // });

  postedReports.forEach((report) => {
    const button = document.createElement("button");
    button.classList.add("date-button");
    button.textContent = `${report.posted_report_id}번 보고서 (작성자:${report.user_name})`;
    button.addEventListener("click", function () {
      redirectToReportDetail(infra, report.posted_report_id);
    });
    dateList.appendChild(button);
  });
}
