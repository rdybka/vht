from pypms.pmstracklist import PMSTrackList

class PMSSequence():
	def __init__(self, pms, seqptr):
		self._pms_handle = pms
		self._seqptr = seqptr
		self._trk = None
	
	@property
	def trk(self):
		if self._trk == None:
			self._trk = PMSTrackList(self._pms_handle, self._seqptr)
		
		return self._trk

			
	def __str__(self):
		return "dupa"
