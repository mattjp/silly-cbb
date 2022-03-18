from generate.build import get_all_teams_from_table

def get_min_and_max(stat):
	teams = get_all_teams_from_table()
	team_stats = list(map(lambda team: team[stat], teams))
	return (min(team_stats), max(team_stats))



if __name__ == '__main__':
	m,n = get_min_and_max('season_ft_pct')
	print(f'ft % - min: {m}, max: {n}')

	m,n = get_min_and_max('off_rebound_avg_pg')
	print(f'off rbd % - min: {m}, max: {n}')

	m,n = get_min_and_max('ft_att_avg_pg')
	print(f'ft att % - min: {m}, max: {n}')

