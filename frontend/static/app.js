function filterTickets() {
  let input = document.getElementById("search").value.toLowerCase();
  let tickets = document.getElementsByClassName("ticket");
  for (let i = 0; i < tickets.length; i++) {
    let text = tickets[i].innerText.toLowerCase();
    tickets[i].style.display = text.includes(input) ? "" : "none";
  }
}
