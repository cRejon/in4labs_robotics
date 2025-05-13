import os

from flask import current_app


def fill_examples(board):
    board_path = os.path.join(current_app.instance_path, 'examples', board)
    commons_path = os.path.join(current_app.instance_path, 'examples', 'Commons')

    examples = []
    for path in [board_path, commons_path]:
        if os.path.isdir(path):
            examples += [file for file in os.listdir(path) if file.endswith('.ino')]

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

def create_navtab(board_conf):
    board = board_conf[0]
    config = board_conf[1]

    name = config['name'].replace(' ', '-')

    navtab_html = f'''
        <button class="nav-link {name.lower()} col-sm-4" id="nav-{board}-tab" data-bs-toggle="tab" data-bs-target="#nav-{board}" type="button" role="tab" aria-controls="nav-{board}" aria-selected="true">{name}</button>
    '''

    return navtab_html

def create_editor(board_conf):
    board = board_conf[0]

    examples = fill_examples(board)

    editor_html = f'''
                <div class="tab-pane fade active show" id="nav-{board}" role="tabpanel" aria-labelledby="nav-{board}-tab">
                    <div class="editor-nav">
                        <div class="row">
                            <div class="editor-examples col-sm-4">
                                <div class="btn-group editor-examples-dropdown">
                                    <select class="editor-select" id="editor-select-{board}" onchange="onLoadExample('{board}',this.value)">
                                        {examples}
                                    </select>
                                </div>
                            </div>
                            <div class="editor-cta col-sm-8">
                                <div class="editor-cta-load">
                                    <button class="upload" onclick="document.getElementById('file-input-{board}').click()" data-toggle="tooltip" data-placement="top" title="Load File"><span class="fa fa-upload"/></button>
                                    <input id="file-input-{board}" type="file" accept=".ino" style="display: none;" />
                                    <script>
                                        document.getElementById('file-input-{board}').addEventListener('change', onLoadFile, false);
                                    </script>
                                    <button class="download" onclick="onSaveFile('{board}')" data-toggle="tooltip" data-placement="top" title="Save File"><span class="fa fa-download"/></button>
                                    <button class="suggest"
                                            id="button-suggest-{board}"
                                            onclick="onSuggest('{board}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Suggest">
                                        <span class="fa fa-commenting"/>
                                    </button>
                                </div>
                                <div class="editor-cta-compile">
                                    <button class="compile"
                                            onclick="onCompileCode('{board}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Compile code">
                                        <span class="fa fa-check"/>
                                    </button>
                                    <button class="execute"
                                            id="button-execute-{board}"
                                            onclick="onExecuteCode('{board}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Run"
                                            disabled="disabled">
                                        <span class="fa fa-play-circle"/>
                                    </button>
                                    <button class="monitor"
                                            id="button-monitor-{board}"
                                            onclick="setupMonitor('{board}')"
                                            data-toggle="tooltip"
                                            data-placement="top"
                                            title="Monitor"
                                            disabled="disabled">
                                        <span class="fa fa-terminal"/>
                                    </button>
                                    <button class="stop"
                                            id="button-stop-{board}"
                                            onclick="onStopExecution('{board}')"
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
                    <form id="editor-{board}">
                        <textarea id="text-{board}" name="text-{board}"></textarea>
                        <script>
                            let editor_{board} = CodeMirror.fromTextArea(document.getElementById('text-{board}'), {{
                                mode: 'text/x-c++src',
                                theme: 'neat',
                                lineNumbers: true,
                                autoCloseBrackets:true,
                            }});

                            function {board}GetEditor() {{
                                return editor_{board};
                            }}

                            onLoadExample('{board}','New_Sketch.ino');
                            
                            // Listener to trigger a function when the code changes
                            editor_{board}.on("change", function() {{ onChangeCode('{board}') }});
                        </script>
                    </form>
                </div>
    '''

    return editor_html
