# Mac Desktop Workflow Guide

This guide explains how to use Layer.ai Playable Studio on your Mac using **Claude Code desktop app** and **GitHub Desktop**.

---

## What You'll Need

- **Mac** running macOS (any recent version)
- **GitHub Desktop** - [Download here](https://desktop.github.com/)
- **Claude Code Desktop App** - [Download here](https://claude.ai/download)
- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Git** (usually pre-installed on Mac, or comes with GitHub Desktop)

---

## Getting Started (5 Steps)

### Step 1: Install Prerequisites

1. **Install Python 3.11+**
   ```bash
   # Check if you have Python installed
   python3 --version

   # Should show Python 3.11.x or higher
   # If not, download from https://www.python.org/downloads/
   ```

2. **Install GitHub Desktop**
   - Download from [desktop.github.com](https://desktop.github.com/)
   - Open the downloaded `.dmg` file
   - Drag GitHub Desktop to Applications
   - Sign in with your GitHub account

3. **Install Claude Code Desktop App**
   - Download from [claude.ai/download](https://claude.ai/download)
   - Open the downloaded file and install
   - Sign in with your Anthropic account

---

### Step 2: Clone the Repository

#### Using GitHub Desktop:

1. **Open GitHub Desktop**
2. **Clone Repository:**
   - Click **File** → **Clone Repository**
   - Go to the **URL** tab
   - Enter: `https://github.com/AlreadyKyle/layer-playable-ads.git`
   - Choose a local path (e.g., `~/Documents/layer-playable-ads`)
   - Click **Clone**

3. **Set Branch to main:**
   - In GitHub Desktop, click **Current Branch**
   - Select **main** from the list

**Your repository is now on your Mac!**

---

### Step 3: Set Up Python Environment

1. **Open Terminal** (Applications → Utilities → Terminal)

2. **Navigate to your project:**
   ```bash
   cd ~/Documents/layer-playable-ads
   # (or wherever you cloned it)
   ```

3. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

4. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

   You should see `(venv)` appear at the start of your terminal prompt.

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Step 4: Configure API Keys

1. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file:**

   You can use any text editor:
   ```bash
   # Open with TextEdit
   open -a TextEdit .env

   # Or open with VS Code (if installed)
   code .env

   # Or use nano in terminal
   nano .env
   ```

3. **Add your API keys:**
   ```bash
   # Required API Keys
   LAYER_API_KEY=your_actual_layer_api_key
   LAYER_WORKSPACE_ID=your_actual_workspace_id
   ANTHROPIC_API_KEY=your_actual_anthropic_key
   ```

4. **Get your API keys:**
   - **Layer.ai**: [app.layer.ai](https://app.layer.ai) → Settings → API Keys
   - **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → Account Settings → API Keys

5. **Save the file** (`Cmd+S` in TextEdit, `Ctrl+X` then `Y` in nano)

**Security Note:** Your `.env` file is in `.gitignore` and won't be committed to git.

---

### Step 5: Launch the App

1. **Make sure your virtual environment is activated:**
   ```bash
   source venv/bin/activate
   ```

2. **Run the app:**
   ```bash
   ./start.sh
   ```

   Or manually:
   ```bash
   streamlit run src/app.py
   ```

3. **Access the app:**
   - Your browser should automatically open to `http://localhost:8501`
   - If not, manually open: `http://localhost:8501`

**You're ready to create playable ads!**

---

## Using Claude Code Desktop App

### Opening Your Project in Claude Code

1. **Launch Claude Code desktop app**
2. **Open Project:**
   - Click **File** → **Open Folder**
   - Navigate to `~/Documents/layer-playable-ads`
   - Click **Open**

3. **Claude Code can now:**
   - Read and edit all project files
   - Run terminal commands
   - Help you debug issues
   - Write new features
   - Run tests

### Example Claude Code Workflows

**Ask Claude to help with development:**
```
"Help me debug why the forge is failing"
"Add a new UA preset for puzzle games"
"Run the tests and fix any failures"
"Update the color palette extraction to include tertiary colors"
```

**Claude Code has access to:**
- All project files
- Terminal (can run Python, git, etc.)
- Documentation in `/docs`
- Your development guidelines in `claude.md`

---

## Making Changes with GitHub Desktop

### After Making Code Changes:

1. **Open GitHub Desktop**

2. **Review Changes:**
   - You'll see all modified files in the left sidebar
   - Click on a file to see the diff (what changed)

3. **Commit Changes:**
   - Write a commit message in the bottom-left
   - Example: "Add new forge preset for RPG games"
   - Click **Commit to main**

4. **Push to GitHub:**
   - Click **Push origin** (top right)
   - Your changes are now on GitHub!

### Working with Branches:

1. **Create a New Branch:**
   - Click **Current Branch** → **New Branch**
   - Name it (e.g., `feature/new-preset`)
   - Click **Create Branch**

2. **Switch Branches:**
   - Click **Current Branch**
   - Select the branch you want to work on

3. **Merge Changes:**
   - Switch to `main` branch
   - Click **Branch** → **Merge into Current Branch**
   - Select the feature branch
   - Click **Merge**

---

## Automated Git Scripts (Recommended!)

We've included helper scripts to automate common git workflows. Use these from the terminal for faster development!

### Quick Status Check

```bash
./git-status.sh
```

**Shows:**
- Current branch
- Sync status with remote (ahead/behind)
- Modified/added/deleted files
- Recent commits

**Use when:** You want to quickly check what's changed and if you're in sync.

---

### Sync with Remote

```bash
./sync.sh
```

**Does:**
- Fetches latest changes from GitHub
- Pulls updates to your current branch

**Use when:** Starting work or checking for team updates.

---

### Quick Save and Push

```bash
./save.sh "Your commit message here"
```

**Does:**
- Shows what will be committed
- Asks for confirmation
- Adds all changes
- Commits with your message
- Pushes to remote

**Example:**
```bash
./save.sh "Add new RPG character preset"
```

**Use when:** You want to quickly save and push your work without multiple commands.

---

### Combined Workflow Example

```bash
# Start your day
./sync.sh

# ... do some work ...

# Check what changed
./git-status.sh

# Save and push
./save.sh "Implement color palette extraction improvements"
```

**This replaces:**
```bash
# Traditional git workflow
git fetch origin
git pull origin main
# ... work ...
git status
git add -A
git commit -m "Implement color palette extraction improvements"
git push -u origin main
```

---

## Daily Workflow

### Starting Your Work Session:

**Option A: Using Automated Scripts (Faster)**
```bash
cd ~/Documents/layer-playable-ads
./sync.sh                    # Get latest changes
source venv/bin/activate     # Activate Python environment
./start.sh                   # Start Streamlit
```

**Option B: Using GitHub Desktop (Visual)**
1. **Open GitHub Desktop**
   - Click **Fetch origin** to get latest changes
   - Click **Pull origin** if there are updates

2. **Open Terminal**
   ```bash
   cd ~/Documents/layer-playable-ads
   source venv/bin/activate
   ./start.sh
   ```

3. **Open Claude Code Desktop**
   - Open your project folder
   - Start developing!

### Ending Your Work Session:

**Option A: Using Automated Script (Faster)**
```bash
# 1. Stop Streamlit
Ctrl+C

# 2. Save all changes
./save.sh "Describe what you did today"

# 3. Deactivate environment
deactivate
```

**Option B: Using GitHub Desktop (Visual)**
1. **Stop Streamlit:**
   - In terminal: `Ctrl+C`

2. **Commit Your Changes:**
   - Use GitHub Desktop to commit and push

3. **Deactivate Virtual Environment:**
   ```bash
   deactivate
   ```

---

## File Management

### Project Structure on Your Mac:

```
~/Documents/layer-playable-ads/
├── .env                    # Your API keys (DO NOT COMMIT)
├── .env.example            # Template for API keys
├── venv/                   # Python virtual environment (DO NOT COMMIT)
├── src/                    # Application code
├── docs/                   # Documentation
├── tests/                  # Tests
└── README.md               # Main documentation
```

### Uploading Screenshots:

**Option 1: Use the Streamlit app**
- Click the file uploader in the browser
- Select images from your Mac

**Option 2: Copy to project folder**
```bash
# Create a screenshots folder
mkdir -p screenshots

# Copy images
cp ~/Downloads/competitor-screenshot.png screenshots/
```

### Downloading Playables:

When you export a playable:
- Click **Download index.html** in the app
- File saves to your `~/Downloads` folder
- Ready to test or upload to ad networks

---

## Troubleshooting

### "Command not found: python3"

**Solution:**
Install Python 3.11+ from [python.org/downloads](https://www.python.org/downloads/)

### "Command not found: streamlit"

**Solution:**
Make sure your virtual environment is activated:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Missing API keys" error

**Solution:**
1. Check `.env` exists: `ls -la .env`
2. Verify it has your keys: `cat .env`
3. Make sure no extra spaces around the `=` signs
4. Restart Streamlit

### Port 8501 already in use

**Solution:**
```bash
# Kill any existing Streamlit processes
pkill -f streamlit

# Or find and kill the process
lsof -ti:8501 | xargs kill -9

# Then restart
./start.sh
```

### GitHub Desktop won't push

**Solution:**
- Make sure you're signed in to GitHub
- Check you have push access to the repository
- Try: **Repository** → **Repository Settings** → Verify remote URL

### Virtual environment activation issues

**Solution:**
```bash
# If you get permission errors
chmod +x venv/bin/activate

# Then activate
source venv/bin/activate
```

---

## Advanced Usage

### Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src

# Run specific test file
pytest tests/test_vision.py -v
```

### Code Formatting

```bash
# Format with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type checking
mypy src/
```

### Using Claude Code for Development

Ask Claude Code to:
- **Run tests**: "Run all tests and show me the results"
- **Debug errors**: "The forge is failing, help me debug"
- **Add features**: "Add a new preset for casual games"
- **Refactor code**: "Refactor the asset forger to be more modular"
- **Update docs**: "Update the README with the new feature"

Claude Code can execute terminal commands, read/write files, and help you develop faster!

---

## Updating Dependencies

### To update Python packages:

```bash
# Activate virtual environment
source venv/bin/activate

# Update all packages
pip install --upgrade -r requirements.txt

# Or update a specific package
pip install --upgrade streamlit

# Freeze new versions
pip freeze > requirements.txt
```

### To update the repository:

```bash
# In GitHub Desktop
1. Click "Fetch origin"
2. Click "Pull origin" if updates available

# Or in terminal
git pull origin main
```

---

## Best Practices

### Git Workflow:

1. **Always pull before starting work:**
   - Click **Fetch origin** in GitHub Desktop
   - Pull any updates

2. **Commit frequently:**
   - Small, focused commits are better
   - Write clear commit messages

3. **Push regularly:**
   - Don't let changes pile up locally
   - Push at least daily

### Development Workflow:

1. **Keep virtual environment activated while working**
2. **Don't commit `.env` or `venv/` (they're in `.gitignore`)**
3. **Run tests before committing major changes**
4. **Use Claude Code for code reviews and debugging**

### API Keys Security:

1. **Never commit API keys to git**
2. **Keep `.env` in `.gitignore`**
3. **Don't share screenshots of `.env` file**
4. **Rotate keys if accidentally exposed**

---

## Claude Code Integration Tips

### Setting Up Claude Code for This Project:

1. **Open the project in Claude Code**
2. **Claude Code reads `claude.md` automatically** - this file contains:
   - Development guidelines
   - API schemas
   - Testing requirements
   - Code style rules

### Useful Claude Code Commands:

```
"Read the product requirements and summarize"
"Find all TODOs in the codebase"
"Run the linter and fix issues"
"Update the changelog with recent commits"
"Help me implement a new forge preset"
"Debug why the Streamlit app won't start"
```

### Claude Code Best Practices:

- **Be specific**: "Fix the color palette extraction bug in vision/competitor_spy.py:145"
- **Provide context**: "The forge is failing with a 403 error when I try to create assets"
- **Ask for explanations**: "Explain how the reference image consistency works"
- **Request testing**: "Write tests for the new playable assembler function"

---

## Keyboard Shortcuts (Mac)

### GitHub Desktop:
- `Cmd+T` - Create new branch
- `Cmd+P` - Push to origin
- `Cmd+Shift+F` - Fetch from origin
- `Cmd+Enter` - Commit changes

### Terminal:
- `Ctrl+C` - Stop Streamlit server
- `Cmd+T` - New terminal tab
- `Cmd+K` - Clear terminal

### Claude Code:
- `Cmd+P` - Quick file search
- `Cmd+Shift+F` - Search in all files
- `Cmd+B` - Toggle sidebar
- `Cmd+J` - Toggle terminal panel

---

## FAQ

**Q: Do I need to keep the virtual environment activated?**
A: Only when running the app or installing packages. You can deactivate it with `deactivate`.

**Q: Can I use VS Code instead of Claude Code?**
A: Yes! The project works with any editor. Claude Code is recommended for AI-assisted development.

**Q: What if I accidentally commit `.env`?**
A: Remove it immediately:
```bash
git rm --cached .env
git commit -m "Remove .env from git"
git push origin main
```
Then rotate your API keys!

**Q: How do I update to the latest code?**
A: In GitHub Desktop, click **Fetch origin** then **Pull origin**.

**Q: Can I work offline?**
A: The app needs internet for API calls (Layer.ai, Anthropic), but you can code offline and commit locally.

**Q: Should I work on main or create branches?**
A: For experiments, create feature branches. For small fixes, main is fine. Use GitHub Desktop to manage branches.

**Q: How do I share my work with teammates?**
A: Commit to a branch, push to GitHub, then create a Pull Request on GitHub.com.

---

## Getting Help

- **Documentation**: Check the `/docs` folder
- **Issues**: Open a GitHub issue
- **Claude Code**: Ask the Claude Code assistant for help
- **Python Errors**: Check the Streamlit logs in terminal
- **API Errors**: Check API key configuration in `.env`

---

## Next Steps

Now that you have a Mac desktop workflow:

1. ✅ Create your first playable ad
2. 📚 Read [Product Requirements](product_requirements.md) to understand use cases
3. 🏗️ Check [Architecture](architecture.md) to understand the system
4. 🔧 Review [Technical Design](technical_design.md) for API details
5. 🎨 Experiment with different styles and presets
6. 🤖 Use Claude Code to build new features!

---

**Happy creating on your Mac! 🎮💻**
