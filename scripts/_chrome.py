"""
_chrome.py — shared terminal-window chrome for the profile SVGs.

Not a script on its own; imported by generate_ascii.py and generate_infocard.py.
"""

BG = "#0b0f17"
BAR_BG = "#12161f"
BORDER = "#1f2733"
GLOW = "#2dd4bf"
TITLE_TEXT = "#8b949e"

BAR_H = 34


def window(width: int, body_height: int, title: str, body_svg: str) -> str:
    """Wrap `body_svg` (already-positioned SVG markup) in a terminal window."""
    total_h = BAR_H + body_height
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" viewBox="0 0 {width} {total_h}">
  <defs>
    <style>
      text {{ font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace; }}
    </style>
  </defs>
  <rect x="0.75" y="0.75" width="{width - 1.5}" height="{total_h - 1.5}" rx="10"
        fill="{BG}" stroke="{GLOW}" stroke-opacity="0.35" stroke-width="1.5"/>
  <path d="M 0.75 10 A 9.25 9.25 0 0 1 10 0.75 L {width - 10} 0.75 A 9.25 9.25 0 0 1 {width - 0.75} 10 L {width - 0.75} {BAR_H} L 0.75 {BAR_H} Z"
        fill="{BAR_BG}"/>
  <line x1="0.75" y1="{BAR_H}" x2="{width - 0.75}" y2="{BAR_H}" stroke="{BORDER}" stroke-width="1"/>
  <circle cx="18" cy="{BAR_H / 2}" r="6" fill="#ff5f56"/>
  <circle cx="38" cy="{BAR_H / 2}" r="6" fill="#ffbd2e"/>
  <circle cx="58" cy="{BAR_H / 2}" r="6" fill="#27c93f"/>
  <text x="{width / 2}" y="{BAR_H / 2 + 4}" font-size="12" fill="{TITLE_TEXT}" text-anchor="middle">{title}</text>
  <g transform="translate(0,{BAR_H})">
    {body_svg}
  </g>
</svg>
'''
