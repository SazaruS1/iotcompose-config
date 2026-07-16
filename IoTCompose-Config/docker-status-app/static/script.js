async function refresh() {

    try {
        const response = await fetch("/api/status");
        const data = await response.json();

        // Vérifier si c'est un tableau ou un objet avec erreur
        if (!Array.isArray(data)) {
            console.error("Erreur API:", data);
            document.getElementById("containers").innerHTML = `<p>Erreur: ${data.error}</p>`;
            return;
        }

        const containers = data;
        const div = document.getElementById("containers");
        div.innerHTML = "";

        containers.forEach(c => {
            let icon = "⚪";
            let status = c.status.toLowerCase();

            if(status.includes("running")) icon="🟢";
            if(status.includes("exited")) icon="🔴";
            if(status.includes("restarting")) icon="🟡";
            if(status.includes("created")) icon="⚪";

            div.innerHTML += `
                <div class="card">
                    <div>
                        <strong>${c.name}</strong><br>
                        ${c.image}
                    </div>

                    <div class="${status}">
                        ${icon} ${status}
                    </div>
                </div>
            `;
        });
    } catch (err) {
        console.error("Erreur:", err);
    }
}

refresh();
setInterval(refresh, 5000);
