from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.columns import Columns
import asyncio
import threading

if TYPE_CHECKING:
    from rich.live import Live as LiveType


class ShazamTUI:
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.songs: List[Dict[str, Any]] = []
        self.status = "Listening..."
        self.show_help = True
        self._dirty = False
        self._force_render = False  # For immediate high-priority updates
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_rows = 15  # Initial value, recalculated on render
        self._status_lock = threading.Lock()
        self._running_tasks: List[asyncio.Task] = []
        self.max_songs = 500
        
        self._cached_header: Optional[Panel] = None
        self._cached_help: Optional[Panel] = None
        self._last_status = ""
        self._last_song_count = 0
        self._last_selected = -1
        self._last_scroll = -1
        
        self._setup_layout()
    
    def _calculate_visible_rows(self) -> int:
        """Recalculate visible rows based on current terminal size"""
        try:
            height = self.console.height
            available_height = height - 14
            return max(5, available_height)
        except Exception:
            return 15
    
    def _setup_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="songs", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
    
    def _make_header(self) -> Panel:
        """Create header panel with caching"""
        if self._cached_header is not None:
            return self._cached_header
            
        header_text = Text()
        header_text.append("♪ SHAZAM LIVE", style="bold cyan")
        header_text.append(" | ", style="dim")
        header_text.append("q", style="bold red")
        header_text.append(" to quit", style="dim")
        
        self._cached_header = Panel(
            Align.center(header_text),
            style="cyan",
            border_style="cyan"
        )
        return self._cached_header
    
    def _make_footer(self) -> Panel:
        """Create footer panel only when status changes"""
        if self.status == self._last_status and hasattr(self, '_cached_footer'):
            return self._cached_footer
            
        footer_text = Text()
        if "Listening" in self.status:
            footer_text.append("● ", style="bold cyan")
        elif "Processing" in self.status:
            footer_text.append("● ", style="bold yellow")
        else:
            footer_text.append("● ", style="bold green")
        
        footer_text.append(self.status, style="dim")
        
        self._cached_footer = Panel(
            footer_text,
            style="cyan",
            border_style="cyan"
        )
        self._last_status = self.status
        return self._cached_footer
    
    def _safe_truncate(self, text: str, width: int) -> str:
        """Safely truncate text with ellipsis, handling unicode properly using Rich's measurement"""
        if not text:
            return ""
        text = str(text)
        
        rich_text = Text(text)
        actual_width = len(rich_text.plain)
        
        if actual_width <= width:
            return text
        
        return text[:max(0, width-3)] + "..."
    
    def _make_songs_panel(self) -> Panel:
        """Ultra-fast songs panel with optimized selection rendering"""
        self.visible_rows = self._calculate_visible_rows()
        
        if not self.songs:
            content = Align.center(
                Text("No songs detected yet...\nListening for music...", style="dim"),
                vertical="middle"
            )
        else:
            # Minimal table settings for maximum performance
            table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1), pad_edge=False)
            table.add_column("", width=2, no_wrap=True)
            table.add_column("ID", style="bold green", width=5, no_wrap=True)
            table.add_column("Time", style="dim", width=10, no_wrap=True)
            table.add_column("Song", style="bold white", no_wrap=True)
            table.add_column("Artist", style="magenta", no_wrap=True)
            table.add_column("Info", style="dim", no_wrap=True)
            
            total_songs = len(self.songs)
            end_idx = min(self.scroll_offset + self.visible_rows, total_songs)
            visible_songs = self.songs[self.scroll_offset:end_idx]
            
            # Pre-calculate selection index for faster comparison
            selected_offset = self.selected_index - self.scroll_offset
            
            # Batch process all rows for faster rendering
            for idx, song in enumerate(visible_songs):
                is_selected = (idx == selected_offset)
                
                # Use simpler indicator and style
                indicator = "►" if is_selected else " "
                row_style = "on blue" if is_selected else ""
                
                # Pre-formatted values
                song_id = f"#{song.get('id', 0):03d}"
                time = song.get('time', '--:--:--')
                title = self._safe_truncate(song.get('title', 'Unknown'), 30)
                artist = self._safe_truncate(song.get('artist', 'Unknown'), 25)
                genre = self._safe_truncate(song.get('genres', 'Unknown'), 12)
                year = song.get('release_date', '----')
                info = f"{genre}, {year}"
                
                table.add_row(
                    indicator,
                    song_id,
                    time,
                    title,
                    artist,
                    info,
                    style=row_style
                )
            
            content = table
        
        title = "[bold cyan]Detected Songs[/]"
        if len(self.songs) > self.visible_rows:
            title += f" [dim]({self.scroll_offset + 1}-{min(self.scroll_offset + self.visible_rows, len(self.songs))}/{len(self.songs)})[/]"
        
        return Panel(
            content,
            title=title,
            border_style="cyan",
            padding=(1, 2)
        )
    
    def _make_help_panel(self) -> Panel:
        """Create help panel with caching"""
        if self._cached_help is not None:
            return self._cached_help
            
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Key", style="bold green", width=8)
        table.add_column("Action", style="white")
        
        commands = [
            ("↑/↓", "Navigate songs"),
            ("d", "Download selected"),
            ("y", "Play selected on YT"),
            ("v", "Voice search"),
            ("?", "Toggle help"),
            ("q", "Quit program"),
            ("", ""),
            ("ESC", "Also quits"),
        ]
        
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        
        self._cached_help = Panel(
            table,
            title="[bold yellow]Keyboard Shortcuts[/]",
            border_style="yellow",
            padding=(1, 1)
        )
        return self._cached_help
    
    def _make_sidebar(self) -> Panel:
        if self.show_help:
            return self._make_help_panel()
        else:
            return Panel(
                "",
                border_style="dim",
                padding=(1, 1)
            )
    
    def render(self) -> Layout:
        """Ultra-fast render with optimized update path for navigation"""
        try:
            if self._cached_header is None:
                self.layout["header"].update(self._make_header())
            
            if self.status != self._last_status:
                self.layout["footer"].update(self._make_footer())
            
            # Always update songs panel for navigation changes - no caching
            # This ensures instant selection highlight updates
            if (len(self.songs) != self._last_song_count or 
                self.selected_index != self._last_selected or 
                self.scroll_offset != self._last_scroll or
                self._force_render):
                self.layout["songs"].update(self._make_songs_panel())
                self._last_song_count = len(self.songs)
                self._last_selected = self.selected_index
                self._last_scroll = self.scroll_offset
            
            # Only update sidebar when needed (help toggle)
            if self.show_help and self._cached_help is None:
                self.layout["sidebar"].update(self._make_sidebar())
            
        except Exception as e:
            error_panel = Panel(
                f"[red]Render error: {str(e)[:50]}[/]\nTerminal might be too small.",
                title="Error",
                border_style="red"
            )
            try:
                self.layout["header"].update(error_panel)
            except:
                pass
        return self.layout
    
    def add_song(self, song_info: Dict[str, Any], auto_scroll: bool = True):
        """Add a new song to history with automatic memory management"""
        if 'time' not in song_info:
            song_info['time'] = datetime.now().strftime("%H:%M:%S")
        
        self.songs.append(song_info)
        
        if len(self.songs) > self.max_songs:
            overflow = len(self.songs) - self.max_songs
            self.songs = self.songs[overflow:]
            self.selected_index = max(0, self.selected_index - overflow)
            self.scroll_offset = max(0, self.scroll_offset - overflow)
        
        if auto_scroll:
            self.selected_index = len(self.songs) - 1
            self._update_scroll()
        
        self._dirty = True
    
    def scroll_up(self):
        if self.songs and self.selected_index > 0:
            self.selected_index -= 1
            self._update_scroll()
            self._dirty = True
            # Force immediate render flag for responsive navigation
            self._force_render = True
    
    def scroll_down(self):
        if self.songs and self.selected_index < len(self.songs) - 1:
            self.selected_index += 1
            self._update_scroll()
            self._dirty = True
            # Force immediate render flag for responsive navigation
            self._force_render = True
    
    def _update_scroll(self):
        if not self.songs:
            return
        
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        
        elif self.selected_index >= self.scroll_offset + self.visible_rows:
            self.scroll_offset = self.selected_index - self.visible_rows + 1
    
    def get_selected_song(self) -> Optional[Dict[str, Any]]:
        if self.songs and 0 <= self.selected_index < len(self.songs):
            return self.songs[self.selected_index]
        return None
    
    def remove_selected_song(self) -> Optional[Dict[str, Any]]:
        """Remove the currently selected song and return it."""
        if not self.songs or self.selected_index < 0 or self.selected_index >= len(self.songs):
            return None
            
        removed_song = self.songs.pop(self.selected_index)
        
        # Adjust selection if we're at the bottom
        if self.selected_index >= len(self.songs):
            self.selected_index = max(0, len(self.songs) - 1)
            
        self._dirty = True
        return removed_song
    
    def set_status(self, status: str):
        """Thread-safe status update"""
        with self._status_lock:
            if self.status != status:
                self.status = status
                self._dirty = True
    
    def toggle_help(self):
        self.show_help = not self.show_help
        self._cached_help = None  # Invalidate cache when toggling
        self._dirty = True
    
    def needs_render(self) -> bool:
        return self._dirty or self._force_render
    
    def mark_rendered(self):
        self._dirty = False
        self._force_render = False
    
    def add_task(self, task: asyncio.Task):
        """Track background tasks for proper cleanup"""
        self._running_tasks.append(task)
        task.add_done_callback(lambda t: self._cleanup_task(t))
    
    def _cleanup_task(self, task: asyncio.Task):
        """Remove completed task from tracking list"""
        try:
            self._running_tasks.remove(task)
        except ValueError:
            pass
    
    async def cancel_all_tasks(self):
        """Cancel all running background tasks on shutdown"""
        for task in self._running_tasks[:]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass  # Ignore errors during shutdown
        self._running_tasks.clear()
