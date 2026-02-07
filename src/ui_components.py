"""
Reusable HTML UI components for the Layer.ai Playable Studio.

All functions return HTML strings for use with st.markdown(html, unsafe_allow_html=True).
Components use CSS variables defined in the main app.py design system.
"""


def glass_card(
    content: str,
    title: str = "",
    icon: str = "",
    accent: str = "",
    extra_style: str = "",
) -> str:
    """Frosted-glass container card.

    Args:
        content: Inner HTML content.
        title: Optional card header text.
        icon: Optional emoji/icon for the header.
        accent: Optional left-border accent color (CSS color string).
        extra_style: Additional inline CSS for the outer wrapper.
    """
    border_left = f"border-left: 3px solid {accent};" if accent else ""
    header = ""
    if title:
        icon_span = f'<span style="margin-right:8px;">{icon}</span>' if icon else ""
        header = f"""
        <div style="
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
        ">{icon_span}{title}</div>"""

    return f"""
    <div style="
        background: var(--glass-bg);
        backdrop-filter: blur(var(--blur));
        -webkit-backdrop-filter: blur(var(--blur));
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-lg);
        padding: 22px 24px;
        margin-bottom: 16px;
        {border_left}
        {extra_style}
        transition: border-color 0.25s ease;
    " class="glass-card">{header}{content}</div>
    """


def step_header(step_num: int, title: str, total_steps: int = 4) -> str:
    """Gradient number badge + progress dots + thin progress bar.

    Args:
        step_num: Current step (1-based).
        title: Step title text.
        total_steps: Total number of steps.
    """
    dots = ""
    for i in range(1, total_steps + 1):
        if i == step_num:
            dots += '<span style="width:10px;height:10px;border-radius:50%;background:var(--accent);display:inline-block;margin:0 4px;"></span>'
        elif i < step_num:
            dots += '<span style="width:8px;height:8px;border-radius:50%;background:var(--color-success);display:inline-block;margin:0 4px;opacity:0.8;"></span>'
        else:
            dots += '<span style="width:8px;height:8px;border-radius:50%;background:var(--glass-border);display:inline-block;margin:0 4px;"></span>'

    pct = int((step_num / total_steps) * 100)

    return f"""
    <div style="margin-bottom:24px;" class="animate-fade-in">
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;">
            <div style="
                width:42px;height:42px;border-radius:12px;
                background:linear-gradient(135deg, var(--accent), var(--accent-secondary));
                display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:1.1rem;color:#fff;
                flex-shrink:0;
            ">{step_num}</div>
            <div>
                <div style="font-size:1.35rem;font-weight:700;color:var(--text-primary);line-height:1.2;">
                    {title}
                </div>
                <div style="margin-top:4px;">{dots}</div>
            </div>
        </div>
        <div style="
            height:3px;border-radius:2px;
            background:var(--glass-border);
            overflow:hidden;
        ">
            <div style="
                height:100%;width:{pct}%;
                background:linear-gradient(90deg, var(--accent), var(--accent-secondary));
                border-radius:2px;
                transition:width 0.5s ease;
            "></div>
        </div>
    </div>
    """


def metric_card(
    label: str,
    value: str,
    icon: str = "",
    status: str = "default",
) -> str:
    """Status-aware metric card.

    Args:
        label: Metric label text.
        value: Metric value.
        icon: Optional emoji/icon.
        status: One of 'success', 'warning', 'error', 'default'.
    """
    bg_map = {
        "success": "rgba(72,187,120,0.12)",
        "warning": "rgba(236,201,75,0.12)",
        "error": "rgba(245,101,101,0.12)",
        "default": "var(--glass-bg)",
    }
    color_map = {
        "success": "var(--color-success)",
        "warning": "var(--color-warning)",
        "error": "var(--color-error)",
        "default": "var(--text-primary)",
    }
    bg = bg_map.get(status, bg_map["default"])
    color = color_map.get(status, color_map["default"])
    icon_html = f'<span style="font-size:1.2rem;margin-right:6px;">{icon}</span>' if icon else ""

    return f"""
    <div style="
        background:{bg};
        backdrop-filter:blur(8px);
        border:1px solid var(--glass-border);
        border-radius:var(--radius-md);
        padding:16px 18px;
        text-align:center;
    ">
        <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;
                     color:var(--text-secondary);margin-bottom:6px;">
            {icon_html}{label}
        </div>
        <div style="font-size:1.5rem;font-weight:700;color:{color};">
            {value}
        </div>
    </div>
    """


