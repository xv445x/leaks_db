import sqlite3
from sys import argv
from argparse import ArgumentParser
import os
from progress.bar import Bar, ChargingBar
import threading
from time import sleep

parser = ArgumentParser(description='procesa archivos a la base de datos sqlite3 creada llamada leaks.db')
parser.add_argument('-f', help='Archivo para parsear', type=str)
parser.add_argument('-s', help='Buscar en la BBDD por un string', type=str)
parser.add_argument('-su', help='Buscar en la BBDD por un string en el campo de usuarios (funciona en conjunto con -sp)', type=str, default = '')
parser.add_argument('-sp', help='Buscar en la BBDD por un string en el campo de credenciales', type=str, default = '')
parser.add_argument('--create', help='Crear una BBDD', action='store_true')
parser.add_argument('--num', help='Numero de credenciales almacenadas', action='store_true')
parser.add_argument('-T', help='Numero de threads, por defecto 1', type=int, default=1)

args = parser.parse_args()


def consult_ddbb(consult):
	con = sqlite3.connect("leaks.db")
	cur = con.cursor()
	res = cur.execute(consult)
	res_r = res.fetchall()
	cur.close()
	con.close()
	return(res_r)

def ddbb_upi(u,p):
		con = sqlite3.connect("leaks.db")
		cur = con.cursor()
		test = 0
		while test == 0:
			try:
				res = cur.execute('SELECT id FROM leaks WHERE user = ? AND pass = ?', (u, p))
				if res.fetchone():
					count_exists.append(u + ":" + p)
				else:
					cur.execute('INSERT INTO leaks (user, pass, list) VALUES (?, ?, ?)', (u, p, args.f))
					count_new.append(u + ":" + p)
					con.commit()
				test = 1
			except Exception as e:
				if  "database is locked" in str(e):
					con.close()
					sleep(20)
					con = sqlite3.connect("leaks.db")
					cur = con.cursor()
				else:
					errors.append(u + ':' + p)
					print(e)
					test = 1

def ddbb_search(args_s):
	test = "SELECT * FROM leaks WHERE user LIKE '%{}%' OR pass LIKE '%{}%'".format(args_s, args_s)
	res_r = consult_ddbb(test)
	for res_pr in res_r:
		print(res_pr)
	print("Total:" + str(len(res_r)))
def ddbb_search_up(args_su, args_sp):
	test = "SELECT user,pass FROM leaks WHERE user LIKE '%{}%' AND pass LIKE '%{}%'".format(args_su, args_sp)
	res_r = consult_ddbb(test)
	for res_pr in res_r:
		print(res_pr)
	print("Total:" + str(len(res_r)))




if __name__ == '__main__':

	if args.create:
		if os.path.exists("leaks.db"):
			print("DDBB leaks.db ya existe")
		else:
			con = sqlite3.connect("leaks.db")
			cur = con.cursor()
			cur.execute('CREATE TABLE IF NOT EXISTS leaks( "id" INTEGER NOT NULL UNIQUE, "user" TEXT NOT NULL, "pass" TEXT NOT NULL, "list" TEXT, PRIMARY KEY("id" AUTOINCREMENT));')
			cur.close()
			con.close()
			print("DDBB leaks.db creada con exito")
	elif args.f:
		try:
			f = open(args.f, "r", errors="ignore")
			ff = f.read().split("\n")
			f.close()
			prog = len(ff)
			bar = Bar("Importando y procesando", max=prog)
			count_exists = []
			count_new = []
			errors = []
			for user_leak in ff:
				while threading.active_count() > args.T:
					sleep(0.01)
				if len(user_leak):
					try:
						us, ps = user_leak.split(":", 1)
						t = threading.Thread(target=ddbb_upi, args=(us,ps))
						t.start()
						#ddbb_upi(us,ps)
						bar.next()
					except:
						pass
				else:
					pass
			bar.finish()
			print("Nuevas credenciales: {} \n Credenciales repetidas: {}".format(len(count_new), len(count_exists)))
			if len(errors) > 0:
				print("Errores con las siguientes credenciales")
				for i in errors:
					print(i)
		except KeyboardInterrupt:
			bar.finish()
			print("Nuevas credenciales: {} \n Credenciales repetidas: {}".format(len(count_new), len(count_exists)))
			if len(errors) > 0:
				print("Errores con las siguientes credenciales")
				for i in errors:
					print(i)
			if len(count_new) > 1:
				print("Ultima pass agregada: " + count_new[-1])
			if len(count_exists) > 1:
				print("Ultima pass repetida: " + count_exists[-1])
	elif args.s:
		ddbb_search(args.s)
	elif args.su != '' or args.sp != '':
		ddbb_search_up(args.su, args.sp)
	elif args.num:
		res_r = consult_ddbb("select seq from sqlite_sequence where name='leaks'")
		print("Credenciales guardadas: " + str(res_r[0][0]))