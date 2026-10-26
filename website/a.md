# How to Run the Road Safety Project

Follow these steps in order. Open PowerShell in the main `road-safety-ai` project folder first.

## 1. Open the project folder

In PowerShell, go to the folder where you saved the project. For example:

```powershell
cd "C:\Users\Ritesh gawade\OneDrive\Desktop\MSC AI\road-safety-ai"
```

You should see two main folders: `website` and `agent`.

## 2. Run the website

The website is a set of HTML, CSS, JavaScript, and JSON files. Run a small local web server so the page can load its JSON data.

1. In PowerShell, while you are in the main `road-safety-ai` folder, run:

   ```powershell
   python -m http.server 8000
   ```

2. Open this address in your browser:

   ```text
   http://localhost:8000/website/
   ```

3. To stop the website server, return to PowerShell and press **Ctrl+C**.

Keep the PowerShell window open while using the website. If port `8000` is busy, use another number, such as `8001`, and open `http://localhost:8001/website/`.

## 3. Prepare the policy agent

The agent uses Python and a Groq API key. You need internet access and a Groq API key for this step.

1. In PowerShell, copy the example settings file:

   ```powershell
   Copy-Item agent\.env.example agent\.env
   ```

2. Open `agent\.env` in a text editor.
3. Replace `replace_me` with your Groq API key after `GROQ_API_KEY=`.
4. Save the file. Keep your API key private; do not paste it into code or share it.

You only need to do this setup once on your computer. The `.env` file is excluded from Git.

## 4. Run the policy agent

Open a **second PowerShell window**. Go to the main project folder again:

```powershell
cd "C:\Users\Ritesh gawade\OneDrive\Desktop\MSC AI\road-safety-ai"
```

Run the agent with a policy question in quotation marks:

```powershell
python agent\main.py "A city has many traffic violations, unpaid e-challans, and repeat offenders. Which intervention should be prioritized?"
```

The agent works through research lenses, policy options, scoring, conflicts, and a final recommendation. When it finishes, the command shows where it saved the report.

## 5. Find the results

- The final report is saved in `agent\output\`.
- Research findings, decisions, and progress are saved under `agent\sandbox\runs\`.
- The run state file is inside that scenario's `state` folder.

You can open the Markdown report with any text editor or Markdown viewer.

## 6. Resume after an interruption

If the agent stops because of a rate limit, internet problem, or other API error:

1. Keep the same policy question. The agent uses it to find the saved run.
2. If needed, replace the Groq key in `agent\.env` with a working key.
3. Run the **same command again**.

The agent checks the saved files and continues from the first incomplete step. It reuses completed stages. If you change the question substantially, the agent creates a separate run and does not combine its results with the old question.

## 7. Which command should I run first?

For the website, run the local server from the main project folder:

```powershell
python -m http.server 8000
```

For the agent, use a second PowerShell window and run:

```powershell
python agent\main.py "Write your road-safety policy question here."
```

The website and agent are separate. You can run either one by itself, or keep both open in two PowerShell windows.
