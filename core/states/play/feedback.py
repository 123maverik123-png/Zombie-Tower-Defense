# core/states/play/feedback.py

class PlayFeedback:
    def __init__(self, state):
        self.state = state
    
    def show_error(self, x, y, msg):
        state = self.state
        state.build_error = True
        state.build_error_pos = (x, y)
        state.build_error_timer = 0.5
        state.build_error_msg = msg
    
    def show_success(self, x, y):
        state = self.state
        state.build_success = True
        state.build_success_pos = (x, y)
        state.build_success_timer = 0.3
    
    def update(self, dt):
        state = self.state
        if state.build_error:
            state.build_error_timer -= dt
            if state.build_error_timer <= 0:
                state.build_error = False
        if state.build_success:
            state.build_success_timer -= dt
            if state.build_success_timer <= 0:
                state.build_success = False