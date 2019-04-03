from PyQt5.QtWidgets import QMenu, QAction

class DictMenu(QMenu):
    ''' A wrapper around QMenu allowing definition of nested menus with only a
        dictionary argument, examples of which are shown as follows.

        Single-level menu:
            menu = {'option1', method1, 'option2', method2}
        Moving method2 into a nested sublevel:
            menu = {'option1', method1, 'sublevel': {'option2', method2}}
    '''
    def __init__(self, menu):
        super().__init__()
        self.actions = {}
        self.add_actions(from_dict=menu, to_dict=self.actions, to_menu=self)

    def add_actions(self, from_dict, to_dict, to_menu):
        ''' Adds all non-dict entries as actions. Dictionary entries, representing
            sublevels, are passed recursively back into this method. '''
        for item in from_dict:
            if not isinstance(from_dict[item], dict):
                to_dict[item] = QAction(item)
                to_dict[item].triggered.connect(from_dict[item])
                to_menu.addAction(to_dict[item])
            else:
                new_level = to_menu.addMenu(item)
                self.actions[item] = {}
                self.add_actions(from_dict[item], self.actions[item], new_level)
