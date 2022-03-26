# Silly CBB 🏀

Picking CBB winners using only free throw percentage, starting guard age, and offensive rebounds.

## Building and deploying

0. Run all `generate/*.py` as normal, using Python 3.
1. Build the calculation Lambda by running:
  ```
  sam build -t cbbSimulate.yaml
  ```
2. Run the calculation Lambda by running:
  ```
  sam local invoke cbbSimulate -e event.json
  ```
3. Deploy a new revision by pushing code to the `origin/main` branch. This is done using Github Actions and AWS SAM.

## Add all team data to S3

Data comes from the Sportradar API. Trial accounts are free, and allow 1,000 requests per month. We'll use three endpoints to gather all of the requisite data, storing it in S3.

First, we get all `team_id` from the standings endpoint:

```
https://api.sportradar.us/ncaamb/trial/v4/en/seasons/2021/reg/standings.json?api_key={KEY}
```

Next, we collect 2021 season data for all `team_id`:

```
https://api.sportradar.us/ncaamb/trial/v4/en/seasons/2021/reg/teams/{team_id}/statistics.json?api_key={KEY}
```

Finally, we gather player data for the two starting guards `player_id`:

```
https://api.sportradar.us/ncaamb/trial/v4/en/players/{player_id}/profile.json?api_key={KEY}
```

## Build DynamoDB table

Using the data compiled in S3, we'll build a DynamoDB table. The primary key will be `school_name`, as there are no duplicates in the raw data.

The table attributes for each school will include:

| Attribute | Description | Type |
| :-------- | :---------- | :--- |
| `ft_att_avg_pg` | Average free throws attempted per game | Number |
| `guards` | List of starting guards | List |
| `guards.experience` | Current year of the guard | String |
| `guards.sport_radar_id` | ID of the guard in Sportradar | String |
| `guards.full_name` | Full name of the guard | String |
| `mascot` | Team mascot | String |
| `season_ft_pct` | Free throw percentage for the regular season | Number |
| `sport_radar_id` | Team ID in Sportradar | String |
| `conference` | Team conference | String |
| `off_rebound_avg_pg` | Average number of offensive rebounds per game | Number |

## Calculation Lambda

We will use a Lambda to serve simulation requests. The Lambda will take one query string parameter, `teams`, which will contain exactly 2 `school_names`. 

For each of the 2 schools requested, the Lambda will calculate a `score`:

```
free throw percentage + average guard age + (0.5 * normalized average offensive rebounds per game)
```

Normalization for average offensive rebounds per game is calculated as follows:

```
(n - min(n)) / (max(n) - min(n))
```

The normalization results in the team with the highest offensive rebound average receiving a `0.5` bonus to their score, and the team with the lowest offensive rebound average receiving a bonus of `0.0`.

Use the following URL to invoke the Lambda:

https://gq2gtmama0.execute-api.us-east-2.amazonaws.com/Prod/simulate?teams=team1,team2

Sample response:

```
{
    "colorado-state": {
        "season_ft_pct": 0.79,
        "avg_guard_age": 0.35,
        "avg_off_rebound": 5.96,
        "score": 1.2
    },
    "michigan": {
        "season_ft_pct": 0.73,
        "avg_guard_age": 0.5,
        "avg_off_rebound": 8.83,
        "score": 1.32
    }
}
```

## Todo

* Use ML, I think me manually tuning the coefficients is just manual machine learning

* prefix search the dynamodb using a lambda.
