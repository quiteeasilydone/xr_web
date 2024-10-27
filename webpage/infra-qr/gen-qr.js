document.addEventListener('DOMContentLoaded', generateQR())


async function generateQR(){
    url = new URL(window.location.href);
    const urlParams = url.searchParams;
    const infraName = urlParams.get('infra');
    const companyName = getCookie("company");
    const infraQrdiv = document.getElementById("infraQr");

    const qrUrl = "https://" + window.location.hostname + "/api/infra-qr-image";

    let requsetBody = {
        infra_name: infraName,
        company_name: companyName,
      };

    const qrResponse = await fetch(qrUrl, {
        method: "POST",
        headers: {
        "Content-Type": "application/json",
        },
        body: JSON.stringify(requsetBody),
    });

    if (!qrResponse.ok) {
        throw new Error(qrResponse.statusText);
    }

    const qrBlob = await qrResponse.blob();
    const imageUrl = URL.createObjectURL(qrBlob);
    const img = document.createElement("img");
    img.id = "qrImg";
    img.src = imageUrl;

    const link = document.createElement("a");
    link.href = imageUrl;
    link.download = "downloaded_image.png";
    link.textContent = "Download Image";

    infraQrdiv.appendChild(img);
    infraQrdiv.appendChild(link);
}
