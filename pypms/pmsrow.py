
class PMSRow():
	def __init__(self, pms, rowptr):
		self._pms_handle = pms
		self._rowptr = rowptr
		
		self._type = pms.row_get_type(self._rowptr)
		self._note = pms.row_get_note(self._rowptr)
		self._velocity = pms.row_get_velocity(self._rowptr)		
		self._delay = pms.row_get_delay(self._rowptr)
		self.update_strrep()
		
	def __eq__(self, other):
		if self._type != other._type:
			return False
		if self._note != other._note:
			return False
		if self._velocity != other._velocity:
			return False
		if self._delay != other._delay:
			return False
			
		return True

	def update_strrep(self):
		notes = ['C-', 'C#' , 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']
		note = self._note % 12
		octave = self._note // 12
		if self._type == 1: #note_on
			self._strrep = notes[note]+str(octave)
			return
			
		if self._type == 2: #note_off
			self._strrep = "  ===" 
			return
		
		self._strrep = "---"
	
	def copy(self, row):
		self._type = row._type
		self._note = row._note
		self._velocity = row._velocity
		self._delay = row._delay
		self._pms_handle.row_set(self._rowptr, self._type, self._note, self._velocity, self._delay)
		self.update_strrep()
		
	def clear(self):
		self._type = 0
		self._note = 0
		self._velocity = 0
		self._delay = 0
		self._pms_handle.row_set(self._rowptr, 0, 0, 0, 0)
		self.update_strrep()
	
	@property
	def type(self):
		return self._type
	
	@type.setter
	def type(self, value):
		self._type = value
		self._pms_handle.row_set_type(self._rowptr, self._type)

	@property
	def note(self):
		return self._note
	
	@note.setter
	def note(self, value):
		if isinstance(value, int):
			self._note = value
			self._pms_handle.row_set_note(self._rowptr, self._note)
		
		if isinstance(value, str):
			self._note = self._pms_handle.parse_note(value)
			self._pms_handle.row_set_note(self._rowptr, self._note)
			self.type = 1
			if self.velocity == 0:
				self.velocity = 100
		
		self.update_strrep()
						
	@property
	def velocity(self):
		return self._velocity
	
	@velocity.setter
	def velocity(self, value):
		self._velocity = int(value)
		self._pms_handle.row_set_velocity(self._rowptr, self._velocity)

	@property
	def delay(self):
		return self._delay
	
	@delay.setter
	def delay(self, value):
		self._delay = int(value)
		self._pms_handle.row_set_delay(self._rowptr, self._delay)

	def __str__(self):
		return self._strrep
