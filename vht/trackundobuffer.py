
class TrackUndoBuffer():
	def __init__(self, trk):
		self._trk = trk
		self._states = []
		self._state = {}
		
		self._states.append({})
						
	def add_state(self, add_if_empty = False):
		state = {}
		for x, c in enumerate(self._trk):
			for y, r in enumerate(c):
				if r.type:
					state[(x, y)] = (r.type, r.note, r.velocity, r.delay)
		
		if len(self._states):
			s = self._state
			for k in s.keys():
				if k in state:
					if state[k] == s[k]:
						del state[k]
				else:
					state[k] = 0
		
		if len(state) or add_if_empty:
			self._states.append(state)

		for k in state.keys():
			self._state[k] = state[k]
			if state[k] == 0:
				del self._state[k]
		
	def restore(self):
		if len(self._states) == 1:
			return
			
		del self._states[-1]
		
		self._state = {}
		for s in self._states:
			for k in s.keys():
				self._state[k] = s[k]
				if s[k] == 0:
					del self._state[k]
	
		cols = 0
		for k in self._state.keys():
			if k[0] > cols:
				cols = k[0]
		
		cols += 1
		
		self._trk.clear()
		while len(self._trk) < cols:
			self._trk.add_column()
		
		for x, c in enumerate(self._trk):
			for y, r in enumerate(c):
				if (x, y) in self._state.keys():
					r = self._state[(x, y)]
					if r == 0:
						self._trk[x][y].clear()
					else:
						self._trk[x][y].type = r[0]
						self._trk[x][y].note = r[1]
						self._trk[x][y].velocity = r[2]
						self._trk[x][y].delay = r[3]
