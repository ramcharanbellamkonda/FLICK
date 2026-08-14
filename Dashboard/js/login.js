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

const forgotPassword =
    document.getElementById("forgotPassword");


// =====================================================
// SHOW / HIDE PASSWORD
// =====================================================

loginEye.addEventListener("click", function () {

    if (passwordInput.type === "password") {

        passwordInput.type = "text";

        loginEye.textContent = "○";

    } else {

        passwordInput.type = "password";

        loginEye.textContent = "◉";

    }

});


// =====================================================
// FORGOT PASSWORD
// =====================================================

forgotPassword.addEventListener(
    "click",
    function (event) {

        event.preventDefault();

        loginMessage.textContent =
            "Password recovery will be available soon.";

        loginMessage.className =
            "message";

    }
);


// =====================================================
// LOGIN
// =====================================================

loginForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        loginMessage.textContent =
            "";

        loginMessage.className =
            "message";


        const email =
            emailInput.value.trim();

        const password =
            passwordInput.value;


        // =================================================
        // EMPTY FIELD VALIDATION
        // =================================================

        if (!email || !password) {

            showError(
                "Please enter your email and password."
            );

            return;

        }


        // =================================================
        // EMAIL VALIDATION
        // =================================================

        if (!isValidEmail(email)) {

            showError(
                "Please enter a valid email address."
            );

            return;

        }


        // =================================================
        // SHOW LOADING
        // =================================================

        loginMessage.textContent =
            "Signing in...";

        loginMessage.className =
            "message";


        try {

            // =================================================
            // CONNECT TO FLASK BACKEND
            // =================================================

            const response = await fetch(
                "http://127.0.0.1:5000/api/login",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials: "include",

                    body: JSON.stringify({

                        email: email,

                        password: password

                    })

                }
            );


            // =================================================
            // READ BACKEND RESPONSE
            // =================================================

            const data =
                await response.json();


            // =================================================
            // LOGIN FAILED
            // =================================================

            if (!response.ok) {

                showError(
                    data.message ||
                    "Invalid email or password."
                );

                return;

            }


            // =================================================
            // LOGIN SUCCESSFUL
            // =================================================

            localStorage.setItem(

                "FlickCurrentUser",

                JSON.stringify(
                    data.user
                )

            );


            loginMessage.textContent =
                "Login successful. Redirecting...";

            loginMessage.className =
                "message success";


            // =================================================
            // REDIRECT TO DASHBOARD
            // =================================================

            setTimeout(function () {

                window.location.href =
                    "index.html";

            }, 700);


        } catch (error) {

            console.error(
                "Login error:",
                error
            );


            showError(
                "Unable to connect to the server. Make sure Flask is running."
            );

        }

    }
);


// =====================================================
// ERROR MESSAGE
// =====================================================

function showError(message) {

    loginMessage.textContent =
        message;

    loginMessage.className =
        "message error";

}


// =====================================================
// EMAIL VALIDATION
// =====================================================

function isValidEmail(email) {

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

}