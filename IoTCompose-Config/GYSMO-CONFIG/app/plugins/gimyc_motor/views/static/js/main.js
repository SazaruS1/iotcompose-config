function buildPayload() {

    const mirrors = [];

    document
        .querySelectorAll('input[name="selected"]:checked')
        .forEach(cb => mirrors.push(cb.id));

    mode = Number(document.getElementById("mode").value)
    if (mode == 3) { //fixed
        return {
            mirrors: mirrors,
            mode:mode,
            angle: Number(document.getElementById("angle").value)
        };
    }  else {
        return {
            mirrors: mirrors,
            mode: mode,
        };
    }

}



function saveState() {
    // Sauvegarde le mode et la valeur éventuelle pour tous les actiionneurs sélectionnées
    val = document.getElementById("angle").value || 0
    mode = document.getElementById("mode").value || 0

    json = buildPayload()
    const csrfToken = document.getElementById('csrf_token').value;

    console.log(json)

    fetch(SET_STATE, {
        method: 'POST', // Méthode HTTP
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(json),
    })
//            .then(response => {
//                   console.log('Réponse du serveur :', response);
//            })
//            .catch(error => {
//                console.log("JE SUIS ICI")
//                console.error(error);
//            });
    showOverlay()
    setTimeout(
        () => {
            window.location.reload();
        },
        1000)
}


function setAngleForAll() {
    console.log("setAngleForAll")
    val = document.getElementById("global_angle_value").value || 0

    document.querySelectorAll("[data-motor]").forEach(element => {
        let key = element.getAttribute("data-motor"); // Récupère la valeur de l'attribut
        setAngle(key, val); // Appelle la fonction avec la clé et la valeur 0
    });
}

function setToTarget() {
    console.log("setToTarget")
    for (key in DATA) {
        val = DATA[key]['target'];
        setAngle(key, val); // Appelle la fonction avec la clé et la valeur 0
    }
}

function setHorizonForAll() {
    console.log("setHorizonForAll")
    val = document.getElementById("global_angle_value").value || 0

    document.querySelectorAll("[data-motor]").forEach(element => {
        let key = element.getAttribute("data-motor"); // Récupère la valeur de l'attribut
        setHorizontal(key); // Appelle la fonction avec la clé et la valeur 0
    });

}


// function setAngle(key, val=document.getElementById(key).value) {

//     console.log("setAngle", key, val);

//     const json = JSON.stringify({uid: key, angle: val})
//     const csrfToken = document.getElementById('csrf_token').value;


//     //fetch("https://echo.free.beeceptor.com", {
//     fetch(SET_ANGLE_URL, {
//         method: 'POST', // Méthode HTTP
//         headers: {
//             'Content-Type': 'application/json',
//             'X-CSRFToken': csrfToken,
//         },
//         body: json,
//     })
// //            .then(response => {
// //                   console.log('Réponse du serveur :', response);
// //            })
// //            .catch(error => {
// //                console.log("JE SUIS ICI")
// //                console.error(error);
// //            });
//     showOverlay()
//     setTimeout(
//         () => {
//             window.location.reload();
//         },
//         1000)

// }


// val n'est calculé qui si sa valeur n'est pas fournie


function setTarget(key) {
    val = document.getElementById(key).value;

    const json = JSON.stringify({uid: key, angle: val})
    const csrfToken = document.getElementById('csrf_token').value;


    //fetch("https://echo.free.beeceptor.com", {
    fetch(SET_TARGET_URL, {
        method: 'POST', // Méthode HTTP
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: json,
    })
//            .then(response => {
//                   console.log('Réponse du serveur :', response);
//            })
//            .catch(error => {
//                console.log("JE SUIS ICI")
//                console.error(error);
//            });
    showOverlay()
    setTimeout(
        () => {
            window.location.reload();
        },
        1000)

}

function setHorizontal(key) {
    val = document.getElementById(key).value;

    const json = JSON.stringify({uid: key, angle: val})
    const csrfToken = document.getElementById('csrf_token').value;


    //fetch("https://echo.free.beeceptor.com", {
    fetch(SET_VERTICAL_URL, {
        method: 'POST', // Méthode HTTP
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: json,
    })
//            .then(response => {
//                   console.log('Réponse du serveur :', response);
//            })
//            .catch(error => {
//                console.log("JE SUIS ICI")
//                console.error(error);
//            });
    showOverlay()
    setTimeout(
        () => {
            window.location.reload();
        },
        1000)

}

// function setState(key, state) {

//     const json = JSON.stringify({uid: key, state: state})
//     const csrfToken = document.getElementById('csrf_token').value;


//     //fetch("https://echo.free.beeceptor.com", {
//     fetch(SET_STATE_URL, {
//         method: 'POST', // Méthode HTTP
//         headers: {
//             'Content-Type': 'application/json',
//             'X-CSRFToken': csrfToken,
//         },
//         body: json,
//     })
// //            .then(response => {
// //                   console.log('Réponse du serveur :', response);
// //            })
// //            .catch(error => {
// //                console.log("JE SUIS ICI")
// //                console.error(error);
// //            });
//     showOverlay()
//     setTimeout(
//         () => {
//             window.location.reload();
//         },
//         1000)

// }