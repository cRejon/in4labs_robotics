import os
import subprocess
import re
import threading
import time
from datetime import datetime, timezone

from flask import current_app


# Class to clean the lab before and after the user session
class cleanLab(threading.Thread):
    def __init__(self, boards, user_end_time, instance_path):
        super(cleanLab, self).__init__()
        self.boards = boards
        self.user_end_time = user_end_time
        self.instance_path = instance_path # It's not possible to access current_app inside a thread

    def clean(self):
        for board in self.boards.keys():
            usb_driver = self.boards[board]['usb_driver']
            fqbn = self.boards[board]['fqbn']
            upload_sketch(board, fqbn, usb_driver, 'stop', self.instance_path)
 
    def run(self):
        self.clean()
        remaining_secs = (self.user_end_time - datetime.now(timezone.utc)).total_seconds()
        if (remaining_secs > 0):
            time.sleep(remaining_secs)
            self.clean()    

# Function to get the serial number and USB driver of the boards 
# depending on the USB port they are connected to
def update_boards_config(boards):
    result = subprocess.run(['dmesg'], capture_output=True, text=True)
    dmesg_output = result.stdout

    # Get serial numbers
    pattern_serial = r'1-1.(\d): SerialNumber:\s(.*?)\n'
    matches_serial = re.findall(pattern_serial, dmesg_output)
    for match in matches_serial:
        for board in boards.values():
            if board['usb_port'] == match[0]:
                board['serial_number'] = match[1]
                break
    
    # Raise an exception if a board is not connected
    for board in boards.values():
        if board['serial_number'] == '':
            raise Exception(f'Board with USB port {board["usb_port"]} is not connected')
        
    # Get USB drivers
    pattern_usb = r'1-1.(\d).*?(tty\w\w\w\d)'
    matches_usb = re.findall(pattern_usb, dmesg_output)
    for match in matches_usb:
        for board in boards.values():
            if board['usb_port'] == match[0]:
                board['usb_driver'] = match[1]
                break

    return boards

def upload_sketch(board, fqbn, usb_driver, target, instance_path=None):
    # Use current_app.instance_path if instance_path is not provided
    path = instance_path or current_app.instance_path
    
    if (target == 'user'): 
        input_file = os.path.join(path, 'compilations', board, 'build','temp_sketch.ino.hex')
    else: # target == 'stop'
        input_file = os.path.join(path, 'compilations', 'precompiled','stop.ino.hex')

    command = ['arduino-cli', 'upload', '--port', f'/dev/{usb_driver}',
                 '--fqbn', fqbn, '--input-file', input_file]
    
    result = subprocess.run(command, capture_output=True, text=True) 
    return(result)        

def fill_examples(board):
    key = board[0]

    example_path = os.path.join(current_app.instance_path, 'examples', key)

    examples = []
    examples += [file for file in os.listdir(example_path) if file.endswith('.ino')]
    # Sort them alphabetically
    examples.sort()

    # Convert example names to show spaces instead of underscores and remove .ino extension 
    example_names = [example.replace('_', ' ').replace('.ino', '') for example in examples]

    examples_html = ''
    for example, example_name in zip(examples, example_names):
        if example_name == 'New Sketch':
            examples_html += f'<option value="{example}" selected="selected">{example_name}</option>\n'
        else:
            examples_html += f'<option value="{example}">{example_name}</option>\n'
    
    return examples_html

def create_navtab(board):
    key = board[0]
    name = board[1]['name'].replace(' ', '-')
    navtab_html = f'''
        <button class="nav-link {name} col-sm-4" id="nav-{key}-tab" data-bs-toggle="tab" data-bs-target="#nav-{key}" type="button" role="tab" aria-controls="nav-{key}" aria-selected="true">{name}</button>
    '''

    return navtab_html

def create_editor(board):
    key = board[0]

    examples = fill_examples(board)

    editor_html = f'''
                <div class="tab-pane fade active show" id="nav-{key}" role="tabpanel" aria-labelledby="nav-{key}-tab">
                    <div class="editor-nav">
                        <div class="row">
                            <div class="editor-examples col-sm-4">
                                <div class="btn-group editor-examples-dropdown">
                                    <select class="editor-select" id="editor-select-{key}" onchange="onLoadExample('{key}',this.value)">
                                        {examples}
                                    </select>
                                </div>
                            </div>
                            <div class="editor-cta col-sm-8">
                                <div class="editor-cta-load">
                                    <button class="upload" onclick="document.getElementById('file-input-{key}').click()" data-toggle="tooltip" data-placement="top" title="Load File"><span class="fa fa-upload"/></button>
                                    <input id="file-input-{key}" type="file" accept=".ino" style="display: none;" />
                                    <script>
                                        document.getElementById('file-input-{key}').addEventListener('change', onLoadFile, false);
                                    </script>
                                    <button class="download" onclick="onSaveFile('{key}')" data-toggle="tooltip" data-placement="top" title="Save File"><span class="fa fa-download"/></button>
                                    <button class="suggest"
                                            id="button-suggest-{key}"
                                            onclick="onSuggest('{key}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Suggest">
                                        <span class="fa fa-commenting"/>
                                    </button>
                                </div>
                                <div class="editor-cta-compile">
                                    <button class="compile"
                                            onclick="onCompileCode('{key}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Compile code">
                                        <span class="fa fa-check"/>
                                    </button>
                                    <button class="execute"
                                            id="button-execute-{key}"
                                            onclick="onExecuteCode('{key}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Run"
                                            disabled="disabled">
                                        <span class="fa fa-play-circle"/>
                                    </button>
                                    <button class="monitor"
                                            id="button-monitor-{key}"
                                            onclick="setupMonitor('{key}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Monitor"
                                            disabled="disabled">
                                        <span class="fa fa-terminal"/>
                                    </button>
                                    <button class="stop"
                                            id="button-stop-{key}"
                                            onclick="onStopExecution('{key}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Stop"
                                            disabled="disabled">
                                        <span class="fa fa-stop-circle"/>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <form id="editor-{key}">
                        <textarea id="text-{key}" name="text-{key}"></textarea>
                        <script>
                            let editor_{key} = CodeMirror.fromTextArea(document.getElementById('text-{key}'), {{
                                mode: 'text/x-c++src',
                                theme: 'neat',
                                lineNumbers: true,
                                autoCloseBrackets:true,
                            }});

                            function {key}GetEditor() {{
                                return editor_{key};
                            }}

                            onLoadExample('{key}','New_Sketch.ino');
                            
                            // Listener to trigger a function when the code changes
                            editor_{key}.on("change", function() {{ onChangeCode('{key}') }});
                        </script>
                    </form>
                </div>
    '''

    return editor_html
