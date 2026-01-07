# Web-Based Workflow Guide

This guide explains how to use Layer.ai Playable Studio entirely in your web browser using GitHub Codespaces - **no local installation required!**

---

## What is GitHub Codespaces?

GitHub Codespaces provides a complete, cloud-based development environment accessible from any web browser. It includes:

- **VS Code in your browser** - Full IDE experience
- **Pre-configured Python environment** - Python 3.11, all dependencies auto-installed
- **Port forwarding** - Access your Streamlit app securely
- **Persistent storage** - Your work is saved between sessions
- **Free tier available** - 60 hours/month for free accounts

---

## Getting Started (3 Steps)

### Step 1: Launch Codespace

1. Go to the GitHub repository
2. Click the green **Code** button
3. Select the **Codespaces** tab
4. Click **Create codespace on [branch]**

**What happens next:**
- GitHub creates a cloud-based development environment
- Python 3.11 is installed automatically
- All dependencies from `requirements.txt` are installed
- VS Code opens in your browser
- Takes ~2-3 minutes on first launch

---

### Step 2: Configure API Keys

Once your Codespace is ready:

1. **Create your environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** (click it in the file explorer):
   ```bash
   # Required API Keys
   LAYER_API_KEY=your_actual_layer_api_key
   LAYER_WORKSPACE_ID=your_actual_workspace_id
   ANTHROPIC_API_KEY=your_actual_anthropic_key
   ```

3. **Get your API keys:**
   - **Layer.ai**: [app.layer.ai](https://app.layer.ai) → Settings → API Keys
   - **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → Account Settings → API Keys

**Security Note:** Your `.env` file is private to your Codespace and won't be committed to git (it's in `.gitignore`).

---

### Step 3: Launch the App

In the Codespace terminal, run:

```bash
./start.sh
```

**What happens:**
- Streamlit server starts on port 8501
- Codespaces automatically forwards the port
- You'll see a notification: **"Your application is running on port 8501"**
- Click **Open in Browser** to access the app

The app will open in a new browser tab, fully functional!

---

## Using the Application

### The 4-Step Wizard

Once the app is running, you'll see a 4-step wizard:

#### 1. Style Intelligence
- Upload competitor screenshots (PNG, JPG, JPEG)
- Or provide an App Store URL with screenshot
- AI analyzes the visual style using Claude Vision
- Extracts color palette, art style, and key elements

#### 2. Style Lock
- Review the extracted style recipe
- Edit prefix terms, technical terms, negative prompts
- Lock the style and create it in Layer.ai
- Deep link to view it in the Layer.ai dashboard

#### 3. Variant Forge
- Select asset presets for your playable:
  - **Hook** (3s): Characters, items
  - **Gameplay** (15s): Backgrounds, game elements
  - **CTA** (5s): Buttons, banners
- Forge generates consistent assets using your locked style
- Progress bar shows real-time status

#### 4. Export & Preview
- Configure playable settings (title, URL, dimensions)
- Assemble into a single HTML file
- Download the final playable ad
- Preview in browser
- File size validation (< 5MB for ad networks)

---

## Managing Your Codespace

### Starting/Stopping

**To stop your Codespace:**
- Close the browser tab
- Codespace auto-stops after 30 minutes of inactivity
- Or manually: Go to GitHub → Codespaces → Stop

**To restart your Codespace:**
- Go to GitHub → Codespaces
- Click on your existing Codespace
- Everything resumes where you left off

### Viewing the App Again

If you closed the app and want to reopen it:

1. Open the terminal in your Codespace
2. Run: `./start.sh`
3. Click the port forwarding notification

Or manually access forwarded ports:
- Click the **Ports** tab (bottom panel)
- Find port 8501
- Click the globe icon to open in browser

---

## File Management

### Uploading Screenshots

**Option 1: Drag & Drop**
- Drag image files into the VS Code file explorer
- They'll be uploaded to your Codespace

**Option 2: Upload via Streamlit**
- Use the file uploader in the app interface
- Files are temporarily stored during the session

### Downloading Playables

When you export a playable:
- Click **Download index.html** in the app
- File downloads to your local computer
- Ready to upload to ad networks

### Viewing Generated Assets

