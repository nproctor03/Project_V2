$("form[name=login_form").submit(function (e) {
  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();

  $.ajax({
    url: "/user/login",
    type: "POST",
    data: data,
    dataType: "json",
    success: function (resp) {
      window.location.href = "/";
    },
    error: function (resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      console.log("fail");
    },
  });

  e.preventDefault();
});

/**
 * Calls the appropriate endpoint based on wether the user is an admin user or not.
 */
$("form[name=create_user_form").submit(function (e) {
  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();

  // console.log(data);
  // console.log("HELLOOOOOO");

  var url;

  if ($("#isAdmin").is(":checked")) {
    console.log("True");
    url = "/user/create_admin";
  } else {
    url = "/user/create_user";
    console.log("False");
  }

  $.ajax({
    url: url,
    type: "POST",
    data: data,
    dataType: "json",
    success: function (resp) {
      $error.text("").addClass("error--hidden");
      alert("User Created");
      window.location.href = "/createaccount/";
      //   $("#username").val("");
      //   $("#password").val("");
      //   $("#isAdmin").prop("checked", false);
    },
    error: function (resp) {
      console.log(resp);
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
    },
  });

  e.preventDefault();
});

// Clears the create user form
$("#clear-form").click(function (e) {
  e.preventDefault();
  $("#username").val("");
  $("#password").val("");
  $("#error-message").html("");
  $("#isAdmin").prop("checked", false);
});