def confidence_badge(label: str, confidence: float, level: str = "medium") -> str:
    """Pill badge with glow effect for confidence display.

    Args:
        label: Badge text.
        confidence: 0-1 confidence value.
        level: 'high', 'medium', or 'low'.
    """
    styles = {
        "high": ("rgba(72,187,120,0.15)", "#9ae6b4", "rgba(72,187,120,0.3)"),
        "medium": ("rgba(236,201,75,0.15)", "#fbd38d", "rgba(236,201,75,0.3)"),
        "low": ("rgba(245,101,101,0.15)", "#feb2b2", "rgba(245,101,101,0.3)"),
    }
    bg, color, glow = styles.get(level, styles["medium"])
    pct = int(confidence * 100)

    return f"""
    <span style="
        display:inline-block;
        padding:5px 14px;
        border-radius:20px;
        font-size:0.85rem;
        font-weight:600;
        background:{bg};
        color:{color};
        box-shadow:0 0 12px {glow};
        letter-spacing:0.02em;
    ">{label} &middot; {pct}%</span>
    """


def color_palette(colors: list[str]) -> str:
    """Swatch strip with hex labels.

    Args:
        colors: List of hex color strings (e.g. ['#FF6B6B', '#4ECDC4']).
    """
    swatches = ""
    for c in colors[:8]:
        swatches += f"""
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
            <div style="
                width:36px;height:36px;border-radius:8px;
                background:{c};
                border:2px solid rgba(255,255,255,0.1);
            "></div>
            <span style="font-size:0.6rem;color:var(--text-muted);font-family:monospace;">
                {c}
            </span>
        </div>"""

    return f"""
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin:8px 0;">
        {swatches}
    </div>
    """


def asset_preview_card(
    key: str,
    image_url: str = "",
    is_valid: bool = True,
    error: str = "",
) -> str:
    """Card with thumbnail placeholder, status dot, and label.

    Args:
        key: Asset key name.
        image_url: URL for the asset image (displayed via Streamlit st.image, not here).
        is_valid: Whether the asset generated successfully.
        error: Error message if invalid.
    """
    dot_color = "var(--color-success)" if is_valid else "var(--color-error)"
    dot_glow = "rgba(72,187,120,0.4)" if is_valid else "rgba(245,101,101,0.4)"
    status_text = "Ready" if is_valid else (error[:40] if error else "Failed")
    status_color = "var(--color-success)" if is_valid else "var(--color-error)"

    return f"""
    <div style="
        background:var(--glass-bg);
        border:1px solid var(--glass-border);
        border-radius:var(--radius-md);
        padding:10px;
        text-align:center;
    ">
        <div style="
            font-size:0.8rem;font-weight:600;color:var(--text-primary);
            margin-bottom:6px;
            display:flex;align-items:center;justify-content:center;gap:6px;
        ">
            <span style="
                width:8px;height:8px;border-radius:50%;
                background:{dot_color};
                box-shadow:0 0 6px {dot_glow};
                display:inline-block;
            "></span>
            {key}
        </div>
        <div style="font-size:0.65rem;color:{status_color};">{status_text}</div>
    </div>
    """


def network_badges(networks: list[str], file_size_mb: float = 0) -> str:
    """Green/red pills per ad network.

    Args:
        networks: List of compatible network names.
        file_size_mb: File size for limit-aware coloring.
    """
    all_networks = {
        "Google Ads": 5,
        "Unity": 5,
        "IronSource": 5,
        "AppLovin": 5,
        "Facebook": 2,
    }
    badges = ""
    for name, limit in all_networks.items():
        compatible = file_size_mb <= limit if file_size_mb > 0 else name in networks
        if compatible:
            bg = "rgba(72,187,120,0.15)"
            color = "#9ae6b4"
            icon = "&#10003;"
        else:
            bg = "rgba(245,101,101,0.1)"
            color = "var(--text-muted)"
            icon = "&#10007;"

        badges += f"""
        <span style="
            display:inline-flex;align-items:center;gap:4px;
            padding:4px 12px;border-radius:14px;
            font-size:0.78rem;font-weight:500;
            background:{bg};color:{color};
            margin:3px;
        ">{icon} {name}</span>"""

    return f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin:8px 0;">{badges}</div>'


def success_banner(title: str, message: str = "") -> str:
    """Animated celebration card.

    Args:
        title: Banner title.
        message: Optional subtitle.
    """
    msg_html = f'<div style="font-size:0.85rem;color:var(--text-secondary);margin-top:6px;">{message}</div>' if message else ""

    return f"""
    <div style="
        background:linear-gradient(135deg, rgba(72,187,120,0.15), rgba(56,161,105,0.08));
        border:1px solid rgba(72,187,120,0.3);
        border-radius:var(--radius-lg);
        padding:20px 24px;
        margin:16px 0;
        animation:fadeInUp 0.5s ease;
    ">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.6rem;">&#10024;</span>
            <div>
                <div style="font-size:1.1rem;font-weight:700;color:var(--color-success);">{title}</div>
                {msg_html}
            </div>
        </div>
    </div>
    """