Forged assets from Layer.ai are:
- Displayed in the Streamlit interface
- Referenced by URL (hosted by Layer.ai)
- Embedded in the final playable as Base64

---

## Troubleshooting

### "Missing API keys" error

**Solution:**
1. Make sure `.env` exists: `ls -la .env`
2. Check it has your keys: `cat .env` (be careful not to share!)
3. Restart the Streamlit app: `Ctrl+C` then `./start.sh`

### Port 8501 not forwarding

**Solution:**
1. Check the **Ports** tab (bottom panel)
2. If port 8501 isn't listed, Streamlit might not be running
3. Restart with `./start.sh`
4. Manually forward: Right-click Ports tab → Forward Port → 8501

### "Command not found: streamlit"

**Solution:**
Dependencies might not have installed. Run:
```bash
pip install -r requirements.txt
```

Then try `./start.sh` again.

### Codespace won't start

**Solution:**
- Check your GitHub billing (Codespaces requires verification)
- Try deleting and recreating the Codespace
- Check [GitHub Status](https://www.githubstatus.com)

### Changes not saving

**Solution:**
- Codespaces auto-saves most files
- For `.env`, make sure you pressed `Ctrl+S` (or `Cmd+S` on Mac)
- Check the file explorer - unsaved files have a dot indicator

---

## Advanced Usage

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

### Accessing Logs

Streamlit logs are in the terminal where you ran `./start.sh`. Scroll up to see them.

For structured logs, set in `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

---

## Cost & Limits

### GitHub Codespaces Pricing

- **Free tier**: 60 hours/month (2-core machine)
- **Pro accounts**: 90 hours/month
- **Stopped Codespaces**: Only storage charged (minimal)

**Tip:** Stop your Codespace when not in use to maximize free hours.

### Layer.ai Credits

- Check credits in the app sidebar
- Minimum 50 credits required to forge
- Each asset costs ~1-5 credits depending on complexity
- Purchase more at [app.layer.ai](https://app.layer.ai)

### Anthropic API

- Claude Vision API calls are metered
- Screenshot analysis: ~1-2 cents per request
- Monitor usage: [console.anthropic.com](https://console.anthropic.com)

---

## Sharing & Collaboration

### Sharing Your Codespace (Live)

Codespaces can be shared with teammates:
1. In Codespace: `Cmd/Ctrl+Shift+P`
2. Type: "Codespaces: Share"
3. Copy the link and share

**Security:** Only share with trusted collaborators - they'll have access to your environment.

### Sharing Playables

Export your playable as `index.html` and:
- Email to stakeholders
- Upload to Dropbox/Drive for preview
- Test in ad network upload tools
- Host on GitHub Pages for demo URLs

---

## FAQ

**Q: Do I need to install anything locally?**
A: No! Everything runs in the cloud via your browser.

**Q: Can I use this on an iPad or Chromebook?**
A: Yes! Any device with a modern web browser works.

**Q: What if I close my browser?**
A: Your Codespace persists. Just reopen it from GitHub → Codespaces.

**Q: Can I use my own Layer.ai workspace?**
A: Yes, just configure your `LAYER_WORKSPACE_ID` in `.env`.

**Q: Is my data secure?**
A: Yes. Your Codespace is private, and `.env` files are never committed to git.

**Q: Can I use a different Python version?**
A: The Codespace is pre-configured for Python 3.11. To change, edit `.devcontainer/devcontainer.json`.

**Q: How do I update dependencies?**
A: Edit `requirements.txt`, then run `pip install -r requirements.txt` in the terminal.

---

## Getting Help

- **Documentation**: [docs/](../docs/) folder
- **Issues**: Open a GitHub issue
- **Codespaces Docs**: [docs.github.com/codespaces](https://docs.github.com/en/codespaces)
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)

---

## Next Steps

Now that you have a web-based workflow:

1. ✅ Create your first playable ad
2. 📚 Read [Product Requirements](product_requirements.md) to understand use cases
3. 🏗️ Check [Architecture](architecture.md) to understand the system
4. 🔧 Review [Technical Design](technical_design.md) for API details
5. 🚀 Build awesome playable ads!

---

**Happy creating! 🎮**
