/**
 * Script with functions to perform the actions needed for the interaction with the user.
 */


function getEditor(board) {
    var editorFunction = board + "GetEditor";
    if (typeof window[editorFunction] === "function") {
        return window[editorFunction]();
    } 
}

/**
 * Function that selects one example from a set of local predefined example files and loads in into
 * the editor.
 */
function onLoadExample(board, example) {

    // Load the file into the editor
    $.ajax({
        type: "GET",
        url: "get_example",
        data: {board:board, example:example},
        dataType: "text",
        success: function(response) {
            let editor = getEditor(board);
            editor.setValue(response);
        }
    });
}


/**
 * Function that is triggered when the user wants to load a file using the 'input' html object.
 *
 * @param evt, the event of the 'input' object when it is changed (file selected)
 */
function onLoadFile(evt) {
    
    let board = evt.target.id.split('-')[2];
    // Check API support
    if (window.File && window.FileReader && window.FileList && window.Blob) {
        // Get the last selected file
        let file = evt.target.files[0];
        if (file) {

            // Check the extension of the selected file
            let fileName = file.name;
            let fileExtension = fileName.split('.')[fileName.split('.').length - 1].toLowerCase();
            if (fileExtension != 'ino') {
                window.alert('The selected file must be a valid *.ino sketch!')
                return;
            }

            // Read the file
            let fr = new FileReader();
            fr.onload = function(e) {
                let contents = e.target.result;
                let editor = getEditor(board);
                editor.setValue(contents);
                document.getElementById('editor-select-'.concat(board)).value = 'new';
            }

            fr.readAsText(file);
        }
    }
}

/**
 * Function that is triggered when the user wants to save the text in the code editor in a file.
 */
function onSaveFile(board) {
   
    let text = getEditor(board).getValue();
    let blob = new Blob([text], {type:'text/plain'});
    let fileName = 'Sketch.ino';

    let downloadLink = document.createElement("a");
    downloadLink.download = fileName;
    downloadLink.innerHTML = 'Download File';
    
    if (window.webkitURL != null) {
        downloadLink.href = window.webkitURL.createObjectURL(blob);
    } else  {
        downloadLink.href = window.URL.createObjectURL(blob);
        downloadLink.style.display = 'none';
        document.body.appendChild(downloadLink);
    }

    downloadLink.click();
}

/**
 * Function that is triggered when the user wants to compile the code.
 */
function onCompileCode(board) {

    // Get the text from the editor and encode it. End of Lines are represented as "//NL"
    //let text = getEditor().getValue("//NL"); // TODO: check if this is needed
    let text = getEditor(board).getValue();

    // Send the text through an Ajax Post
    $.ajax({
        type: "POST",
        url: "compile",
        data: {board:board, text:text},
        success: compilationFeedback,
        error: ajaxError
    });

    // Display loader animation
    let loader = $('#loader-bg');
    loader.show();
}

/**
 * Function that is triggered when the user wants to execute the compiled code
 */
function onExecuteCode(board) {

    // Send the instruction through an Ajax Post
    $.ajax({
        type: "POST",
        url: "execute",
        data: {board:board, target:"user"},
        success: executionFeedback,
        error: ajaxError
    });

    // Display loader animation
    let loader = $('#loader-bg');
    loader.show();
}

function setupMonitor(board) {

    $('#modal_dialog').addClass('modal-sm');
    $('#modal_message').modal('show');
    let setup = $('#modal-setup-monitor');
    setup.show();
    $('#modal-msg').text(messages.SERIAL_OUTPUT_CONFIG);

    $('#modal_message').one('hidden.bs.modal', function() {
        $('#modal_dialog').removeClass('modal-sm');
        setup.hide();
        let baudrate = $('#baudrate-select').val();
        let seconds = $('#seconds-select').val();
        onMonitor(board, baudrate, seconds);
    })
}

/**
 * Function that is triggered when the user wants to monitor the serial output
 */
function onMonitor(board, baudrate, seconds) {

    // Send the instruction through an Ajax Post
    $.ajax({
        type: "GET",
        url: "monitor",
        data: {board:board, baudrate:baudrate, seconds:seconds},
        success: monitoringFeedback,
        error: ajaxError
    });

    // Display loader animation
    let loader = $('#loader-bg');
    loader.show();
}

/**
 * Function that is triggered when the user wants to get suggestions for the code with ChatGPT
 */
