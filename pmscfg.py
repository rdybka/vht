
class cfg():
	def __init__(self):
		self._highlight = 4
		self.on_highlight = []			# add callbacks here

		self.seq_font = "Roboto Mono Medium"
		#self.seq_font = "Ubuntu Mono"
		#self.seq_font = "Monospace"
		#self.seq_font = "LCD"
	
		self.seq_font_size = 16
		self.seq_line_width = 1.0
		self.seq_spacing = 1.05
		self.octave = 4
		self.velocity = 98
		
		self.page_height = 16
		self.skip = 1
		self.padding = 3
		self.colour = (.9, 1.0, .2)
		#self.colour = (.6, .6, 1.0)
		#self.colour = (.3, 1.0, .3)
		self.intensity_background = .3
		self.intensity_txt = .7
		self.intensity_txt_highlight = 1.0
		self.intensity_lines = .6
		self.pointer_opacity = .8
	
		self.auto_scroll_delay = .15

	@property
	def highlight(self):
		return self._highlight

	@highlight.setter
	def highlight(self, value):
		self._highlight = value
		if len(self.on_highlight):
			for cb in self.on_highlight:
				cb()
