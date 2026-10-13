GLASS_CLARITY = 0.25

CANVAS = "#102127"
TEXT = "#EFF8FA"
TEXT_ACTIVE = "#173B4B"
MUTED = "#E3F2F5B8"
EDGE = "#FFFFFFCF"
GLASS = f"rgba(205, 230, 237, {GLASS_CLARITY})"


def build_stylesheet():
    return f"""
    QWidget#root {{ background: transparent; color: {TEXT}; }}
    QFrame#glass {{
        background-color: {GLASS};
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(255,255,255,91), stop:.17 rgba(255,255,255,20),
            stop:.49 rgba(205,238,247,22), stop:.78 rgba(255,255,255,47), stop:1 rgba(255,255,255,85));
        border: 1px solid {EDGE};
        border-radius: 32px;
    }}
    QTextEdit#source {{
        background: rgba(255,255,255,25);
        border: 1px solid rgba(255,255,255,98);
        border-radius: 14px;
        color: #F6FCFD;
        padding: 12px 14px;
        font-size: 18px;
    }}
    QTextEdit#source:focus {{ border: 1px solid rgba(255,255,255,208); }}
    QFrame#result {{ border: 1px solid transparent; border-radius: 18px; }}
    QFrame#result[selected="true"] {{
        background: rgba(255,255,255,170);
        border: 1px solid rgba(255,255,255,236);
    }}
    QFrame#result[selected="false"] {{ background: rgba(255,255,255,26); }}
    QPushButton#chip, QPushButton#sourceChip {{
        background: rgba(255,255,255,43);
        border: 1px solid rgba(255,255,255,98);
        border-radius: 8px;
        padding: 6px 9px;
        color: #F3FBFC;
        font-size: 11px;
    }}
    QPushButton#chip[enabled="true"], QPushButton#sourceChip[selected="true"] {{
        background: rgba(255,255,255,130);
        color: #214858;
        border: 1px solid white;
    }}
    QPushButton#paste {{
        background: rgba(255,255,255,225);
        border: 1px solid rgba(255,255,255,220);
        border-radius: 22px;
        padding: 11px 18px;
        color: #204E63;
        font-weight: 650;
    }}
    """
