import psycopg2

# Globals
DATABASE = 'radar_db'
TABLE = 'ref'
LOOKUP = 'lookup'
connection = None
cursor = None

'''
Placeholder
'''
def add_entry_db(i_id, f_id, f_screen):
	insert_query = "INSERT INTO " + TABLE + " (icon_id, follower_id, follower_screen) VALUES(%s, %s, %s)"
	values = [i_id, f_id, f_screen]
	# print(values)

	# Insert values
	if not cursor is None:
		cursor.execute(insert_query, values)

	return True

def connect_db(dbname = DATABASE):
	global connection, cursor
	try:
		connection = psycopg2.connect(database = dbname,
								      user = 'postgres',
								      password = '<your password>')
		cursor = connection.cursor()
	except:
		print('Make sure DB exists!')

'''
Placeholder
'''
def create_table(table_name = TABLE):
	create_query = ('CREATE TABLE IF NOT EXISTS ' + TABLE + ' ('
			'ID serial NOT NULL PRIMARY KEY, '
			'icon_id BIGINT NOT NULL, '
			'follower_id BIGINT NOT NULL, '
			'follower_screen VARCHAR NOT NULL'
			')')

	# Re-write with placeholder
	cursor.execute(create_query)

def drop_table(table_name = TABLE):
	cursor.execute('DROP TABLE IF EXISTS ' + TABLE)

def commit_db():
	connection.commit()
	return

def close_db():
	connection.close()
	return

