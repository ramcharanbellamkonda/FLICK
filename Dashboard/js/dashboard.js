const currentUser = JSON.parse(
    localStorage.getItem("movieMindCurrentUser")
);


// If user is not logged in, go back to login
if (!currentUser) {
    window.location.href = "login.html";
}


// Show user name
const userName = document.getElementById("userName");

if (userName) {
    userName.textContent = `Welcome, ${currentUser.name}`;
}


// Logout
const logoutButton = document.getElementById("logout");

if (logoutButton) {

    logoutButton.addEventListener("click", function () {

        localStorage.removeItem("movieMindCurrentUser");

        window.location.href = "login.html";

    });

}