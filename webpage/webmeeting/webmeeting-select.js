function addOptionsToInfraOption(optionsArray) {
    // Get the select element by its ID
    const select = document.getElementById("machineSelect");
  
    // Clear existing options
    select.innerHTML = "";
  
    // Iterate over the array and create option elements
    optionsArray.forEach((optionValue) => {
      // Create a new option element
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue; // Set the text content of the option
  
      // Append the option to the select
      select.appendChild(option);
    });
  }

async function getOptiensArray(){
    const companyName = getCookie('company');
    const optionUrl = 'https://' + window.location.hostname + '/api/wearable-machine-lists';
    const requestBody = {company_name : companyName}

    const response = await fetch(optionUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(requestBody)
    })

    const data = await response.json();
    console.log(data.wearable_identifications)
    if (!response.ok) {
        throw new Error(response.statusText)
    } else {
        addOptionsToInfraOption(data.wearable_identifications)
    }
}

document.addEventListener("DOMContentLoaded", getOptiensArray)