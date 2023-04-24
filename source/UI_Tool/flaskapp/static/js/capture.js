const canvas = document.getElementById("screenshot");
const video = document.getElementById("video");

let analyse = false;
let face_data = [];
let apiUrl = "/processimage";

// define button constants. used later to enable/disable buttons.
const method_1_btn = document.getElementById("method_1_btn");
const method_2_btn = document.getElementById("method_2_btn");
const method_3_btn = document.getElementById("method_3_btn");

//https://www.tutorialspoint.com/how-to-open-a-webcam-using-javascript#:~:text=The%20process%20of%20opening%20a%20Webcam%201%20STEP,true%20as%20we%20will%20use%20them%20More%20items
// checks if the navigator.mediaDevices object and the getUserMedia method are both supported by the browser.
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
  navigator.mediaDevices
    .getUserMedia({ video: true })
    .then(function (stream) {
      video.srcObject = stream;
    })
    .catch(function (error) {
      console.log("Unable to access webcam");
    });
} else {
  console.log("getUserMedia not supported");
}

//Method commented out below is deprecated. This method above is the new one.
// // Checks if the browser supports userMedia method
// navigator.getUserMedia =
//   navigator.getUserMedia ||
//   navigator.webkitGetUserMedia ||
//   navigator.mozGetUserMedia ||
//   navigator.msGetUserMedia;

// if (navigator.getUserMedia) {
//   navigator
//     .getUserMedia({ video: true })
//     .then(function (stream) {
//       //set the source object of the video element to the stream of the users media device.
//       video.srcObject = stream;
//     })
//     .catch(function (error) {
//       console.log("Unable to access webcam");
//     });

// Stops the Webcam. Not Used.
// var stop = function () {
//   var stream = video.srcObject;
//   var tracks = stream.getTracks();
//   for (var i = 0; i < tracks.length; i++) {
//     var track = tracks[i];
//     track.stop();
//   }
//   video.srcObject = null;
// };

/**
 * Stops image analyses process but setting analyse = False.
 * Enables buttons.
 */
function stopAnalysis() {
  analyse = false;
  method_1_btn.disabled = false;
  method_2_btn.disabled = false;
  method_3_btn.disabled = false;
}

//replaces handleScreenshot() commented out below. Method split into 2 methods (take_screenshot() and updateUI())
function take_screenshot(method) {
  analyse = true;
  method_1_btn.disabled = true;
  method_2_btn.disabled = true;
  method_3_btn.disabled = true;

  var method_in = method;
  canvas.height = video.videoHeight;
  canvas.width = video.videoWidth;
  canvas.getContext("2d").drawImage(video, 0, 0);
  // Get the image data from the canvas
  const imageData = canvas.toDataURL("image/png");
  console.log("image taken");
  // Call Backend API.
  //https://stackoverflow.com/questions/38332701/fetch-vs-ajaxcall
  fetch(apiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      img: imageData,
      method: method,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      updateUI(data);
      if (analyse == true) {
        setTimeout(take_screenshot(method_in), 10);
      }
    });
}

/**
 *
 * Receives image data and updates UI.
 */
function updateUI(data) {
  if (data.success !== "True") {
    console.log(data.msg);
  } else if (data.success === "True" && data.FaceDetected === "False") {
    console.log("No Face Detected.");
    // Display "No Face Detected"
    for (let i = 1; i < 4; i++) {
      document.getElementById("ctn_face_" + i).style.display = "none";
      document.getElementById("not_detected_" + i).style.display = "flex";
    }
  } else if (data.success === "True" && data.FaceDetected === "True") {
    console.log("labelled image received");
    face_data = data.face_data;
    let html = "";
    // for (let i = 0; i < face_data.length; i++) {
    for (let i = 1; i < 4; i++) {
      labels = [];
      html = "";
      image_name = "";
      item = face_data[i - 1];

      if (!item) {
        // clear UI
        // console.log(i);
        document.getElementById("ctn_face_" + i).style.display = "none";
        document.getElementById("not_detected_" + i).style.display = "flex";
        continue;
      } else {
        //console.log(item);
        image = item.image;
        image_name = item.name;
        //console.log(image_name);
        labels = item.labels;
        // console.log("item labels: " + item.labels);
        // console.log("labels: " + labels);

        // create a list of labels to insert into DOM.
        labels.forEach((element) => {
          listItem = "<li class='label-font-size'>" + element + "</li>";
          // console.log(listItem);
          html = html.concat("", listItem);
        });

        document.getElementById(image_name).src =
          "data:image/jpeg;base64," + image;
        // console.log(html);

        document.getElementById("label_" + image_name).innerHTML = html;
        document.getElementById("ctn_face_" + i).style.display = "flex";
        document.getElementById("not_detected_" + i).style.display = "none";
      }
    }
    //update results image. This is the origional image with faces bordered.
    document.getElementById("image_1").src =
      "data:image/jpeg;base64," + data.image_url;
  }
}

// -----Code commented out below is an old version------

// function handleScreenshot() {
//   analyse = true;
//   canvas.height = video.videoHeight;
//   canvas.width = video.videoWidth;
//   canvas.getContext("2d").drawImage(video, 0, 0);
//   // Get the image data from the canvas
//   const imageData = canvas.toDataURL("image/png");
//   console.log("Image taken.");

//   //Call Backend API.
//   fetch("http://127.0.0.1:5003//processImage", {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//     },
//     body: JSON.stringify({
//       img: imageData,
//     }),
//   })
//     .then((response) => response.json())
//     .then((data) => {
//       if (data.success != "True") {
//         console.log(data.msg);
//       } else if (data.success === "True" && data.FaceDetected == "False") {
//         console.log("No face Detected");
//         if (analyse == true) {
//           handleScreenshot_3();
//         }
//       } else if (data.success === "True" && data.FaceDetected == "True") {
//         console.log("labelled image received");
//         face_data = data.face_data;
//         console.log(face_data);
//         let html = "";

//         for (let i = 0; i < face_data.length; i++) {
//           item = face_data[i];
//           console.log(item);
//           image = item.image;
//           name = item.name;
//           console.log(name);

//           labels = item.labels;
//           labels.forEach((element) => {
//             listItem = "<li>" + element + "</li>";
//             console.log(listItem);
//             html = html.concat("", listItem);
//           });
//           document.getElementById(name).src = "data:image/jpeg;base64," + image;
//           console.log(html);
//           document.getElementById("label_" + name).innerHTML = html;
//           // console.log("image:")
//           // console.log(image)

//           if (i >= 3) {
//             break;
//           }
//         }

//         document.getElementById("image_1").src =
//           "data:image/jpeg;base64," + data.image_url;

//         if (analyse == true) {
//           handleScreenshot_3();
//         }
//         //document.getElementById("test1").innerHTML = face_datalabels;

//         // if(analyse == true){
//         //   handleScreenshot()
//         //   }
//       }
//     });
// }
