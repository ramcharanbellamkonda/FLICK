async function loadComponent(id, file) {
  const response = await fetch(file);
  const data = await response.text();
  document.getElementById(id).innerHTML = data;
}

loadComponent("header", "header.html");
loadComponent("footer", "footer.html");