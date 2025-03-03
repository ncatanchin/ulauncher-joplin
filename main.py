import logging
import json
import requests

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, SystemExitEvent, PreferencesUpdateEvent, \
    PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

logger = logging.getLogger(__name__)

# Using the REST-Api of Joplin: https://joplinapp.org/api/references/rest_api/
class JoplinExtension(Extension):
    def __init__(self):
        super(JoplinExtension, self).__init__()

        # Number of notebooks that should be suggested
        self.limit = None

        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(SystemExitEvent, SystemExitEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

    def add_note(self, note):
        requests.post('http://localhost:41184/notes?token=5f99742799fac18bff82a173cfca2b6ea509f37b6b05dd6b47c2e4d6c7ce76fa8399ee4025325e87a44fdf2b781c0d631e25146fc1a010f6b1ebffb34ab7652f', json.dumps({
            'title': note['text'],
            'is_todo': note['type'] == 'todo',
            'parent_id': note['notebookId']
        }))

    def get_notebooks(self, query):
        # response = requests.get('http://localhost:41184/folders?token=5f99742799fac18bff82a173cfca2b6ea509f37b6b05dd6b47c2e4d6c7ce76fa8399ee4025325e87a44fdf2b781c0d631e25146fc1a010f6b1ebffb34ab7652f')
        response = requests.get('http://localhost:41184/search?query='+query+'*&type=folder&token=5f99742799fac18bff82a173cfca2b6ea509f37b6b05dd6b47c2e4d6c7ce76fa8399ee4025325e87a44fdf2b781c0d631e25146fc1a010f6b1ebffb34ab7652f')
        
        return json.loads(response.content)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        extension.add_note(event.get_data())


class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        try:
            n = int(event.preferences['limit'])
        except:
            n = 10
        extension.limit = n


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event, extension):
        if not event.id == 'limit':
            pass

        try:
            n = int(event.new_value)
            extension.limit = n
        except:
            pass


class SystemExitEventListener(EventListener):
    def on_event(self, event, extension):
        extension.close()


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        keyword = event.get_keyword()
        query = event.get_argument()

        if query == None:
            return None

        notebooks = extension.get_notebooks(query)
        logging.error(notebooks)
        
        # Sort by note count. The notebook with the most notes should be on top.
        # notebooks.sort(key=lambda x: x['note_count'], reverse=True)

        results = []

        print(extension.limit)

        for notebook in notebooks["items"][:extension.limit]:
            data = {
                'text': query,
                'type': keyword,
                'notebookId': notebook['id']
            }
            results.append(ExtensionResultItem(icon='images/icon.png',
                                               name="Add %s to notebook %s" % (keyword, notebook['title']),
                                               on_enter=ExtensionCustomAction(data, keep_app_open=False)))

        return RenderResultListAction(results)


if __name__ == '__main__':
    JoplinExtension().run()
