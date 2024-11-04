const companyName = getCookie("company");

document.addEventListener("DOMContentLoaded", function () {
  const infraList = document.getElementById("infra-list");

  let infraArray; // infraArray 변수 선언

  // fetchInfraList 함수를 호출하고 반환된 프로미스를 이용하여 데이터를 처리
  fetchInfraList()
    .then((data) => {
      // 받은 데이터를 infraArray 변수에 할당
      console.log(data.infra_list); // 할당된 데이터 출력
      generateInfraButtons(data.infra_list, infraList);
    })
    .catch((error) => {
      console.error("Error fetching infra list:", error);
    });
});

function redirectToReport(infra) {
  window.location.href = `/report-view?infra=${infra}`;
}

function fetchInfraList() {
  // fetch 함수는 프로미스를 반환하므로 해당 프로미스를 반환
  return fetch(`/api/infra-list?company_name=${companyName}`)
    .then((response) => response.json())
    .then((data) => {
      // 서버에서 받은 데이터 반환
      return data;
    });
}

function generateInfraButtons(infraArray, infraList) {
  // 설비 버튼 생성
  infraArray.forEach((infra, index) => {
    const button = document.createElement("button");
    button.classList.add("infra-button");
    button.textContent = `설비 ${infra}`;
    button.addEventListener("click", function () {
      redirectToReport(infra);
    });
    infraList.appendChild(button);
  });
}
