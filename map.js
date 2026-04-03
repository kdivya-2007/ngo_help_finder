function getLocationAndSubmit() {

    // alert("Function called");   
    const district = document.getElementById("district").value;

    if (district === "") {
        alert("Please select district");
        return;
    }

    if (navigator.geolocation) {

        navigator.geolocation.getCurrentPosition(function(position) {

            document.getElementById("latitude").value = position.coords.latitude;
            document.getElementById("longitude").value = position.coords.longitude;

            console.log("Latitude:", position.coords.latitude);
            console.log("Longitude:", position.coords.longitude);

            document.querySelector("form").submit();

        }, function(error) {
            alert("Please allow location access");
        });

    } else {
        alert("Geolocation not supported");
    }
}