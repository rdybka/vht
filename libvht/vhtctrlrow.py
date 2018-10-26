
class VHTCtrlRow():
	def __init__(self, vht, crowptr, dummy = False):
		self._vht_handle = vht
		self._crowptr = crowptr
		self._dummy = dummy

		self._velocity = vht.ctrlrow_get_velocity(self._crowptr)		
		self._linked = vht.ctrlrow_get_linked(self._crowptr)
		self._smooth = vht.ctrlrow_get_smooth(self._crowptr)
		self._anchor = vht.ctrlrow_get_anchor(self._crowptr)

		self.update_strrep()
		
	def __eq__(self, other):
		if other == None:
			return False
			
		if self._velocity != other._velocity:
			return False
		if self._linked != other._linked:
			return False
		if self._linked != other._smooth:
			return False
		if self._anchor != other._anchor:
			return False
			
		return True

	def update_strrep(self):
		lnk = " "
		if self._linked == 1:
			lnk = "L"

		if self._velocity > -1:
			self._strrep = "%3d %s %d %d" % (self._velocity, lnk, self._smooth, self._anchor) 
		else:
			self._strrep = "--- - - -"
	
	def copy(self, row):
		self._velocity = row._velocity
		self._linked = row._linked
		self._smooth = row._smooth
		self._anchor = row._anchor
		if not self._dummy:
			self._vht_handle.ctrlrow_set(self._crowptr, self._velocity, self._linked, self._smooth, self.anchor)
		self.update_strrep()
		
	def clear(self):
		self._velocity = -1
		self.linked = 0
		self.smooth = 0
		self.anchor = 0
		if not self._dummy:
			self._vht_handle.ctrlrow_set(self._crowptr, -1, 0, 0, 0)
		self.update_strrep()

	def dummy(self):
		return VHTCtrlRow(self._vht_handle, self._crowptr, True)
						
	@property
	def velocity(self):
		return self._velocity
	
	@velocity.setter
	def velocity(self, value):
		self._velocity = int(value)

		if not self._dummy:
			self._vht_handle.ctrlrow_set_velocity(self._crowptr, self._velocity)

	@property
	def linked(self):
		return self._linked
	
	@linked.setter
	def linked(self, value):
		self._linked = int(value)
		if not self._dummy:
			self._vht_handle.ctrlrow_set_linked(self._crowptr, self._linked)

	@property
	def smooth(self):
		return self._smooth
	
	@smooth.setter
	def smooth(self, value):
		self._smooth = int(value)
		if not self._dummy:
			self._vht_handle.ctrlrow_set_smooth(self._crowptr, self._smooth)

	@property
	def anchor(self):
		return self._anchor
	
	@anchor.setter
	def anchor(self, value):
		self._anchor = int(value)
		if not self._dummy:
			self._vht_handle.ctrlrow_set_anchor(self._crowptr, self._anchor)

	def __str__(self):
		return self._strrep

