
/**
 * Function that is triggered when the code in the editor changes.
 */
function onChangeCode(board) {

    // When the code is changed, disable the execute button so that it must be compiled again
    $('#button-execute-'+board).prop('disabled', true);
    $('#button-monitor-'+board).prop('disabled', true);
}

/**
 * Function for the countdown timer. 
*/
function countdownTimer(end_time) {

    // Update the timer every second
    let countdown = setInterval(() => {
        // Get the current date and time
        let currentDate = new Date().getTime();

        // Calculate the remaining time in milliseconds
        let remainingTime = end_time - currentDate;

        // Alert the user when the remaining time is close to be expired
        if (remainingTime <= 30 * 1000) {
            $(".timer").addClass("red"); 
        }

        // Check if the countdown is finished
        if (remainingTime <= 0) {
            clearInterval(countdown);   
            // Disable actions
            $('select.editor-select').prop('disabled',true);
            $('button.upload').prop('disabled',true);
            $('button.suggest').prop('disabled',true);
            $('button.compile').prop('disabled',true);
            $('button.execute').prop('disabled',true);
            $('button.monitor').prop('disabled',true);
            $('button.stop').prop('disabled',true);
            // Notify the user
            $('#modal_message').modal('show');
            $('#modal-msg').text(messages.SESSION_EXPIRED);
            $('#camera').prepend('<div class="session_blocked"><p>' + messages.SESSION_EXPIRED + '</p></div>');
            $('#cam').prop('src', '');
        return;
        }

        // Convert the remaining time to minutes and seconds
        let minutes = Math.floor((remainingTime / 1000 / 60) % 60);
        let seconds = Math.floor((remainingTime / 1000) % 60);

        // Format the time display
        let display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        // Update the HTML element with the timer value
        $("#timer-count").text(display);
    }, 1000);
}
