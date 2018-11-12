import sublime
import sublime_plugin

from ..lib import omnisharp
from ..lib import helpers


class OmniSharpCodeActions(sublime_plugin.TextCommand):
    data = None
    selection = {
        "Start": {
            "Line": 0,
            "Column": 0
        },
        "End": {
            "Line": 0,
            "Column": 0
        }
    }

    def run(self, edit):
        if self.data is None:

            selection = self.view.sel()
            
            params = {}

            if len(selection) > 0:
                print('length is : ' + str(len(selection)))
                location = selection[0]
                cursor = self.view.rowcol(location.begin())
                
                self.selection["Start"]["Line"] = cursor[0] + 1
                self.selection["Start"]["Column"] = cursor[1] + 1

                othercursor = self.view.rowcol(location.end())
                self.selection["End"]["Line"] = othercursor[0] + 1
                self.selection["End"]["Column"] = othercursor[1] + 1

                params['Selection'] = self.selection

            omnisharp.get_response(
                self.view, '/v2/getcodeactions', self._handle_codeactions, params)
        else:
            self._show_code_actions_view(edit)

    def _handle_codeactions(self, data):
        print(data)
        if data is None:
            return
        self.data = data
        self.view.run_command('omni_sharp_code_actions')

    def _show_code_actions_view(self, edit):
        print('codeactions is :')
        print(self.data)
        self.quickitems = [];
        self.quickitemids = [];
        if "CodeActions" in self.data and self.data["CodeActions"] != None:
            for i in self.data["CodeActions"]:
                print(i)
                self.quickitems.append(i["Name"])
                self.quickitemids.append(i["Identifier"])
        if len(self.quickitems) > 0:
            self.view.show_popup_menu(self.quickitems, self.on_done)
        else:
            self.data = None
            self.selection["End"]["Line"] = 0
            self.selection["End"]["Column"] = 0
            self.selection["Start"]["Line"] = 0
            self.selection["Start"]["Column"] = 0

    def is_enabled(self):
        return helpers.is_csharp(self.view)

    def on_done(self, index):
        if index == -1:
            self.data = None
            self.selection["End"]["Line"] = 0
            self.selection["End"]["Column"] = 0
            self.selection["Start"]["Line"] = 0
            self.selection["Start"]["Column"] = 0
            return

        print("run index: " + str(index))

        params = {}
        params['Identifier'] = self.quickitemids[index]
        params['Selection'] = self.selection
        params['WantsTextChanges'] = True
        params['WantsAllCodeActionOperations'] = True
        omnisharp.get_response(self.view, '/v2/runcodeaction', self._handle_runcodeaction, params)
        self.data = None
        self.selection["End"]["Line"] = 0
        self.selection["End"]["Column"] = 0
        self.selection["Start"]["Line"] = 0
        self.selection["Start"]["Column"] = 0
        
    def _handle_runcodeaction(self, data):
        print('runcodeaction is:')
        print(data)
        if data is None:
            return
        
        for change in data['Changes']:
            self.view.run_command("omni_sharp_run_code_action",{"args":{'change':change}})

class OmniSharpRunCodeAction(sublime_plugin.TextCommand):
  def run(self, edit, args):
    view = self.view.window().open_file(args['change']['FileName'])

    while(view.is_loading()):
        pass

    for change in args['change']['Changes']:
        region = sublime.Region(
            view.text_point(change['StartLine'] - 1, change['StartColumn'] - 1),
            view.text_point(change['EndLine'] - 1, change['EndColumn'] - 1)
        )

        view.replace(edit, region, change['NewText'])
