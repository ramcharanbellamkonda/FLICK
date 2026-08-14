const signupForm = document.getElementById("signupForm");

const nameInput = document.getElementById("signupName");
const emailInput = document.getElementById("signupEmail");
const passwordInput = document.getElementById("signupPassword");
const confirmInput = document.getElementById("confirmPassword");

const signupMessage = document.getElementById("signupMessage");

const signupEye = document.getElementById("signupEye");
const confirmEye = document.getElementById("confirmEye");

const strengthText = document.getElementById("strengthText");

const strengthBars = [
    document.getElementById("strength1"),
    document.getElementById("strength2"),
    document.getElementById("strength3"),
    document.getElementById("strength4")
];


// =====================================================
// PASSWORD VISIBILITY
// =====================================================

signupEye.addEventListener("click", function () {

    togglePassword(passwordInput, signupEye);

});


confirmEye.addEventListener("click", function () {

    togglePassword(confirmInput, confirmEye);

});


function togglePassword(input, button) {

    if (input.type === "password") {

        input.type = "text";

        button.textContent = "○";

    } else {

        input.type = "password";

        button.textContent = "◉";

    }

}


// =====================================================
// PASSWORD STRENGTH
// =====================================================

passwordInput.addEventListener(
    "input",
    checkPasswordStrength
);


function checkPasswordStrength() {

    const password = passwordInput.value;

    let score = 0;


    if (password.length >= 8) {
        score++;
    }


    if (/[A-Z]/.test(password)) {
        score++;
    }


    if (/[0-9]/.test(password)) {
        score++;
    }


    if (/[^A-Za-z0-9]/.test(password)) {
        score++;
    }


    strengthBars.forEach(function (bar, index) {

        if (index < score) {

            bar.style.background = "#d6a84f";

        } else {

            bar.style.background = "#e5e7eb";

        }

    });


    if (password.length === 0) {

        strengthText.textContent =
            "Use at least 8 characters";

    } else if (score === 1) {

        strengthText.textContent =
            "Weak password";

    } else if (score === 2) {

        strengthText.textContent =
            "Fair password";

    } else if (score === 3) {

        strengthText.textContent =
            "Good password";

    } else {

        strengthText.textContent =
            "Strong password";

    }

}


// =====================================================
// SIGNUP
// =====================================================

signupForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        clearMessage();


        const name = nameInput.value.trim();

        const email = emailInput.value.trim();

        const password = passwordInput.value;

        const confirmPassword = confirmInput.value;


        // =================================================
        // NAME VALIDATION
        // =================================================

        if (name.length < 2) {

            showError(
                "Please enter your full name."
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
        // PASSWORD VALIDATION
        // =================================================

        if (password.length < 8) {

            showError(
                "Password must contain at least 8 characters."
            );

            return;

        }


        // =================================================
        // CONFIRM PASSWORD
        // =================================================

        if (password !== confirmPassword) {

            showError(
                "Passwords do not match."
            );

            return;

        }


        // =================================================
        // SHOW LOADING MESSAGE
        // =================================================

        signupMessage.textContent =
            "Creating your account...";

        signupMessage.className =
            "message";


        try {

            // =================================================
            // CONNECT TO FLASK BACKEND
            // =================================================

            const response = await fetch(
                "http://127.0.0.1:5000/api/signup",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        name: name,

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
            // SIGNUP FAILED
            // =================================================

            if (!response.ok) {

                showError(
                    data.message ||
                    "Unable to create account."
                );

                return;

            }


            // =================================================
            // SIGNUP SUCCESSFUL
            // =================================================

            signupMessage.textContent =
                "Account created successfully! Redirecting to login...";

            signupMessage.className =
                "message success";


            // Clear form

            signupForm.reset();


            // Reset password strength bars

            strengthBars.forEach(function (bar) {

                bar.style.background =
                    "#e5e7eb";

            });


            strengthText.textContent =
                "Use at least 8 characters";


            // =================================================
            // REDIRECT TO LOGIN
            // =================================================

            setTimeout(function () {

                window.location.href =
                    "login.html";

            }, 1000);


        } catch (error) {

            console.error(
                "Signup error:",
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

    signupMessage.textContent =
        message;

    signupMessage.className =
        "message error";

}


// =====================================================
// CLEAR MESSAGE
// =====================================================

function clearMessage() {

    signupMessage.textContent =
        "";

    signupMessage.className =
        "message";

}


// =====================================================
// EMAIL VALIDATION
// =====================================================

function isValidEmail(email) {

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

}