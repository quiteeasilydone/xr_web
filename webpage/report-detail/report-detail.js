let reportContent;
let infra;

document.addEventListener("DOMContentLoaded", function () {
  // URL에서 파라미터 값 가져오기
  const urlParams = new URLSearchParams(window.location.search);
  infra = urlParams.get("infra");
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
  console.log("get post");
  const apiUrl = `/api/posted-reports-detail?infra=${infra}&company_name=${getCookie(
    "company"
  )}&posted_report_id=${id}`;

  fetch(apiUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      console.log(data.report); // 받아온 JSON 데이터를 콘솔에 출력
      const extractedData = {
        start_time: formatUnixTime(data.report.start_time) + " (KST)",
        end_time: formatUnixTime(data.report.end_time) + " (KST)",
        inspection_list: data.report.inspection_list.map(inspection => ({
            topic: inspection.topic,
            instruction_list: inspection.instruction_list.map(instruction => ({
                instruction: instruction.instruction,
                answer: instruction.answer
            }))
        }))
    };
      reportContent.textContent = JSON.stringify(extractedData, null, "\t"); // 객체를 문자열로 변환하여 표시
      // 필요에 따라 데이터를 처리하는 로직 추가
    })
    .catch((error) => {
      console.error("Error fetching the posted report:", error);
    });
}

function formatUnixTime(unixTime) {
  // 유닉스 타임을 Date 객체로 변환
  const date = new Date(unixTime * 1000); // 유닉스 타임은 초 단위이므로 밀리초로 변환

  // 원하는 포맷으로 변환하는 방법 (예: "YYYY-MM-DD HH:MM:SS")
  const pad = (num) => num.toString().padStart(2, '0');

  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1); // getMonth()는 0부터 시작하므로 1을 더해줍니다.
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}