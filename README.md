## From Origin to Cup — Streamlit App

by: Vinny Turtora (vt216)

Interactive storytelling app about coffee origin, trade structure, terrain, and cup outcomes.

### Tech Stack

- Python
- Streamlit
- Plotly
- PyDeck

### Run Locally

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### App Structure

- `streamlit_app.py`: app entrypoint (landing map)
- `app/landing.py`: Stage-1 U.S. import map and opening narrative
- `app/map_layers.py`: PyDeck map layers and route rendering
- `app/stage2/`: regional chapters (Americas, Africa, Asia-Pacific)
- `app/stage3/`: compare + conclusion chapters
- `pages/`: Streamlit multipage routing
- `assets/`: shared visual assets (favicon, infographic, fallback map image)
- `data/processed/`, `data/external/`, `data/raw/`: data used by the app

### Map Fallback Mode

In `app/config.py`, `MAP_MODE` controls landing-map rendering:

- `interactive_backup` (default): interactive PyDeck map
- `backup_image`: static fallback image at `assets/map_backup_current.png`

### Notes

- Landing trade routes are stylized narrative paths for communication, not audited shipping-lane reconstructions.

