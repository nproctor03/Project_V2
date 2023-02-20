const canvas = document.getElementById("screenshot");
const video = document.getElementById("video");

let analyse = false;
let face_data = [];
//let apiUrl = "http://127.0.0.1:5003//processImage";
let apiUrl = "/processimage";

//Method commented out below is deprecated. This method is the new one.
//https://www.tutorialspoint.com/how-to-open-a-webcam-using-javascript#:~:text=The%20process%20of%20opening%20a%20Webcam%201%20STEP,true%20as%20we%20will%20use%20them%20More%20items
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

// Stops the Webcam.
var stop = function () {
  var stream = video.srcObject;
  var tracks = stream.getTracks();
  for (var i = 0; i < tracks.length; i++) {
    var track = tracks[i];
    track.stop();
  }
  video.srcObject = null;
};

// Stop analysis
var stopAnalysis = function () {
  analyse = false;
};

//replaces handleScreenshot() commented out below. Method split into 2 methods (take_screenshot() and updateUI())
function take_screenshot() {
  analyse = true;

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
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      updateUI(data);
      if (analyse == true) {
        setTimeout(take_screenshot, 10);
      }
    });
}

//Receives image data and updates UI.
function updateUI(data) {
  if (data.success !== "True") {
    console.log(data.msg);
  } else if (data.success === "True" && data.FaceDetected === "False") {
    console.log("No Face Detected.");
  } else if (data.success === "True" && data.FaceDetected === "True") {
    console.log("labelled image received");
    face_data = data.face_data;
    let html = "";

    for (let i = 0; i < face_data.length; i++) {
      item = face_data[i];
      //console.log(item);
      image = item.image;
      image_name = item.name;
      //console.log(image_name);

      labels = item.labels;

      // create a list of labels to insert into DOM.
      labels.forEach((element) => {
        listItem = "<li class='font-size-s'>" + element + "</li>";
        console.log(listItem);
        html = html.concat("", listItem);
      });

      document.getElementById(image_name).src =
        "data:image/jpeg;base64," + image;
      console.log(html);

      document.getElementById("label_" + image_name).innerHTML = html;

      //This limits the number of faces that will be displayed on screen to 4. For this project it is unlikely that
      //more that 4 faces will be detected. Can be increased if neccessary.
      if (i >= 3) {
        break;
      }
    }
    //update results image. This is the origional image with faces bordered.
    document.getElementById("image_1").src =
      "data:image/jpeg;base64," + data.image_url;
  }
}

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
