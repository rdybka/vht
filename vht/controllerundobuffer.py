class ControllerUndoBuffer():
	def __init__(self, trk, ctrlnum):
		self._trk = trk
		self._ctrlnum = ctrlnum
		self._states = []
		self._state = {}

		self._dstates = []
		self._dstate = {}

		self._states.append({})
		self._dstates.append({})
		self.add_state()

	def add_state(self):
		state = {}
		for r, rr in enumerate(self._trk.ctrl[self._ctrlnum]):
			if rr.velocity != -1:
				state[r] = (rr.velocity, rr.linked, rr.anchor, rr.smooth)

		if len(self._states):
			s = self._state
			for k in s.keys():
				if k in state:
					if state[k] == s[k]:
						del state[k]
				else:
					state[k] = 0

		if len(state):
			self._states.append(state)
			self._dstates.append({})

		for k in state.keys():
			self._state[k] = state[k]
			if state[k] == 0:
				del self._state[k]

		dstate = {}
		for r, rr in enumerate(self._trk.ctrl[self._ctrlnum]):
			dstate[r] = self._trk.get_ctrl_rec(self._ctrlnum, r)

		if len(self._dstates):
			s = self._dstate
			for k in s.keys():
				if k in dstate:
					if dstate[k] == s[k]:
						del dstate[k]
				else:
					dstate[k] = 0

		if len(dstate):
			self._dstates.append(dstate)
			self._states.append({})

		for k in dstate.keys():
			self._dstate[k] = dstate[k]
			if dstate[k] == 0:
				del self._dstate[k]

	def restore(self):
		if len(self._states) > 1:
			del self._states[-1]

			self._state = {}
			for s in self._states:
				for k in s.keys():
					self._state[k] = s[k]
					if s[k] == 0:
						del self._state[k]

			x = self._ctrlnum
			self._trk.ctrl[x].clear()

			for y, r in enumerate(self._trk.ctrl[x]):
				if y in self._state.keys():
					r = self._state[y]
					if r == 0:
						self._trk.ctrl[x][y].clear()
					else:
						self._trk.ctrl[x][y].velocity = r[0]
						self._trk.ctrl[x][y].linked = r[1]
						self._trk.ctrl[x][y].anchor = r[2]
						self._trk.ctrl[x][y].smooth = r[3]

		if len(self._dstates) > 1:
			del self._dstates[-1]

			self._dstate = {}
			for s in self._dstates:
				for k in s.keys():
					self._dstate[k] = s[k]

			dpr = self._trk.ctrlpr

			for y, r in enumerate(self._trk.ctrl[self._ctrlnum]):
				if y in self._dstate.keys():
					r = self._dstate[y]
					for yy in range(dpr):
						self._trk.set_ctrl(self._ctrlnum, (dpr * y) + yy, r[yy])