def empty_state(title: str, message: str = "", icon: str = "") -> str:
    """Centered placeholder with large icon.

    Args:
        title: Heading text.
        message: Subtitle/description.
        icon: Large emoji icon.
    """
    icon_html = f'<div style="font-size:2.8rem;margin-bottom:12px;opacity:0.7;">{icon}</div>' if icon else ""
    msg_html = f'<div style="font-size:0.88rem;color:var(--text-muted);max-width:400px;margin:0 auto;line-height:1.5;">{message}</div>' if message else ""

    return f"""
    <div style="
        text-align:center;
        padding:40px 20px;
        background:var(--glass-bg);
        border:1px dashed var(--glass-border);
        border-radius:var(--radius-lg);
        margin:16px 0;
    ">
        {icon_html}
        <div style="font-size:1.05rem;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">
            {title}
        </div>
        {msg_html}
    </div>
    """


def sidebar_progress(current_step: int) -> str:
    """Vertical timeline with circles and connecting lines.

    Args:
        current_step: The active step number (1-based).
    """
    steps = [
        (1, "Input Game"),
        (2, "Analyze & Review"),
        (3, "Generate Assets"),
        (4, "Export Playable"),
    ]

    items = ""
    for i, (num, label) in enumerate(steps):
        if num < current_step:
            circle_bg = "var(--color-success)"
            circle_border = "var(--color-success)"
            text_color = "var(--text-secondary)"
            inner = "&#10003;"
            font_weight = "400"
        elif num == current_step:
            circle_bg = "var(--accent)"
            circle_border = "var(--accent)"
            text_color = "var(--text-primary)"
            inner = str(num)
            font_weight = "700"
        else:
            circle_bg = "transparent"
            circle_border = "var(--glass-border)"
            text_color = "var(--text-muted)"
            inner = str(num)
            font_weight = "400"

        # Connecting line (not for last item)
        line = ""
        if i < len(steps) - 1:
            line_color = "var(--color-success)" if num < current_step else "var(--glass-border)"
            line = f"""
            <div style="
                width:2px;height:24px;
                background:{line_color};
                margin-left:13px;
            "></div>"""

        items += f"""
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="
                width:28px;height:28px;border-radius:50%;
                background:{circle_bg};
                border:2px solid {circle_border};
                display:flex;align-items:center;justify-content:center;
                font-size:0.75rem;font-weight:700;color:#fff;
                flex-shrink:0;
            ">{inner}</div>
            <span style="font-size:0.85rem;font-weight:{font_weight};color:{text_color};">
                {label}
            </span>
        </div>
        {line}"""

    return f'<div style="padding:4px 0;">{items}</div>'


def api_status_row(name: str, is_set: bool) -> str:
    """Colored dot + label row for API key status.

    Args:
        name: Display name for the API key.
        is_set: Whether the key is configured.
    """
    dot_color = "var(--color-success)" if is_set else "var(--color-error)"
    label_color = "var(--text-secondary)" if is_set else "var(--text-muted)"
    status_text = "Connected" if is_set else "Missing"

    return f"""
    <div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0;">
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="
                width:8px;height:8px;border-radius:50%;
                background:{dot_color};
                display:inline-block;
            "></span>
            <span style="font-size:0.82rem;color:{label_color};">{name}</span>
        </div>
        <span style="font-size:0.7rem;color:{label_color};">{status_text}</span>
    </div>
    """


def credits_display(credits: int | str) -> str:
    """Counter with color-coded progress bar.

    Args:
        credits: Number of credits available, or '?' if unknown.
    """
    if isinstance(credits, str) or credits is None:
        bar_pct = 0
        bar_color = "var(--glass-border)"
        value_color = "var(--text-muted)"
        cred_str = str(credits) if credits else "?"
    else:
        cred_int = int(credits)
        bar_pct = min(cred_int, 500) / 500 * 100  # Normalize to 500
        if cred_int >= 100:
            bar_color = "var(--color-success)"
            value_color = "var(--color-success)"
        elif cred_int >= 50:
            bar_color = "var(--color-warning)"
            value_color = "var(--color-warning)"
        else:
            bar_color = "var(--color-error)"
            value_color = "var(--color-error)"
        cred_str = str(cred_int)

    return f"""
    <div style="margin:8px 0;">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">
            <span style="font-size:0.78rem;color:var(--text-secondary);text-transform:uppercase;
                         letter-spacing:0.05em;">Credits</span>
            <span style="font-size:1.3rem;font-weight:700;color:{value_color};">{cred_str}</span>
        </div>
        <div style="height:4px;border-radius:2px;background:var(--glass-border);overflow:hidden;">
            <div style="height:100%;width:{bar_pct}%;background:{bar_color};
                        border-radius:2px;transition:width 0.5s ease;"></div>
        </div>
    </div>
    """


