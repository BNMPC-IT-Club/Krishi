"""Professional inline SVG icon system (Lucide-style stroke icons).

Replaces all emoji in the UI with crisp, theme-colored vector icons.
Usage:  st.markdown(icon("sprout", size=20) + " শিরোনাম", unsafe_allow_html=True)
or inside f-string HTML blocks:  {icon("map-pin")}
"""

_ICONS = {
    "home": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
    "chart-bar": '<path d="M3 21h18"/><rect x="6" y="11" width="3.5" height="7" rx="0.7"/><rect x="12.5" y="6" width="3.5" height="12" rx="0.7"/><rect x="19" y="14" width="2.5" height="4" rx="0.7"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "coins": '<circle cx="9" cy="9" r="6"/><path d="M15.5 4.6a6 6 0 1 1 0 14.8"/><path d="M9 6.5v5l3 1.5"/>',
    "sprout": '<path d="M7 20h10"/><path d="M12 20c0-6 0-6 0-8"/><path d="M12 12C12 8 9 5 4 5c0 4 3 7 8 7Z"/><path d="M12 10c0-3 2.5-5 7-5 0 3.5-2.5 5-7 5Z"/>',
    "microscope": '<path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>',
    "cloud-sun": '<path d="M12 2v2"/><path d="m4.9 4.9 1.4 1.4"/><path d="M20 9h2"/><path d="M4 9h2"/><path d="M8 16a4 4 0 1 0 6.3-3.3"/><path d="M12 19a4 4 0 0 0 8-1c0-1.5-.8-2.8-2-3.5"/><path d="M17 19H8"/><path d="m19.1 4.9-1.4 1.4"/><path d="M12 6.5V9"/>',
    "bot": '<rect x="4" y="8" width="16" height="12" rx="2.5"/><path d="M12 8V5"/><circle cx="12" cy="4" r="1.2"/><path d="M9 13v1.5"/><path d="M15 13v1.5"/><path d="M2 13v3"/><path d="M22 13v3"/>',
    "info": '<circle cx="12" cy="12" r="9.5"/><path d="M12 16v-5"/><path d="M12 8h.01"/>',
    "map-pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "locate": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3"/><path d="M12 19v3"/><path d="M2 12h3"/><path d="M19 12h3"/><circle cx="12" cy="12" r="8"/>',
    "refresh-cw": '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/>',
    "check-circle": '<circle cx="12" cy="12" r="9.5"/><path d="m8.5 12.5 2.5 2.5 5-5.5"/>',
    "alert-triangle": '<path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "x-circle": '<circle cx="12" cy="12" r="9.5"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "droplet": '<path d="M12 2.7 6.7 8a7.5 7.5 0 1 0 10.6 0Z"/>',
    "wind": '<path d="M12.8 2A2.2 2.2 0 1 1 12 6.2H2"/><path d="M17.8 6A2.2 2.2 0 1 1 17 10.2H2"/><path d="M10.8 10A2.2 2.2 0 1 1 10 14.2H2"/><path d="M16 14a2 2 0 1 0 2-2H2"/>',
    "thermometer": '<path d="M14 4.5a2.5 2.5 0 0 0-5 0v9.2a4.5 4.5 0 1 0 5 0Z"/><path d="M12 14.5V9"/>',
    "calendar": '<rect x="3" y="4.5" width="18" height="17" rx="2.5"/><path d="M8 2.5v4"/><path d="M16 2.5v4"/><path d="M3 10h18"/>',
    "camera": '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2Z"/><circle cx="12" cy="13" r="4"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "shield": '<path d="M12 22s8-3.5 8-10V5.5l-8-3-8 3V12c0 6.5 8 10 8 10Z"/><path d="m9 11.5 2 2 4-4.5"/>',
    "leaf": '<path d="M11 20A7 7 0 0 1 4 13c0-5 4-9.5 13-10 .5 8-3 13-6 17Z"/><path d="M4 21c4-6 8-9 13-11"/>',
    "truck": '<path d="M14 17V6a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v11h2"/><path d="M14 10h4l3 3v4h-2"/><path d="M12 17H9"/><circle cx="6.5" cy="18" r="2"/><circle cx="16.5" cy="18" r="2"/>',
    "store": '<path d="m2 7 2-4h16l2 4"/><path d="M2 7h20v3a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0Z"/><path d="M4 12v9h16v-9"/><path d="M9 21v-5h6v5"/>',
    "flask": '<path d="M10 2.5v6L4.5 18a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L14 8.5v-6"/><path d="M8.5 2.5h7"/><path d="M7 15h10"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.9 4.9 1.4 1.4"/><path d="m17.7 17.7 1.4 1.4"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.3 17.7-1.4 1.4"/><path d="m19.1 4.9-1.4 1.4"/>',
    "cloud-rain": '<path d="M4 14.9A5 5 0 1 1 11 6a6 6 0 1 1 8 8.5"/><path d="M8 19v2"/><path d="M12 18v3"/><path d="M16 19v2"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.3 17a10 10 0 1 1 17.4 0"/>',
    "target": '<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="5.5"/><circle cx="12" cy="12" r="1.5"/>',
    "lightbulb": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.4 1 2.3h6c0-.9.4-1.8 1-2.3A7 7 0 0 0 12 2Z"/>',
    "book-open": '<path d="M2 4.5h7a3 3 0 0 1 3 3V21a2.5 2.5 0 0 0-2.5-2.5H2Z"/><path d="M22 4.5h-7a3 3 0 0 0-3 3V21a2.5 2.5 0 0 1 2.5-2.5H22Z"/>',
    "heart-pulse": '<path d="M19.5 13.5c1.3-1.3 2.5-2.9 2.5-4.8A4.7 4.7 0 0 0 12 5.6a4.7 4.7 0 0 0-10 3.1c0 5 7 10.8 10 13 3-2.2 5.8-4.9 7.7-7.7"/><path d="M3.5 12h4l1.5-2.5 3 5 2-3.5h3"/>',
    "globe": '<circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19"/><path d="M12 2.5a14 14 0 0 1 0 19 14 14 0 0 1 0-19Z"/>',
    "menu": '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.9 2.9l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.9-2.9l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.9-2.9l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.9 2.9l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
    "lock": '<rect x="4" y="10.5" width="16" height="11" rx="2"/><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
    "bell": '<path d="M6 8.5a6 6 0 0 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 14.5 6 8.5"/><path d="M10 20a2.2 2.2 0 0 0 4 0"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.1 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.13.96.36 1.9.7 2.8a2 2 0 0 1-.45 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.27a2 2 0 0 1 2.1-.45c.9.34 1.84.57 2.8.7A2 2 0 0 1 22 16.9Z"/>',
    "mail": '<rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/><path d="m3 6 9 7 9-7"/>',
    "star": '<polygon points="12 2.5 15 8.7 21.5 9.6 17 14.2 18 20.7 12 17.6 6 20.7 7 14.2 2.5 9.6 9 8.7 12 2.5"/>',
    "award": '<circle cx="12" cy="9" r="6"/><path d="m8.5 13.5-1.5 8 5-3 5 3-1.5-8"/>',
    "database": '<ellipse cx="12" cy="5.5" rx="8.5" ry="3"/><path d="M3.5 5.5v13c0 1.7 3.8 3 8.5 3s8.5-1.3 8.5-3v-13"/><path d="M3.5 12c0 1.7 3.8 3 8.5 3s8.5-1.3 8.5-3"/>',
    "layers": '<polygon points="12 2.5 2 7.5 12 12.5 22 7.5 12 2.5"/><polyline points="2 12.5 12 17.5 22 12.5"/><polyline points="2 17.5 12 22.5 22 17.5"/>',
    "compass": '<circle cx="12" cy="12" r="9.5"/><polygon points="16 8 14 14 8 16 10 10 16 8"/>',
    "grid": '<rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5"/>',
    "arrow-right": '<path d="M5 12h14"/><polyline points="13 6 19 12 13 18"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2.5"/><circle cx="8.5" cy="8.5" r="1.8"/><polyline points="21 15 16 10 5 21"/>',
    "folder-open": '<path d="m6 14 1.5-2.9A2 2 0 0 1 9.2 10H22a2 2 0 0 1 1.9 2.7l-2.6 7.6A2 2 0 0 1 19.3 22H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4.4a2 2 0 0 1 1.7.9l1.2 1.9a2 2 0 0 0 1.7.9H20a2 2 0 0 1 2 2v3"/>',
    "clock": '<circle cx="12" cy="12" r="9.5"/><polyline points="12 6.5 12 12 16 14"/>',
    "external-link": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "chevron-down": '<polyline points="6 9 12 15 18 9"/>',
    "sparkles": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/><path d="M5 3v4"/><path d="M3 5h4"/><path d="M19 17v4"/><path d="M17 19h4"/>',
    "piggy-bank": '<path d="M19 11.5a7.5 7.5 0 0 0-11-6.6"/><path d="M2 13a2 2 0 0 1 2-2h1l.6-2.3A5 5 0 0 1 15 6.5h2.5a2.5 2.5 0 0 1 2.5 2.5c0 1-.5 1.9-1.3 2.4V16a2 2 0 0 1-2 2h-1l-1 2.5h-3l.5-2.5H9l-.5 2.5h-3L4.7 17A5.6 5.6 0 0 1 2 13Z"/><path d="M16.5 11h.01"/>',
    "scale": '<path d="M12 3v18"/><path d="M5 21h14"/><path d="m5 7 3.5 7L1.5 14Z"/><path d="M5 7l7-2 7 2"/><path d="m19 7 3.5 7-7-.7Z"/>',
}


def icon(name, size=18, color="currentColor", stroke=2):
    """Return an inline SVG string for the given icon name."""
    body = _ICONS.get(name, _ICONS["info"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:-{int(size*0.18)}px;flex:none;">{body}</svg>')
