from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

class AuraTUI:
    def __init__(self):
        self.layout = Layout()
        self.songs = []
        self.status = 'Listening...'
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_rows = 15
        self._dirty = False
        self._setup_layout()
    
    def _setup_layout(self):
        self.layout.split(
            Layout(name='header', size=3),
            Layout(name='main', ratio=1),
            Layout(name='footer', size=3)
        )
        self.layout['main'].split_row(
            Layout(name='songs', ratio=2),
            Layout(name='sidebar', ratio=1)
        )
    
    def add_song(self, song_info):
        if 'time' not in song_info:
            from datetime import datetime
            song_info['time'] = datetime.now().strftime('%H:%M:%S')
        self.songs.append(song_info)
        self.selected_index = len(self.songs) - 1
        self._dirty = True
    
    def set_status(self, status):
        self.status = status
        self._dirty = True
    
    def render(self):
        # Build panels
        self.layout['header'].update(Panel('â™ª AURA', style='cyan'))
        self.layout['footer'].update(Panel(self.status, style='cyan'))
        
        # Songs table
        table = Table(show_header=True, header_style='bold cyan')
        table.add_column('ID', width=5)
        table.add_column('Song', no_wrap=True)
        table.add_column('Artist', no_wrap=True)
        
        for i, song in enumerate(self.songs):
            style = 'on blue' if i == self.selected_index else ''
            table.add_row(
                f\"#{song.get('id', i)}\",
                song.get('title', 'Unknown')[:30],
                song.get('artist', 'Unknown')[:25],
                style=style
            )
        
        self.layout['songs'].update(Panel(table, title='Detected Songs'))
        return self.layout
    
    def needs_render(self):
        return self._dirty
    
    def mark_rendered(self):
        self._dirty = False
