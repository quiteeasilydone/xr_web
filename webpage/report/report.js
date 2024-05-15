class Inspection {
    constructor(topic, instructionList, imageRequired) {
      this.topic = topic;
      this.instructionList = instructionList;
      this.imageRequired = imageRequired;
    }
  
    changeTopicName(topic) {
      this.topic = topic;
    }
  
    // Instruction 객체를 추가하는 함수
    addInstruction(instruction) {
      this.instructionList.push(instruction);
    }
  
    setInstruction(instructionList) {}
  }
  
  class Instruction {
    constructor(instruction, instructionType, options, answer) {
      this.instruction = instruction;
      this.instructionType = instructionType;
  
      console.log(options);
      console.log(answer);
  
      if (options == null) {
        console.log("options가 null이에요");
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
      console.log(this.instructionType);
      if (this.instructionType == "check") return ["true"];
      else if (this.instructionType == "numericInput") return ["0"];
      else {
        return [this.options[0]];
      }
    }
  }
  
  class JsonData {
    constructor(infra, inspectionList) {
      this.infra = infra;
      this.inspectionList = inspectionList;
    }
  
    toJsonString() {
      return JSON.stringify(this, null, 2);
    }
  }
  
  let inspectionList = [];
  let jsonString;
  let jsonData;
  let container;
  
  // 새로운 토픽을 추가하는 함수
  function addTopic() {
    const topicElement = document.createElement("div"); // 새로운 토픽 요소 생성
    const topicNameInput = document.createElement("input"); // 토픽 이름 입력 필드 생성
    const addInstructionBtn = document.createElement("button"); // "Add Instruction" 버튼 생성
    const instructionContainer = document.createElement("div"); // 지시사항을 담을 컨테이너 생성
    const toggleInstructionsBtn = document.createElement("button"); // Instruction 토글 버튼 생성
  
    topicElement.classList.add("topic");
    instructionContainer.classList.add("instructionContainer");
  
    // 토픽 이름 입력 필드 속성 설정
    topicNameInput.setAttribute("type", "text");
    topicNameInput.setAttribute("placeholder", "토픽 입력");
    topicNameInput.classList.add("topicInput"); // 클래스 추가
  
    // "Add Instruction" 버튼 텍스트 설정
    addInstructionBtn.textContent = "항목 추가";
    addInstructionBtn.classList.add("addInstructionBtn"); // 클래스 추가
  
    // Instruction 토글 버튼 텍스트 및 속성 설정
    toggleInstructionsBtn.textContent = "내용 숨기기/보이기";
    toggleInstructionsBtn.classList.add("toggleInstructionBtn"); // 클래스 추가
  
    //임시 삭제 버튼
    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "삭제";
    deleteBtn.classList.add("delete-btn");
    deleteBtn.addEventListener("click", function () {
      // 삭제 버튼 클릭 시 해당 input을 포함한 부모 요소를 삭제합니다.
      topicElement.remove();
    });
  
    // 생성한 요소들을 토픽 요소에 추가
    topicElement.appendChild(topicNameInput);
    topicElement.appendChild(addInstructionBtn);
    topicElement.appendChild(toggleInstructionsBtn); // 토글 버튼 추가
    topicElement.appendChild(deleteBtn); // 삭제 버튼 추가
    topicElement.appendChild(instructionContainer); // 지시사항 컨테이너를 토픽 요소에 추가
    container.appendChild(topicElement); // 토픽 요소를 컨테이너에 추가
  
    // "Add Instruction" 버튼 클릭 시 실행될 함수
    addInstructionBtn.addEventListener("click", function () {
      addInstruction(instructionContainer);
    });
  
    // "Toggle Instructions" 버튼 클릭 시 실행될 함수
    toggleInstructionsBtn.addEventListener("click", function () {
      toggleInstructions(instructionContainer);
    });
  }
  
  // 지시사항 숨기기/보이기 토글 함수
  function toggleInstructions(instructionContainer) {
    // instructionContainer의 display 속성을 토글하여 숨기거나 보여줌
    if (instructionContainer.style.display === "none") {
      instructionContainer.style.display = "block";
    } else {
      instructionContainer.style.display = "none";
    }
  }
  
  function addInstruction(instructionContainer) {
    const instructionElement = document.createElement("div"); // 새로운 지시사항 요소 생성
    const instructionInput = document.createElement("input"); // 지시사항 입력 필드 생성
    const instructionTypeSelect = document.createElement("select"); // instructionType 선택 셀렉트 태그 생성
  
    //임시 삭제 버튼
    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "삭제";
    deleteBtn.classList.add("delete-btn");
    deleteBtn.addEventListener("click", function () {
      // 삭제 버튼 클릭 시 해당 input을 포함한 부모 요소를 삭제합니다.
      instructionElement.remove();
    });
  
    const options = document.createElement("div"); // 옵션 div 생성
    options.classList.add("options");
    const optionsContainer = document.createElement("div"); // 옵션 리스트 컨테이너 생성
  
    optionsContainer.classList.add("optionsContainer");
  
    // 옵션에 새 원소를 추가하는 버튼
    const addOptionBtn = document.createElement("button");
    addOptionBtn.textContent = "선택지 추가";
    addOptionBtn.classList.add("addOptionBtn");
  
    // 옵션 리스트를 숨김/보임 토글하는 버튼
    const toggleOptionsBtn = document.createElement("button");
    toggleOptionsBtn.textContent = "선택지 숨기기/보이기";
    toggleOptionsBtn.classList.add("toggleOptionBtn");
  
    // "Toggle Instructions" 버튼 클릭 시 실행될 함수
    toggleOptionsBtn.addEventListener("click", function () {
      toggleOptions(instructionContainer);
    });
  
    optionsContainer.appendChild(addOptionBtn);
    //optionsContainer.appendChild(toggleOptionsBtn);
  
    instructionElement.classList.add("instruction");
  
    // 지시사항 입력 필드 속성 설정
    instructionInput.setAttribute("type", "text");
    instructionInput.setAttribute("placeholder", "Instruction");
    instructionInput.classList.add("instructionInput");
  
    instructionTypeSelect.classList.add("instructionTypeSelect");
  
    // instruction Type을 변경했을 때 호출됨
    instructionTypeSelect.addEventListener("change", function (event) {
      const selectedValue = event.target.value; //변경된 값 가져옴
  
      const parentDiv = event.target.parentElement; // select 요소의 부모 요소 가져오기
      const optionsContainer = parentDiv.querySelector(".optionsContainer"); // options 컨테이너 찾기
      console.log(selectedValue);
  
      // 선택한 값이 "multipleChoice" 또는 "multipleSelect"인 경우
      if (
        selectedValue === "multipleChoice" ||
        selectedValue === "multipleSelect"
      ) {
        console.log("선택지 띄울게요");
        // 숨겨진 div를 보이도록 설정
        optionsContainer.style.display = "block";
      } else {
        // 다른 경우, 숨깁니다.
        console.log("선택지를 숨길게요");
        optionsContainer.style.display = "none";
      }
    });
  
    // instructionType 선택 셀렉트 태그 옵션 설정
    const optionValues = [
      "check",
      "multipleChoice",
      "singleChoice",
      "multipleSelect",
      "numericInput",
    ];
    const optionTexts = [
      "Check",
      "Multiple Choice",
      "Single Choice",
      "Multiple Select",
      "Numeric Input",
    ];
  
    for (let i = 0; i < optionValues.length; i++) {
      const option = document.createElement("option");
      option.value = optionValues[i];
      option.textContent = optionTexts[i];
      instructionTypeSelect.appendChild(option);
    }
  
    // 생성한 요소들을 지시사항 요소에 추가
    instructionElement.appendChild(instructionInput);
    instructionElement.appendChild(instructionTypeSelect);
    instructionElement.appendChild(deleteBtn);
    instructionContainer.appendChild(instructionElement); // 지시사항을 토픽 요소의 컨테이너에 추가
    instructionElement.appendChild(optionsContainer);
  
    addOptionBtn.addEventListener("click", function () {
      addOption(optionsContainer);
    });
    optionsContainer.style.display = "none";
  }
  
  // 선택지 숨기기/보이기 토글 함수
  function toggleOptions(optionContainer) {
    // instructionContainer의 display 속성을 토글하여 숨기거나 보여줌
    if (optionContainer.style.display === "none") {
      optionContainer.style.display = "block";
    } else {
      optionContainer.style.display = "none";
    }
  }
  
  function addOption(optionsContainer) {
    const optionElement = document.createElement("div");
    optionElement.classList.add("option");
  
    const optionInput = document.createElement("input");
    optionInput.setAttribute("type", "text");
    optionInput.setAttribute("placeholder", "Option");
  
    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Delete";
    deleteBtn.classList.add("delete-btn");
    deleteBtn.addEventListener("click", function () {
      // 삭제 버튼 클릭 시 해당 input을 포함한 부모 요소를 삭제합니다.
      optionElement.remove();
    });
  
    optionElement.appendChild(optionInput);
    optionElement.appendChild(deleteBtn);
  
    optionsContainer.appendChild(optionElement);
  }
  
  // 옵션들을 가져오는 함수
  function getOptions(instructionElement, instructionType) {
    let options = [];
    console.log(instructionType);
  
    switch (instructionType) {
      case "check":
        return null;
      case "singleChoice":
        options = ["예", "아니오"];
        break;
      case "numericInput":
        return null;
      case "multipleChoice":
      case "multipleSelect":
        const optionList = instructionElement.querySelectorAll(
          ".optionsContainer > div"
        );
  
        optionList.forEach(function (optionElement) {
          let value = optionElement.querySelector("input[type='text']").value;
          options.push(value);
        });
        break;
    }
  
    return options;
  }
  
  function saveReportForm() {
    if (jsonData == null) {
      console.log("새로 생성");
      generateJson();
    }
  
    sendRequest(jsonData);
  }
  
  // JSON을 생성하고 화면에 표시하는 함수
  function generateJson() {
    const infraName = document.getElementById("infraInput").value;
  
    const topicElements = document.querySelectorAll(".topic"); // topicInput 클래스에 속한 요소들 가져오기
  
    // 각 토픽 요소를 순회하며 정보를 가져오기
    topicElements.forEach(function (topicElement) {
      const topicName = topicElement.querySelector("input[type='text']").value; // 토픽 이름 가져오기
      const instructionList = []; // 각 토픽의 지시사항 목록을 담을 배열 초기화
      const instructionElement = topicElement.querySelector(
        ".instructionContainer"
      );
      const instructionElements = topicElement.querySelectorAll(
        "div .instructionInput"
      ); // 각 토픽의 지시사항 입력 요소들 가져오기
      const instructionTypeElements = topicElement.querySelectorAll(
        "div .instructionTypeSelect"
      ); // 각 토픽의 instructionType 선택 요소들 가져오기
  
      // 각 지시사항 입력 요소와 instructionType 선택 요소를 순회하며 정보를 가져와서 Instruction 객체를 만들고 instructionList에 추가
      for (let i = 0; i < instructionElements.length; i++) {
        const instructionValue = instructionElements[i].value;
        const instructionType = instructionTypeElements[i].value; // 선택한 instructionType 가져오기
  
        const instructionObject = new Instruction(
          instructionValue,
          instructionType,
          getOptions(instructionElement, instructionType),
          null
        ); // Instruction 객체 생성
        instructionList.push(instructionObject); // instructionList에 추가
      }
  
      const inspection = new Inspection(topicName, instructionList, false);
      inspectionList.push(inspection);
    });
  
    jsonData = new JsonData(infraName, inspectionList);
  
    const jsonOutputElement = document.getElementById("jsonOutput");
    jsonString = jsonData.toJsonString();
    jsonOutputElement.textContent = jsonString; // 들여쓰기 2로 설정하여 가독성 향상
    console.log(jsonString);
    sendRequest(jsonString);
  }
  
  function sendRequest(jsonData) {
    // HTTP POST 요청을 보낼 URL
    const url = "http://rtctest.p-e.kr/api/submit";
  
    // HTTP 요청 옵션 설정
    const requestOptions = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(jsonData),
    };
  
    // Fetch API를 사용하여 HTTP 요청 보내기
    fetch(url, requestOptions)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Response:", data);
        // 여기서 응답에 대한 작업을 수행합니다.
      })
      .catch((error) => {
        console.error("There was a problem with the request:", error);
        // 여기서 오류 처리를 수행합니다.
      });
  }
  
  function sendGetRequest() {
    // GET 요청을 보낼 URL
    const url = "http://rtctest.p-e.kr/api/db-view";
  
    // Fetch API를 사용하여 HTTP GET 요청 보내기
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Response:", data);
        // 여기서 응답에 대한 작업을 수행합니다.
      })
      .catch((error) => {
        console.error("There was a problem with the request:", error);
        // 여기서 오류 처리를 수행합니다.
      });
  }
  
  // HTML 문서가 로드되면 실행됨
  document.addEventListener("DOMContentLoaded", function () {
    console.log("abc");
    container = document.getElementById("report-container");
    console.log(container);
    const addTopicBtn = document.getElementById("addTopicBtn");
    const generateJsonBtn = document.getElementById("generateJsonBtn");
  
    // "Add Topic" 버튼 클릭 시 실행될 함수
    addTopicBtn.addEventListener("click", function () {
      addTopic();
    });
  
    // "Generate Json" 버튼 클릭 시 실행될 함수
    generateJsonBtn.addEventListener("click", function () {
      saveReportForm();
      //generateJson();
    });
  });
  