def phone_preview(b64_html: str, width: int = 320, height: int = 480) -> str:
    """CSS phone mockup frame wrapping a preview iframe.

    Args:
        b64_html: Base64-encoded HTML string for the iframe src.
        width: Playable width.
        height: Playable height.
    """
    frame_w = width + 24
    frame_h = height + 80

    return f"""
    <div style="
        display:flex;justify-content:center;margin:20px 0;
    ">
        <div style="
            width:{frame_w}px;
            background:linear-gradient(145deg, #1a1a2e, #16162a);
            border-radius:32px;
            padding:36px 12px 44px 12px;
            border:2px solid rgba(255,255,255,0.08);
            box-shadow:0 20px 60px rgba(0,0,0,0.5);
            position:relative;
        ">
            <!-- Notch -->
            <div style="
                width:80px;height:6px;border-radius:3px;
                background:rgba(255,255,255,0.1);
                position:absolute;top:16px;left:50%;transform:translateX(-50%);
            "></div>
            <!-- Screen -->
            <iframe
                src="data:text/html;base64,{b64_html}"
                width="{width}"
                height="{height}"
                style="border:none;border-radius:8px;display:block;background:#000;"
            ></iframe>
            <!-- Home indicator -->
            <div style="
                width:100px;height:4px;border-radius:2px;
                background:rgba(255,255,255,0.12);
                position:absolute;bottom:12px;left:50%;transform:translateX(-50%);
            "></div>
        </div>
    </div>
    """


def gradient_divider() -> str:
    """Gradient horizontal divider replacing st.markdown('---')."""
    return """
    <div style="
        height:1px;
        background:linear-gradient(90deg, transparent, var(--glass-border), transparent);
        margin:20px 0;
    "></div>
    """


def styled_pill(label: str, color: str = "var(--accent)") -> str:
    """Small styled pill badge.

    Args:
        label: Badge text.
        color: CSS color for the pill.
    """
    return f"""
    <span style="
        display:inline-block;
        padding:3px 10px;
        border-radius:12px;
        font-size:0.75rem;
        font-weight:500;
        background:rgba(255,255,255,0.06);
        color:{color};
        border:1px solid rgba(255,255,255,0.08);
        margin:2px;
    ">{label}</span>"""


def onboarding_card() -> str:
    """Rich onboarding card for missing API keys state."""
    steps_html = ""
    setup_steps = [
        ("1", "Layer.ai API Key", "Get from app.layer.ai/settings", "LAYER_API_KEY"),
        ("2", "Workspace ID", "Found in your Layer.ai workspace URL", "LAYER_WORKSPACE_ID"),
        ("3", "Anthropic API Key", "Get from console.anthropic.com", "ANTHROPIC_API_KEY"),
    ]

    for num, title, desc, env_var in setup_steps:
        steps_html += f"""
        <div style="
            background:var(--glass-bg);
            border:1px solid var(--glass-border);
            border-radius:var(--radius-md);
            padding:16px;
            flex:1;min-width:200px;
        ">
            <div style="
                width:28px;height:28px;border-radius:8px;
                background:linear-gradient(135deg, var(--accent), var(--accent-secondary));
                display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:0.8rem;color:#fff;
                margin-bottom:10px;
            ">{num}</div>
            <div style="font-size:0.9rem;font-weight:600;color:var(--text-primary);margin-bottom:4px;">
                {title}
            </div>
            <div style="font-size:0.78rem;color:var(--text-muted);margin-bottom:8px;">
                {desc}
            </div>
            <code style="font-size:0.72rem;color:var(--accent);background:rgba(255,75,75,0.1);
                         padding:2px 6px;border-radius:4px;">{env_var}</code>
        </div>"""

    return f"""
    <div style="
        background:linear-gradient(135deg, rgba(255,75,75,0.05), rgba(99,102,241,0.05));
        border:1px solid var(--glass-border);
        border-radius:var(--radius-lg);
        padding:28px;
        margin:20px 0;
    ">
        <div style="text-align:center;margin-bottom:20px;">
            <div style="font-size:2rem;margin-bottom:8px;">&#128273;</div>
            <div style="font-size:1.15rem;font-weight:700;color:var(--text-primary);">
                API Keys Required
            </div>
            <div style="font-size:0.85rem;color:var(--text-muted);margin-top:4px;">
                Set up your keys to unlock the full workflow, or try Demo Mode in the sidebar
            </div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
            {steps_html}
        </div>
        <div style="text-align:center;margin-top:16px;">
            <span style="font-size:0.78rem;color:var(--text-muted);">
                Add keys to a <code>.env</code> file in your project root
            </span>
        </div>
    </div>
    """
