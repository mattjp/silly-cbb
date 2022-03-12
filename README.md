# silly-cbb


season per team:
```
https://api.sportradar.us/ncaamb/{access_level}/{version}/{language_code}/seasons/{season_year}/{ncaamb_season}/teams/{team_id}/statistics.{format}?api_key={your_api_key}
```

```
https://api.sportradar.us/ncaamb/trial/v4/en/seasons/2021/REG/teams/bdc2561d-f603-4fab-a262-f1d2af462277/statistics.json?api_key=vvzkx4pzffvrzbzb84khdcn9
```


rpi:
```
https://api.sportradar.us/ncaamb/{access_level}/{version}/{language_code}/rpi/{season_year}/rankings.{format}?api_key={KEY}
```

standings:
```
https://api.sportradar.us/ncaamb/trial/v4/en/seasons/2021/reg/standings.json?api_key={KEY}
```

raw standings located at: `s3://silly-cbb/standings_2021.json`

1. Get team IDs from `standings_2021.json` and put into `teams.json`. Map "market" to "teamId".

## TODO

* organize operations by what s3 component they're working with

"""
FR – Freshman
SO – Sophomore
JR – Junior
SR – Senior
GR – Graduate Student
"""

