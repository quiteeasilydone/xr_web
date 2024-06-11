const cookie  = getCookie('company');
console.log(cookie)

async function makeQr() {
    try{
        const companyName  = getCookie('company');
        const employeeIdentificationNumber = getCookie('employee_number');
        const imgDiv = document.getElementById('qr');
    
        console.log(typeof(Number(employeeIdentificationNumber)))
        const qrUrl = "https://" + window.location.hostname + "/api/wearable-qr-image";
        requsetBody = {
            employee_identification_number : 0,
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
        console.error(error)
    }
}

document.addEventListener("DOMContentLoaded", makeQr)