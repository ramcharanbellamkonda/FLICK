// =========================================================
// FLICK COMPONENT LOADER
// =========================================================


// =========================================================
// LOAD COMPONENT
// =========================================================

async function loadComponent(id, file) {

    try {

        const response = await fetch(file, {
            cache: "no-store"
        });


        if (!response.ok) {

            throw new Error(
                `${file} returned HTTP ${response.status}`
            );

        }


        const html =
            await response.text();


        const element =
            document.getElementById(id);


        if (!element) {

            console.error(
                `Element #${id} was not found.`
            );

            return;

        }


        // Insert component
        element.innerHTML = html;


        console.log(
            `${file} loaded successfully.`
        );


        // =====================================================
        // HEADER
        // =====================================================

        if (id === "header") {

            checkLoginStatus();

        }


        // =====================================================
        // CUBE
        // =====================================================

        if (id === "cube") {

            loadCubeScript();

        }


    } catch (error) {

        console.error(
            `Failed to load ${file}:`,
            error
        );

    }

}



// =========================================================
// CHECK LOGIN STATUS
// =========================================================

async function checkLoginStatus() {

    const authButton =
        document.getElementById(
            "authButton"
        );


    if (!authButton) {

        console.error(
            "authButton was not found in header.html"
        );

        return;

    }


    try {

        const response =
    await fetch(
        "https://flick-qorf.onrender.com/api/me",
        {
            method: "GET",

            credentials: "include",

            cache: "no-store"
        }
    );


        const data =
            await response.json();


        console.log(
            "LOGIN STATUS:",
            data
        );


        // =================================================
        // LOGGED IN
        // =================================================

        if (
            response.ok &&
            data.loggedIn === true
        ) {

            authButton.textContent =
                "LOGOUT →";


            authButton.href =
                "#";


            // Remove old click handler
            authButton.onclick =
                null;


            authButton.addEventListener(
                "click",
                handleLogout
            );


        }


        // =================================================
        // NOT LOGGED IN
        // =================================================

        else {

            authButton.textContent =
                "SIGN IN →";


            authButton.href =
                "/login.html";


            authButton.onclick =
                null;

        }


    } catch (error) {

        console.error(
            "Login status check failed:",
            error
        );


        authButton.textContent =
            "SIGN IN →";


        authButton.href =
            "/login.html";

    }

}



// =========================================================
// LOGOUT
// =========================================================

async function handleLogout(event) {

    event.preventDefault();


    const authButton =
        document.getElementById(
            "authButton"
        );


    if (authButton) {

        authButton.textContent =
            "LOGGING OUT...";

        authButton.style.pointerEvents =
            "none";

    }


    try {

        const response =
            await fetch(
               "https://flick-qorf.onrender.com/api/logout",
                {
                    method: "POST",

                    credentials: "include"
                }
            );


        const data =
            await response.json();


        console.log(
            "LOGOUT RESPONSE:",
            data
        );


        if (
            response.ok &&
            data.success
        ) {

            window.location.href =
                "/login.html";

        }


        else {

            console.error(
                "Logout failed:",
                data
            );


            if (authButton) {

                authButton.textContent =
                    "LOGOUT →";

                authButton.style.pointerEvents =
                    "auto";

            }

        }


    } catch (error) {

        console.error(
            "Logout error:",
            error
        );


        if (authButton) {

            authButton.textContent =
                "LOGOUT →";

            authButton.style.pointerEvents =
                "auto";

        }

    }

}



// =========================================================
// LOAD CUBE JAVASCRIPT
// =========================================================

function loadCubeScript() {

    // Prevent loading cube.js multiple times

    if (
        document.querySelector(
            'script[data-flick-cube="true"]'
        )
    ) {

        return;

    }


    const script =
        document.createElement(
            "script"
        );


    script.src =
        "/cube.js";


    script.setAttribute(
        "data-flick-cube",
        "true"
    );


    script.onload =
        function () {

            console.log(
                "cube.js loaded successfully."
            );

        };


    script.onerror =
        function () {

            console.error(
                "Failed to load cube.js"
            );

        };


    document.body.appendChild(
        script
    );

}



// =========================================================
// LOAD ALL COMPONENTS
// =========================================================

loadComponent(
    "header",
    "/header.html"
);


loadComponent(
    "footer",
    "/footer.html"
);


loadComponent(
    "cube",
    "/cube.html"
);


loadComponent(
    "flow",
    "/flow.html"
);