
# 🏛️ Get Political. Take Action.
**An interactive Streamlit app for exploring Congressional activity, analyzing bills, and contacting your representatives — powered by the U.S. Congress API and OpenAI.**

🌐 **Live App:** [https://getpolitical.streamlit.app/](https://getpolitical.streamlit.app/)

---

## 🚀 Overview
This Streamlit app empowers users to:
- **Explore recent congressional activity** with filters for chamber, legislative stage, date range, and cosponsors.  
- **Analyze any bill** in Congress using AI-generated summaries, pros and cons, and legislative timelines.  
- **Find and contact U.S. Representatives and Senators** by entering your home address.

The app combines real-time data from the [Congress.gov API](https://api.congress.gov/) with large-language-model analysis from OpenAI’s GPT-4.1-nano.

---

## 🧭 Features
### 1️⃣ Congressional Activity
- Fetches and displays the most recent bills from the 119th Congress.  
- Interactive filters for:
  - Action date range  
  - Chamber (House, Senate, All)  
  - Legislative stage (Introduced → Became Law)  
  - Minimum cosponsors  
- Click any bill to jump directly into detailed analysis.

### 2️⃣ Analyze a Bill
- Retrieves full bill metadata, sponsor info, and legislative actions.  
- Summarizes the bill using OpenAI:
  - **Summary**  
  - **Pros & Cons**  
  - **Overall Assessment**  
- Visualizes milestones and floor activity timelines.

### 3️⃣ Contact Congress
- Enter any U.S. address to instantly identify your House and Senate representatives.  
- Displays names, party affiliation, and both D.C. and local office phone numbers.

---

## 🛠️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/NOLATL/GetPolitical.git
cd GetPolitical
```

### 2️⃣ Create and activate a virtual environment
Using Conda:
```bash
conda env create -f environment.yml
conda activate congress-bills-env
```

Or with `venv`:
```bash
python -m venv venv
source venv/bin/activate  # (Mac/Linux)
venv\Scripts\activate     # (Windows)
pip install -r requirements.txt
```

### 3️⃣ Create a `.env` file
In the project root, add the following lines:
```
CONGRESS_API_KEY=your_congress_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ACCESS_CODE=your_private_access_code
```
> 💡 *ACCESS_CODE is optional but recommended for restricting access when deployed on Streamlit Cloud.*

---

## ▶️ Run the App Locally
```bash
streamlit run app.py
```

Then open the local URL shown in the terminal (usually `http://localhost:8501`).

---

## ☁️ Deployment (Streamlit Community Cloud)
1. Push your project to GitHub.  
2. Go to [share.streamlit.io](https://share.streamlit.io).  
3. Connect your GitHub repo and deploy.  
4. In **Settings → Secrets**, add:
   - `CONGRESS_API_KEY`
   - `OPENAI_API_KEY`
   - `ACCESS_CODE` *(optional)*

---

## 📦 Conda Environment Example (`environment.yml`)
```yaml
name: congress-bills-env
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - streamlit
  - pandas
  - requests
  - python-dotenv
  - openai
  - pip
  - pip:
      - streamlit-option-menu
```

---

## 🧩 Tech Stack
| Component | Description |
|------------|-------------|
| **Frontend/UI** | [Streamlit](https://streamlit.io) |
| **Data Source** | [Congress.gov API](https://api.congress.gov/) |
| **AI Analysis** | [OpenAI GPT-4.1-nano](https://platform.openai.com/docs/) |
| **Data Handling** | `pandas` |
| **Environment Management** | `dotenv`, `.env` file |

---

## 🔒 Access Control
This app includes a lightweight access gate to protect deployed apps on public Streamlit Cloud.  
Users must enter the <letmein123> to unlock the app interface.

---

## 🧠 Example Use Cases
- Quickly see what Congress is working on this week.  
- Understand key provisions and controversies in major bills.  
- Identify and reach out to your elected officials on issues you care about.

---

## 👨‍💻 Author
**Jared Carollo**  
[GitHub](https://github.com/NOLATL) • [LinkedIn](https://www.linkedin.com/in/jaredcarollo)

---

## 📝 License
This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
