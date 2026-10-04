from nba_api.stats.endpoints import leaguedashplayerstats
import pandas as pd, time

parcalar = []
for y in range(2000, 2026):
    sezon = f"{y}-{str(y+1)[-2:]}"
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=sezon, per_mode_detailed="PerGame").get_data_frames()[0]
    df["SEZON_YIL"] = y
    parcalar.append(df); time.sleep(1)
df = pd.concat(parcalar, ignore_index=True)


df = df.sort_values(["PLAYER_ID", "SEZON_YIL"])
g = df.groupby("PLAYER_ID")
df["HEDEF_PTS"] = g["PTS"].shift(-1)
ardisik = g["SEZON_YIL"].shift(-1) == df["SEZON_YIL"] + 1
df.loc[~ardisik, "HEDEF_PTS"] = None


ard = df.dropna(subset=["HEDEF_PTS"])
ard = ard[(ard["GP"] >= 20) & (ard["MIN"] >= 10)]
ard["DEGISIM"] = ard["HEDEF_PTS"] - ard["PTS"]
ard.groupby("AGE")["DEGISIM"].agg(["mean", "count"])

X_cols = [...]  # öznitelik listen
egitim = veri[veri["SEZON_YIL"] <= 2019]
dogrulama = veri[veri["SEZON_YIL"].between(2020, 2022)]
test = veri[veri["SEZON_YIL"].between(2023, 2024)]
tahmin = veri[veri["SEZON_YIL"] == 2025]  # 2026-27 tahmini, hedefi yok