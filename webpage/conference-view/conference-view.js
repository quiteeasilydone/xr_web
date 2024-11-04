document.addEventListener("DOMContentLoaded", function () {
    const conferenceList = document.getElementById("conference-list");
  
    // 화상회의 목록 생성 (임시 데이터로 예시)
    const conferences = [
      { name: "화상회의 1", date: "2024-05-01" },
      { name: "화상회의 2", date: "2024-05-02" },
      { name: "화상회의 3", date: "2024-05-03" },
      { name: "화상회의 4", date: "2024-05-04" },
      { name: "화상회의 5", date: "2024-05-05" },
      { name: "화상회의 6", date: "2024-05-06" },
      { name: "화상회의 7", date: "2024-05-07" },
      { name: "화상회의 8", date: "2024-05-08" },
      { name: "화상회의 9", date: "2024-05-09" },
      { name: "화상회의 10", date: "2024-05-10" },
    ];
  
    conferences.forEach((conference) => {
      const conferenceItem = document.createElement("div");
      conferenceItem.classList.add("conference-item");
      conferenceItem.textContent = `${conference.name} - ${conference.date}`;
      conferenceItem.addEventListener("click", function () {
        // 화상회의 목록 항목을 클릭하면 해당 화상회의 페이지로 이동
        redirectToConferenceDetail(conference.name, conference.date);
      });
      conferenceList.appendChild(conferenceItem);
    });
  });
  
  function redirectToConferenceDetail(name, date) {
    window.location.href = `/conference-detail?name=${name}&date=${date}`;
  }
  