# proxy_dialog.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
import kytten

class StateManager():
    """StateManager ensures that only the topmost state is handling events
    for the window at a time.  States are expected to implement these
    functions:
        def on_hide_state(self, window, manager):
	    '''Called when the state is hidden, i.e. another state
	    has been pushed on top.

	    @param window The application window
	    @param manager The StateManager
	    '''

	def on_show_state(self, window, manager):
	    '''Called when the state is visible, i.e. it has just been
	    pushed or a state that was on top has been removed.

	    @param window The application window
	    @param manager The StateManager
	    '''
    """
    def __init__(self, window):
	self.window = window
	self.stack = []

    def _hide_state(self, state):
	self.window.remove_handlers(state)
	if hasattr(state, 'on_hide_state'):
	    state.on_hide_state(self.window, self)

    def _show_state(self, state):
	self.window.push_handlers(state)
	if hasattr(state, 'on_show_state'):
	    state.on_show_state(self.window, self)

    def push(self, state):
	if self.stack:
	    self._hide_state(self.stack[-1])
	self.stack.append(state)
	self._show_state(self.stack[-1])

    def pop(self):
	assert self.stack
	self._hide_state(self.stack[-1])
	retval = self.stack.pop()
	if self.stack:
	    self._show_state(self.stack[-1])
	else:
	    # no more states to show - we're done!
	    pyglet.app.exit()
	return retval

