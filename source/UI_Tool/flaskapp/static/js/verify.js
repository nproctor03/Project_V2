/**
 * Hides the first page of the verify labels form and shows page 2
 */
function ShowFormPage2() {
  // hide page 1
  document.getElementById("form-page-1").style.display = "none";
  //   unhide page 2
  document.getElementById("form-page-2").style.display = "block";
}

/**
 * Hides the second page of the verify labels form and shows page 1
 */
function ShowFormPage1() {
  //  unhide page 1
  document.getElementById("form-page-2").style.display = "none";
  // hide page 2
  document.getElementById("form-page-1").style.display = "block";
}

/**
 *
 * Validates and adds a user added label to the label list.
 */
function AddLabel() {
  user_label = document.getElementById("user-labels").value;
  labelList = document.getElementById("labelList");
  if (user_label.trim().length < 1 || user_label.trim().length > 50) {
    alert("Label must be between 1 and 50 characters long");
    return;
  }
  // console.log(user_label);
  listHTML = user_label.trim();
  labelList.innerHTML +=
    "<div class='row'><div class='col-sm-10'><li>" +
    listHTML +
    "</li></div><div class='col-sm-2'><i class='bi bi-trash3-fill' onclick = 'removeElement(this)'></div></div>";

  //   labelListInput.innerHTML += listHTML;
  document.getElementById("user-labels").value = "";
  document.getElementById("user-added-labels").value += listHTML + ",";
}

/**
 *
 * Removes a user added label from the label list.
 */
function removeElement(icon) {
  // This first part of the funciton removes the element from the list displyed on screen.
  // get the parent element of the icon
  var colDiv = icon.parentNode;
  // get parent element
  var rowDiv = colDiv.parentNode;
  // get the parent element of the row
  var ul = rowDiv.parentNode;
  // remove the row div from the list
  ul.removeChild(rowDiv);

  // This second part updates the user-added-labels form input
  labels = ul.getElementsByTagName("li");
  userAddedLabels = "";
  for (var i = 0; i < labels.length; i++) {
    // console.log(labels[i]);
    userAddedLabels += labels[i].textContent + ",";
  }
  // console.log(userAddedLabels);
  document.getElementById("user-added-labels").value = userAddedLabels;
}
