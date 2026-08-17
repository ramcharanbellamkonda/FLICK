document.addEventListener("DOMContentLoaded", function () {

    const loginForm =
        document.getElementById("loginForm");

    const emailInput =
        document.getElementById("loginEmail");

    const passwordInput =
        document.getElementById("loginPassword");

    const loginMessage =
        document.getElementById("loginMessage");

    const loginEye =
        document.getElementById("loginEye");


    // =====================================================
    // PASSWORD SHOW / HIDE
    // =====================================================

    if (loginEye) {

        loginEye.addEventListener(
            "click",
            function () {

                if (
                    passwordInput.type ===
                    "password"
                ) {

                    passwordInput.type =
                        "text";

                    loginEye.textContent =
                        "◉";

                } else {

                    passwordInput.type =
                        "password";

                    loginEye.textContent =
                        "◉";

                }

            }
        );

    }


    // =====================================================
    // LOGIN
    // =====================================================

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const email =
                emailInput.value.trim();

            const password =
                passwordInput.value;


            loginMessage.textContent =
                "";


            // -------------------------------------------------
            // VALIDATION
            // -------------------------------------------------

            if (!email) {

                loginMessage.textContent =
                    "Please enter your email address.";

                return;

            }


            if (!password) {

                loginMessage.textContent =
                    "Please enter your password.";

                return;

            }


            // -------------------------------------------------
            // DISABLE BUTTON
            // -------------------------------------------------

            const button =
                loginForm.querySelector(
                    ".main-button"
                );


            const originalText =
                button.innerHTML;


            button.disabled =
                true;


            button.innerHTML =
                "Signing in...";


            try {

                // =================================================
                // CALL FLASK LOGIN API
                // =================================================

                const response =
                    await fetch(
                        "/api/login",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "include",

                            body:
                                JSON.stringify({

                                    email:
                                        email,

                                    password:
                                        password

                                })
                        }
                    );


                const data =
                    await response.json();


                // =================================================
                // LOGIN FAILED
                // =================================================

                if (
                    !response.ok ||
                    !data.success
                ) {

                    throw new Error(
                        data.message ||
                        "Invalid email or password."
                    );

                }


                // =================================================
                // LOGIN SUCCESSFUL
                // =================================================

                loginMessage.textContent =
                    "Login successful. Redirecting...";


                loginMessage.classList.add(
                    "success"
                );


                // Give Flask session a moment
                // to be established, then open dashboard.

                setTimeout(
                    function () {

                        window.location.href =
                            "/";

                    },
                    300
                );


            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );


                loginMessage.textContent =
                    error.message ||
                    "Login failed.";


            } finally {

                button.disabled =
                    false;

                button.innerHTML =
                    originalText;

            }

        }
    );

});