function onSuggest(board) {

    let text = getEditor(board).getValue();

    $.ajax({
        type: "POST",
        url: "suggest",
        data: {board:board, text:text},
        success: suggestionFeedback,
        error: ajaxError
    });

    // Display loader animation
    let loader = $('#loader-bg');
    loader.show();
}

/**
 * Function that is triggered when the user wants to stop the program execution
 */
function onStopExecution(board) {

    // Send the instruction through an Ajax Post
    $.ajax({
        type: "POST",
        url: "execute",
        data: {board:board, target:"stop"}
    });

    // Disable the stop execution button
    $('#button-stop-'+board).prop('disabled', true);

    $('#button-monitor-'+board).prop('disabled', true);
}

/**
 * Function that is triggered when the user wants to reset the lab
 */
function onResetLab() {

    // Send the instruction through an Ajax Post
    $.ajax({
        type: "GET",
        url: "reset_lab",
        success: resetLabFeedback,
        error: ajaxError
    });

    $('button.execute').prop('disabled',true);
    $('button.monitor').prop('disabled',true);
    $('button.stop').prop('disabled',true);

    // Display loader animation
    let loader = $('#loader-bg');
    loader.show();
}

/**
 * Function that is executed once a compilation process has been performed in the back-end.
 *
 * @param errorMsg, contains a message in case there are compilation errors, otherwise it is null.
 */
function compilationFeedback(response) {

    // Hide loader animation
    let loader = $('#loader-bg');
    loader.hide();

    let board = response.board
    let error = response.error
    // If there are errors
    if (error) {
        // Print the error message
        $('#modal_dialog').addClass('modal-xl');
        $('#modal_message').modal('show');
        $('#modal-msg').text(messages.COMPILATION_ERROR).after('<pre>' + error + '</pre>');

        $('#modal_message').on('hidden.bs.modal', function() {
            $('#modal_message pre').remove();
            $('#modal_dialog').removeClass('modal-xl');
        })
    } else {
        // Enable the execution button after a successful compilation
        $('#button-execute-'+board).prop('disabled', false);
    }
}


/**
 * Function that is executed once a program execution process has been performed in the back-end.
 *
 * @param response, contains the board used.
 */
function executionFeedback(response) {

    // Hide loader animation
    let loader = $('#loader-bg');
    loader.hide();

    let board = response.board
    
    // Enable the monitor button after a successful execution
    $('#button-monitor-'+board).prop('disabled', false);

    // Enable the stop execution button after a successful execution
    $('#button-stop-'+board).prop('disabled', false);
}

/**
 * Function that is executed once a monitoring process has been performed in the back-end.
 *
 * @param response, contains the board used and the serial monitor result.
 */
function monitoringFeedback(response) {

    // Hide loader animation
    let loader = $('#loader-bg');
    loader.hide();

    let board = response.board
    let output = response.output

    // Print the monitor result in the modal
    $('#modal_dialog').addClass('modal-lg');
    $('#modal_message').modal('show');
    $('#modal-msg').text(messages.SERIAL_OUTPUT).after('<pre>' + output + '</pre>');
    
    $('#modal_message').on('hidden.bs.modal', function() {
        $('#modal_message pre').remove();
        $('#modal_dialog').removeClass('modal-lg');
    })
}

/**
 * Function that is executed once a monitoring process has been performed in the back-end.
 *
 * @param response, contains the board used and the serial monitor result.
 */
function suggestionFeedback(response) {

    // Hide loader animation
    let loader = $('#loader-bg');
    loader.hide();

    let board = response.board
    let suggestion = response.suggestion

    $('#modal_dialog').addClass('modal-xl');
    $('#modal_message').modal('show');
    $('#modal-msg').text(messages.SUGGEST).after('<pre>' + suggestion + '</pre>');
    
    $('#modal_message').on('hidden.bs.modal', function() {
        $('#modal_message pre').remove();
        $('#modal_dialog').removeClass('modal-xl');
    })
}

/**
 * Function that is executed once a reset lab process has been performed in the back-end.
 *
 * @param response, contains the board used and the serial monitor result.
 */
function resetLabFeedback(response) {

    // Hide loader animation
    let loader = $('#loader-bg');
    loader.hide();

    $('#modal_message').modal('show');
    $('#modal-msg').text(messages.RESET_LAB);
}

/**
 * Function that is executed in case that an ajax operation finishes abnormally.
 */
function ajaxError() {

    // Hide loader animation
    let loader = $('#loader-bg');
    loader.hide();

    // Back-end error
    $('#modal_message').modal('show');
    $('#modal-msg').text(messages.UNEXPECTED_ERROR);
}
