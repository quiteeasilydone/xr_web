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
        infra: data.report.infra,
        start_time: formatUnixTime(data.report.start_time) + " (KST)",
        end_time: formatUnixTime(data.report.end_time) + " (KST)",
        inspection_list: data.report.inspection_list.map((inspection) => ({
          topic: inspection.topic,
          instruction_list: inspection.instruction_list.map((instruction) => ({
            instruction: instruction.instruction,
            answer: instruction.answer,
          })),
        })),
      };

      //reportContent.textContent = JSON.stringify(extractedData, null, 2); // 객체를 문자열로 변환하여 표시
      const reportView = new ReportView(data);
      console.log(reportView);
      console.log(reportView.toJsonString());
      reportView.generateReportContainer();
      reportContent.textContent = reportView.toJsonString(); // toJsonString()을 사용하여 JSON 문자열로 변환
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
  const pad = (num) => num.toString().padStart(2, "0");

  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

//
// 테스트 작업
//

class Inspection {
  constructor(topic, instructionList, imageRequired) {
    this.topic = topic;
    this.instruction_list = instructionList;
    this.image_required = imageRequired;
  }

  changeTopicName(topic) {
    this.topic = topic;
  }

  // Instruction 객체를 추가하는 함수
  addInstruction(instruction) {
    this.instruction_list.push(instruction);
  }

  setInstruction(instructionList) {}
}

class Instruction {
  constructor(instruction, instructionType, options, answer) {
    this.instruction = instruction;
    this.instruction_type = instructionType;

    // console.log(options);
    // console.log(answer);

    if (options == null) {
      //console.log("options가 null이에요");
      this.options = [];
    } else {
      this.options = options;
    }

    if (answer == null) {
      this.answer = this.createDefaultAnswer();
    } else {
      this.answer = answer;
    }
  }
  createDefaultAnswer() {
    //console.log(this.instruction_type);
    if (this.instruction_type == "check") return ["true"];
    else if (this.instruction_type == "numeric_input") return ["0"];
    else {
      console.log(this.instruction_type);
      return [this.options[0]];
    }
  }
}

class ReportView {
  constructor(data) {
    const report = data.report;
    this.infra = report.infra;

    this.start_time = report.start_time;
    this.end_time = report.end_time;

    this.inspection_list = report.inspection_list.map((inspection) => ({
      topic: inspection.topic,
      instruction_list: inspection.instruction_list.map((instruction) => ({
        instruction: instruction.instruction,
        answer: instruction.answer,
      })),
    }));

    this.topic_count = this.inspection_list.length;
  }

  currentUnixTime() {
    return Math.floor(Date.now() / 1000).toString();
  }

  toJsonString() {
    const output = {
      infra: this.infra,
      start_time: this.start_time,
      end_time: this.end_time,
      inspection_list: this.inspection_list,
    };
    return JSON.stringify(output, null, 2);
  }

  generateReportContainer() {
    const reportContainer = document.getElementById("report-container");

    // 보고서 헤더 세팅
    const reportHeader = document.getElementById("report-header");
    reportHeader.textContent = `
    설비명 : ${this.infra}
    보고서 작성 시작시간 : ${this.start_time}
    보고서 작성 완료시간 : ${this.end_time}
    `;

    this.inspection_list.forEach((inspection) => {
      const topic = inspection.topic;
      console.log(`topic : ${topic}`);
      const instructions = inspection.instruction_list;

      // topic div 생성
      const topicDiv = document.createElement("div");
      topicDiv.className = "topic";

      // 타이틀 생성
      const topicTitle = document.createElement("span");
      topicTitle.className = "title";
      topicTitle.textContent = `토픽 이름 : ${topic}`;

      topicDiv.appendChild(topicTitle);

      // Instruction 토글 버튼 생성
      const toggleInstructionsBtn = document.createElement("button"); // Instruction 토글 버튼 생성

      toggleInstructionsBtn.textContent = "질문 숨기기/보이기";
      toggleInstructionsBtn.classList.add("addInstructionBtn"); // 클래스 추가
      topicDiv.appendChild(toggleInstructionsBtn); // 토글 버튼 추가

      // 질문 컨테이너 생성
      const instructionContainer = document.createElement("div");
      instructionContainer.className = "instructionContainer";

      for (let i = 0; i < instructions.length; i++) {
        const instructionDiv = this.generateInstruction(instructions[i]);
        instructionContainer.appendChild(instructionDiv);
      }
      topicDiv.appendChild(instructionContainer);

      // reportContainer에 topicDiv 추가
      reportContainer.appendChild(topicDiv);
    });
  }

  generateInstruction(instruction) {
    console.log(instruction);
    // instruction div 생성
    const instructionDiv = document.createElement("div");
    instructionDiv.className = "instruction";

    // 지시 사항 제목
    const instructionTitle = document.createElement("input"); // 지시사항 입력 필드 생성
    instructionTitle.value = instruction.instruction;
    instructionTitle.readOnly = true;

    instructionDiv.appendChild(instructionTitle);

    // 지시 사항 타입 (체크, 예/아니오, 다지선다)
    const questionType = document.createElement("button");
    questionType.textContent = "체크";
    questionType.className = "question-type";

    instructionDiv.appendChild(questionType);

    // 답변 생성
    const answer = document.createElement("p");
    answer.textContent = `답변: ${instruction.answer}`;

    instructionDiv.appendChild(answer);

    return instructionDiv;
  }
}
