async function makeQr() {
    try{
        const companyName  = getCookie('company');
        const employeeIdentificationNumber = getCookie('employee_number');
        const imgDiv = document.getElementById('qr');
    
        const qrUrl = "https://" + window.location.hostname + "/api/wearable-qr-image";
        requsetBody = {
            employee_identification_number : Number(employeeIdentificationNumber),
            company_name : companyName,
            email : "dummy@example.com"
        };
        console.log(JSON.stringify(requsetBody))
        const response = await fetch(qrUrl, {
            method : "POST",
            headers: {
                'Content-Type': 'application/json'
              },
            body : JSON.stringify(requsetBody)
        })

        console.log(response)
    
        if (!response.ok) {
            throw new Error(response.statusText);
        }
    
        const qrBlob = await response.blob();
        const imageUrl = URL.createObjectURL(qrBlob);
        const img = document.createElement('img');
    
        img.src = imageUrl;
        imgDiv.appendChild(img);
    } catch (error) {
        const companyName  = getCookie('company');
        if (companyName === undefined) {
            alert("다시 로그인 하십시오");
        }
        console.error(error)
    }
}

document.addEventListener("DOMContentLoaded", makeQr)