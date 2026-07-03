"""Floating suggestion dropdown anchored under the ticker entry.

The caller feeds it SymbolSuggestion lists and receives the picked
symbol via on_pick; this widget only handles display and selection.
"""

import tkinter as tk

from .. import theme


class SuggestionDropdown:
    def __init__(self, entry, on_pick):
        self.entry = entry
        self.on_pick = on_pick
        self.suggestions = []
        # width=0 sizes the listbox to its longest line.
        self.box = tk.Listbox(entry.winfo_toplevel(), width=0,
                              activestyle="none", exportselection=False,
                              relief="solid", bd=1, highlightthickness=0,
                              bg=theme.SURFACE, fg=theme.INK_PRIMARY,
                              selectbackground=theme.GRIDLINE,
                              selectforeground=theme.INK_PRIMARY)
        self.box.bind("<ButtonRelease-1>", self._on_click)
        # Delay so a click on the listbox (which steals focus) can land first.
        entry.bind("<FocusOut>",
                   lambda e: entry.after(120, self._hide_unless_focused))

    @property
    def visible(self):
        return bool(self.suggestions)

    def show(self, suggestions):
        if not suggestions:
            self.hide()
            return
        self.suggestions = list(suggestions)
        self.box.delete(0, "end")
        for s in self.suggestions:
            label = f" {s.symbol}  ·  {s.name}"
            if s.exchange:
                label += f"  ({s.exchange})"
            self.box.insert("end", label)
        self.box.configure(height=len(self.suggestions))
        self.box.place(in_=self.entry, x=0, rely=1.0, y=4)
        self.box.lift()

    def hide(self):
        self.suggestions = []
        self.box.place_forget()

    def move(self, delta):
        """Arrow-key navigation while focus stays in the entry."""
        if not self.visible:
            return
        cur = self.box.curselection()
        if cur:
            idx = cur[0] + delta
        else:
            idx = 0 if delta > 0 else len(self.suggestions) - 1
        idx = max(0, min(idx, len(self.suggestions) - 1))
        self.box.selection_clear(0, "end")
        self.box.selection_set(idx)
        self.box.see(idx)

    def pick_active(self):
        """Pick the highlighted suggestion; True if one was highlighted."""
        cur = self.box.curselection()
        if not (self.visible and cur):
            return False
        self._pick(cur[0])
        return True

    def _on_click(self, event):
        idx = self.box.nearest(event.y)
        if 0 <= idx < len(self.suggestions):
            self._pick(idx)

    def _pick(self, idx):
        symbol = self.suggestions[idx].symbol
        self.hide()
        self.entry.focus_set()
        self.on_pick(symbol)

    def _hide_unless_focused(self):
        if self.entry.focus_get() is not self.box:
            self.hide()
