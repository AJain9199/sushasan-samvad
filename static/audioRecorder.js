function recordAudio(submit_callback) {

    const recButton = document.getElementById("rec");
    const output = document.getElementById("audioPlayer");
    const subButton = document.getElementById("sub");

    output.hidden = true;
    let audioRecorder;
    let formData = new FormData();
    let started = false;

    navigator.mediaDevices.getUserMedia({audio: true})
        .then(stream => {

            // Initialize the media recorder object
            audioRecorder = new MediaRecorder(stream);

            // dataavailable event is fired when the recording is stopped
            audioRecorder.addEventListener('dataavailable', e => {
                formData.set("audio", e.data, "audio.webm");
                output.src = URL.createObjectURL(e.data);
            });

            // start recording when the start button is clicked
            recButton.addEventListener('click', () => {
                if (started) {
                    audioRecorder.stop();
                    recButton.innerHTML = `<a style="font-size: 25px;">Start RecordingðŸŽ™ï¸</a>`;
                    output.hidden = false;
                } else {
                    audioRecorder.start();
                    recButton.innerHTML = `<a style="font-size: 25px;">Stop Recording</a>`;
                    output.hidden = true;
                }
                started = !started;
            });

            // play the recorded audio when the play button is clicked
            subButton.addEventListener('click', () => {
		submit_callback();
                $.ajax({
                    method: 'POST',
                    processData: false,
                    mimeType: 'multipart/form-data',
                    contentType: false,
                    data: formData,
                    async: false,
                    success: (data, textSuccess) => {
                        window.location = (JSON.parse(data)).url;
                    }
                });
            });
        });
}
