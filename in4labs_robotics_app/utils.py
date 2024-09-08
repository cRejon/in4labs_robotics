import os
import subprocess
import re

from flask import current_app


def get_serial_number(boards):
    result = subprocess.run(['dmesg'], capture_output=True, text=True)
    dmesg_output = result.stdout

    pattern = r'1-1.(\d): SerialNumber:\s(.*?)\n'
    matches = re.findall(pattern, dmesg_output)

    for match in matches:
        for board in boards.values():
            if board['usb_port'] == match[0]:
                board['serial_number'] = match[1]
                break

    return boards

def get_usb_driver(boards):
    result = subprocess.run(['dmesg'], capture_output=True, text=True)
    dmesg_output = result.stdout

    pattern = r'1-1.(\d).*?(tty\w\w\w\d)'
    matches = re.findall(pattern, dmesg_output)

    for match in matches:
        for board in boards.values():
            if board['usb_port'] == match[0]:
                board['usb_driver'] = match[1]
                break

    return boards

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
    name = board[1]['name'].lower().replace(' ', '-')
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
                            onStopExecution('{key}');
                            
                            // Listener to trigger a function when the code changes
                            editor_{key}.on("change", function() {{ onChangeCode('{key}') }});
                        </script>
                    </form>
                </div>
    '''

    return editor_html
