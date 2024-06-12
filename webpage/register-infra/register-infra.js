async function sendRegisterRequest() {
    try{
        const requestUrl = 'https://' + window.location.hostname + '/api/infra';
        const infraName = document.getElementById('infraName').value;
        const companyName = getCookie('company');
        const infraQrdiv = document.getElementById('infraQr');
    
        let requsetBody = {
            infra_name : infraName,
            company_name : companyName
        };
    
        const response = await fetch(requestUrl, {
            method : "POST",
            headers: {
                'Content-Type': 'application/json'
                },
            body : JSON.stringify(requsetBody)
        });
    
        if (response.ok) {
            const qrUrl = 'https://' + window.location.hostname + '/api/infra-qr-image';
    
            const qrResponse = await fetch(qrUrl, {
                method : "POST",
                headers : {
                    'Content-Type' : 'application/json'
                },
                body : JSON.stringify(requsetBody)
            })
            
            if (!qrResponse.ok) {
                throw new Error(qrResponse.statusText)
            }
    
            const qrBlob = await qrResponse.blob();
            const imageUrl = URL.createObjectURL(qrBlob);
            const img = document.createElement('img');
            img.src = imageUrl;

            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = 'downloaded_image.png';
            link.textContent = 'Download Image';

            
            infraQrdiv.appendChild(img);
            infraQrdiv.appendChild(link)
            
        } else {
            throw new Error(response.statusText)
        }
    } catch (error) {
        console.error(error)
    }
}